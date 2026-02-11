"""
Memory management service for hybrid memory retrieval and formatting.
"""

import asyncio
from datetime import datetime
import numpy as np
from src.core.logs import logger
from src.core.config import settings
from src.prompts.constants import (
    MEMORY_CRITICAL,
    MEMORY_SEMANTIC,
    MEMORY_RECENT,
    MEMORY_NONE,
)


class MemoryManager:
    """Manages retrieval, deduplication, and formatting of user memories from Mem0."""

    def __init__(self, memory):
        """
        Args:
            memory: Mem0 Memory instance for semantic search
        """
        self._memory = memory

    def _format_date(self, date_str: str) -> str:
        """Format date compactly. Returns empty string if memory is recent (<7 days)."""
        if not date_str:
            return ""
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            now = datetime.now(dt.tzinfo)

            # Hide date if memory is recent (< N days)
            if (now - dt).days < settings.MEM0_DATE_THRESHOLD_DAYS:
                return ""

            return dt.strftime("%d/%m")
        except (ValueError, AttributeError):
            return ""

    def _normalize_mem0_results(self, results, source: str) -> list[dict]:
        """Normalize Mem0 search results to standard format."""
        normalized = []
        data = results.get("results", []) if isinstance(results, dict) else results
        for mem in data:
            if text := mem.get("memory", ""):
                normalized.append(
                    {
                        "text": text,
                        "created_at": mem.get("created_at", ""),
                        "source": source,
                        "embedding": mem.get("embedding", None),  # For semantic dedup
                    }
                )
        return normalized

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if not vec1 or not vec2:
            return 0.0
        try:
            arr1 = np.array(vec1, dtype=np.float32)
            arr2 = np.array(vec2, dtype=np.float32)
            norm1 = np.linalg.norm(arr1)
            norm2 = np.linalg.norm(arr2)
            if norm1 == 0 or norm2 == 0:
                return 0.0
            return float(np.dot(arr1, arr2) / (norm1 * norm2))
        except (ValueError, TypeError) as e:
            logger.warning("Error computing cosine similarity: %s", e)
            return 0.0

    def _deduplicate_semantically(
        self, memories: list[dict], threshold: float = 0.85
    ) -> list[dict]:
        """
        Remove semantically similar memories, keeping only the most recent.
        """
        if not memories:
            return []

        # Sort by created_at (most recent first)
        sorted_mems = sorted(
            memories, key=lambda m: m.get("created_at", ""), reverse=True
        )

        unique_memories = []
        seen_texts = set()
        seen_embeddings = []

        for mem in sorted_mems:
            text = mem.get("text", "")

            # Exact string dedup (primary)
            if text in seen_texts:
                continue

            # Semantic dedup (if embeddings available)
            embedding = mem.get("embedding")
            if embedding and seen_embeddings:
                is_semantic_dup = False
                for seen_emb in seen_embeddings:
                    similarity = self._cosine_similarity(embedding, seen_emb)
                    if similarity > threshold:
                        is_semantic_dup = True
                        logger.debug(
                            "Semantic duplicate detected (sim=%.2f): %s",
                            similarity,
                            text[:50],
                        )
                        break
                if is_semantic_dup:
                    continue

            unique_memories.append(mem)
            seen_texts.add(text)
            if embedding:
                seen_embeddings.append(embedding)

        return unique_memories

    def _retrieve_critical_facts(self, user_id: str) -> list[dict]:
        """
        Explicit search for critical facts (health, injuries, goals) with priority.
        """
        critical_keywords = (
            "alergia lesão dor objetivo meta restrição médico cirurgia "
            "preferência equipamento disponível horário treino experiência "
            "limitação físico histórico peso altura"
        )
        results = self._memory.search(
            user_id=user_id,
            query=critical_keywords,
            limit=settings.MEM0_CRITICAL_LIMIT,
        )
        return self._normalize_mem0_results(results, source="critical")

    def _retrieve_semantic_memories(
        self, user_id: str, query: str, limit: int | None = None
    ) -> list[dict]:
        """Retrieve semantic context based on current user input."""
        if limit is None:
            limit = settings.MEM0_SEMANTIC_LIMIT
        results = self._memory.search(user_id=user_id, query=query, limit=limit)
        return self._normalize_mem0_results(results, source="semantic")

    def _retrieve_recent_memories(self, user_id: str, limit: int | None = None) -> list[dict]:
        """Retrieve recently-added memories."""
        if limit is None:
            limit = settings.MEM0_RECENT_LIMIT
        try:
            results = self._memory.get_all(user_id=user_id, limit=limit)
            return self._normalize_mem0_results(results, source="recent")
        except Exception:  # pylint: disable=broad-exception-caught
            return []

    async def retrieve_hybrid_memories(self, user_input: str, user_id: str) -> dict:
        """
        Retrieves memories using Hybrid Search (Critical + Semantic + Recent).
        """
        logger.debug("Retrieving HYBRID memories for user: %s", user_id)

        # Parallel searches using asyncio.gather to reduce TTFT
        critical, semantic, recent = await asyncio.gather(
            asyncio.to_thread(self._retrieve_critical_facts, user_id),
            asyncio.to_thread(self._retrieve_semantic_memories, user_id, user_input),
            asyncio.to_thread(self._retrieve_recent_memories, user_id),
        )

        # Apply semantic deduplication first (within each category)
        critical = self._deduplicate_semantically(
            critical, threshold=settings.MEM0_SEMANTIC_DEDUP_THRESHOLD
        )
        semantic = self._deduplicate_semantically(
            semantic, threshold=settings.MEM0_SEMANTIC_DEDUP_THRESHOLD
        )
        recent = self._deduplicate_semantically(
            recent, threshold=settings.MEM0_SEMANTIC_DEDUP_THRESHOLD
        )

        # Then apply cross-category deduplication (prefer Critical > Semantic > Recent)
        seen_texts = set()

        unique_critical = []
        for m in critical:
            if m["text"] not in seen_texts:
                unique_critical.append(m)
                seen_texts.add(m["text"])

        unique_semantic = []
        for m in semantic:
            if m["text"] not in seen_texts:
                unique_semantic.append(m)
                seen_texts.add(m["text"])

        unique_recent = []
        for m in recent:
            if m["text"] not in seen_texts:
                unique_recent.append(m)
                seen_texts.add(m["text"])

        return {
            "critical": unique_critical,
            "semantic": unique_semantic,
            "recent": unique_recent,
        }

    def format_memories(self, hybrid_memories: dict) -> str:
        """
        Format hybrid memories into compact prompt-ready string with optimized size.
        """
        memory_sections = []
        total_size = 0
        max_size = settings.MEM0_MAX_CONTEXT_SIZE

        for category, header in [
            ("critical", MEMORY_CRITICAL),
            ("semantic", MEMORY_SEMANTIC),
            ("recent", MEMORY_RECENT),
        ]:
            memories = hybrid_memories.get(category, [])
            if not memories:
                continue

            section_lines = [header]

            for mem in memories:
                dt = self._format_date(mem.get("created_at"))
                text = mem["text"]

                # Compact format: "- Text [dd/mm]" or "- Text" if recent
                line = f"- {text} [{dt}]" if dt else f"- {text}"

                # Check size limit
                line_size = len(line) + 1  # +1 for newline
                if total_size + line_size > max_size:
                    logger.debug(
                        "Memory context truncated at %d bytes (max: %d)",
                        total_size,
                        max_size,
                    )
                    break

                section_lines.append(line)
                total_size += line_size

            if len(section_lines) > 1:  # Has content beyond header
                memory_sections.append("\n".join(section_lines))

        # Log memory stats for monitoring
        if memory_sections:
            logger.info(
                "Memory formatted: %d bytes. C: %d, S: %d, R: %d",
                total_size,
                len(hybrid_memories.get("critical", [])),
                len(hybrid_memories.get("semantic", [])),
                len(hybrid_memories.get("recent", [])),
            )

        return "\n\n".join(memory_sections) if memory_sections else MEMORY_NONE
