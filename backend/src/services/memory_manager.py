"""
Memory management service for hybrid memory retrieval and formatting.

Extracts memory-related operations from AITrainerBrain for better modularity:
- Hybrid memory retrieval (critical, semantic, recent)
- Memory deduplication
- Memory formatting for prompt injection
"""

from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from src.core.logs import logger
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
        """Helper to format date strings to DD/MM format."""
        if not date_str:
            return "Data desc."
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime("%d/%m")
        except (ValueError, AttributeError):
            return "Data desc."

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
                    }
                )
        return normalized

    def _retrieve_critical_facts(self, user_id: str) -> list[dict]:
        """
        Explicit search for critical facts (health, injuries, goals) with priority.
        Ensures 'alergia', 'lesão', etc. are recovered even if semantic search fails.
        """
        critical_keywords = (
            "alergia lesão dor objetivo meta restrição médico cirurgia "
            "preferência equipamento disponível horário treino experiência "
            "limitação físico histórico peso altura"
        )
        results = self._memory.search(user_id=user_id, query=critical_keywords, limit=10)
        return self._normalize_mem0_results(results, source="critical")

    def _retrieve_semantic_memories(
        self, user_id: str, query: str, limit: int = 10
    ) -> list[dict]:
        """Retrieve semantic context based on current user input."""
        results = self._memory.search(user_id=user_id, query=query, limit=limit)
        return self._normalize_mem0_results(results, source="semantic")

    def _retrieve_recent_memories(self, user_id: str, limit: int = 10) -> list[dict]:
        """Retrieve recently-added memories (short-term temporal context)."""
        try:
            results = self._memory.get_all(user_id=user_id, limit=limit)
            return self._normalize_mem0_results(results, source="recent")
        except Exception:
            return []

    def retrieve_hybrid_memories(self, user_input: str, user_id: str) -> dict:
        """
        Retrieves memories using Hybrid Search (Critical + Semantic + Recent).
        Uses parallel execution to reduce latency.

        Returns:
            dict: Structured dictionary with critical, semantic, and recent memories.
        """
        logger.debug("Retrieving HYBRID memories for user: %s", user_id)

        # Parallel searches to reduce TTFT
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_critical = executor.submit(self._retrieve_critical_facts, user_id)
            future_semantic = executor.submit(
                self._retrieve_semantic_memories, user_id, user_input
            )
            future_recent = executor.submit(self._retrieve_recent_memories, user_id)

            critical = future_critical.result()
            semantic = future_semantic.result()
            recent = future_recent.result()

        # Deduplicate (prefer Critical > Semantic > Recent)
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
        Format hybrid memories into prompt-ready string with simplified headers.

        Args:
            hybrid_memories: dict with 'critical', 'semantic', 'recent' keys

        Returns:
            str: Formatted memory string for prompt injection
        """
        memory_sections = []

        if hybrid_memories["critical"]:
            sec = [MEMORY_CRITICAL]
            for mem in hybrid_memories["critical"]:
                dt = self._format_date(mem.get("created_at"))
                sec.append(f"- ({dt}) {mem['text']}")
            memory_sections.append("\n".join(sec))

        if hybrid_memories["semantic"]:
            sec = [MEMORY_SEMANTIC]
            for mem in hybrid_memories["semantic"]:
                dt = self._format_date(mem.get("created_at"))
                sec.append(f"- ({dt}) {mem['text']}")
            memory_sections.append("\n".join(sec))

        if hybrid_memories["recent"]:
            sec = [MEMORY_RECENT]
            for mem in hybrid_memories["recent"]:
                dt = self._format_date(mem.get("created_at"))
                sec.append(f"- ({dt}) {mem['text']}")
            memory_sections.append("\n".join(sec))

        return "\n\n".join(memory_sections) if memory_sections else MEMORY_NONE
