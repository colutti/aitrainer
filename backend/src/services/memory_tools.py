"""
LangChain tools for AI-driven memory management.

The AI agent can explicitly save, search, update, and delete memories,
replacing the automatic Mem0 extraction with agent-controlled memory curation.

Uses Gemini embeddings with dimensionality reduction to ensure 768-dim
compatibility with existing Qdrant vectors.
"""

from datetime import datetime
from uuid import uuid4
import numpy as np
from langchain_core.tools import tool
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

from src.core.config import settings
from src.core.logs import logger

# pylint: disable=broad-exception-caught
# Justificativa: Qdrant Client não expõe exceções específicas para todas as falhas,
# precisamos evitar que erros de conexão/API quebrem as interações da IA.


def _get_embedder() -> GoogleGenerativeAIEmbeddings:
    """Returns a Gemini embedder for generating 768-dim vectors."""
    return GoogleGenerativeAIEmbeddings(
        model=settings.GEMINI_EMBEDDER_MODEL,
        google_api_key=settings.GEMINI_API_KEY
    )


def _embed_text(text: str) -> list:
    """
    Generate 768-dim embedding from text using Gemini with dimensionality reduction.

    Gemini returns 3072-dim vectors which we reduce to 768-dim via average pooling.
    """
    embedder = _get_embedder()
    embedding = embedder.embed_query(text)

    # Reduce 3072 → 768 via average pooling
    embedding_array = np.array(embedding)
    reduced = embedding_array.reshape(-1, 4).mean(axis=1)

    # Normalize
    reduced = reduced / np.linalg.norm(reduced)

    return reduced.tolist()


def _get_collection_name(_user_email: str) -> str:
    """Returns collection name (shared across all users)."""
    return settings.QDRANT_COLLECTION_NAME


def _ensure_collection(qdrant_client: QdrantClient, collection_name: str):
    """Creates collection if it doesn't exist."""
    try:
        qdrant_client.get_collection(collection_name)
    except (ValueError, TypeError, AttributeError, Exception):
        # Collection doesn't exist, create it
        logger.info("Creating Qdrant collection: %s", collection_name)
        try:
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE),
            )
        except (ValueError, TypeError, AttributeError, Exception) as create_error:
            # Handle race condition
            if "already exists" not in str(create_error):
                logger.error("Failed to create collection %s: %s", collection_name, create_error)
                raise


def create_save_memory_tool(qdrant_client: QdrantClient, user_email: str):
    """
    Factory function to create a save_memory tool with injected dependencies.

    Args:
        qdrant_client: Qdrant client for vector storage
        user_email: User email for ownership and filtering
    """

    @tool
    def save_memory(content: str, category: str) -> str:
        """
        Salva uma memória importante sobre o aluno.

        QUANDO SALVAR:
        - Lesão, alergia, restrição, condição médica
        - Preferência de treino/alimentação/horário
        - Objetivo ou mudança de objetivo
        - Contexto importante (viagem, rotina, equipamento)

        QUANDO NÃO SALVAR:
        - Dados já salvos por outras ferramentas (treinos, nutrição, peso)
        - Conversas triviais, saudações
        - Info temporária ("hoje estou cansado")

        ⚠️ DEDUPLICAÇÃO: Antes de salvar, SEMPRE busque com search_memory
        se já existe algo similar. Se encontrar, use update_memory.

        Argumentos:
        - content: O conteúdo da memória (ex: "Tem alergia a amendoim")
        - category: Categoria da memória. Opções:
          "preference", "limitation", "goal", "health", "context"

        Exemplos:
        - save_memory(content="Prefere treinar de manhã", category="preference")
        - save_memory(content="Tem dor nas costas", category="limitation")
        """
        try:
            # pylint: disable=import-outside-toplevel
            from qdrant_client import models as qdrant_models

            valid_categories = {"preference", "limitation", "goal", "health", "context"}
            if category not in valid_categories:
                return f"Erro: categoria '{category}' inválida. Use: {', '.join(valid_categories)}"

            collection_name = _get_collection_name(user_email)
            _ensure_collection(qdrant_client, collection_name)

            # Generate 768-dim embedding using Gemini with dimensionality reduction
            embedding = _embed_text(content)

            # Check for semantic duplicates before saving
            user_filter = qdrant_models.Filter(
                must=[
                    qdrant_models.FieldCondition(
                        key="user_id", match=qdrant_models.MatchValue(value=user_email)
                    )
                ]
            )
            similar_results = qdrant_client.query_points(
                collection_name=collection_name,
                query=embedding,
                query_filter=user_filter,
                limit=1,
                score_threshold=0.92,  # High threshold for semantic duplicates
                with_payload=True,
            )

            if similar_results.points:
                existing = similar_results.points[0]
                existing_id = existing.payload.get("id", existing.id)
                existing_text = existing.payload.get("memory", "")[:80]
                logger.info("Duplicate memory found for %s: %s", user_email, existing_id)
                return (
                    f"⚠️ Memória similar já existe (ID: {existing_id}): \"{existing_text}...\"\n"
                    f"Use update_memory(memory_id='{existing_id}', "
                    "new_content=...) para atualizar, "
                    "ou delete_memory para remover antes de criar uma nova."
                )

            # Create point
            memory_id = str(uuid4())
            now = datetime.utcnow().isoformat()
            point = PointStruct(
                id=memory_id,
                vector=embedding,
                payload={
                    "id": memory_id,
                    "memory": content,
                    "category": category,
                    "user_id": user_email,
                    "created_at": now,
                    "updated_at": now,
                },
            )

            # Upsert to Qdrant
            qdrant_client.upsert(collection_name, points=[point])
            logger.info(
                "Saved memory for %s (ID: %s, category: %s)",
                user_email, memory_id, category
            )

            return f"✅ Memória salva (ID: {memory_id}): {content[:60]}..."

        except ValueError as e:
            logger.error("Validation error in save_memory: %s", e)
            return f"Erro de validação: {str(e)}"
        except (TypeError, AttributeError, Exception) as e:
            logger.error("Failed to save memory for %s: %s", user_email, e)
            return "❌ Erro ao salvar memória. Tente novamente."

    return save_memory


def create_search_memory_tool(qdrant_client: QdrantClient, user_email: str):
    """
    Factory function to create a search_memory tool with injected dependencies.

    Args:
        qdrant_client: Qdrant client for vector search
        user_email: User email for filtering
    """

    @tool
    def search_memory(query: str, limit: int = 5) -> str:
        # pylint: disable=too-many-locals
        """
        Busca memórias relacionadas a uma query.

        QUANDO BUSCAR:
        - Antes de dar conselho personalizado ou criar plano
        - Quando precisar de contexto sobre histórico do aluno
        - ANTES de salvar qualquer memória (verificar duplicatas)

        Argumentos:
        - query: Descrição do que procurar (ex: "limitações", "preferências")
        - limit: Número máximo de memórias a retornar (default: 5)

        Exemplo:
        - search_memory(query="limitações", limit=5)
        """
        try:
            # pylint: disable=import-outside-toplevel
            from qdrant_client import models as qdrant_models

            collection_name = _get_collection_name(user_email)

            # Check if collection exists
            try:
                qdrant_client.get_collection(collection_name)
            except (ValueError, TypeError, AttributeError, Exception):
                return "Nenhuma memória encontrada (coleção vazia)."

            # Generate query embedding with Gemini + dimensionality reduction
            query_embedding = _embed_text(query)

            # Filter by user_id to ensure data isolation
            user_filter = qdrant_models.Filter(
                must=[
                    qdrant_models.FieldCondition(
                        key="user_id", match=qdrant_models.MatchValue(value=user_email)
                    )
                ]
            )

            # Search in Qdrant using query_points (vector search with filter)
            query_response = qdrant_client.query_points(
                collection_name=collection_name,
                query=query_embedding,
                query_filter=user_filter,
                limit=limit,
                with_payload=True,
            )
            results = query_response.points if query_response else []

            if not results:
                return f"Nenhuma memória encontrada para: '{query}'"

            # Format results
            formatted_results = []
            for result in results:
                payload = result.payload
                memory_text = payload.get("memory", "")
                memory_id = payload.get("id", result.id)
                category = payload.get("category", "")
                created_at = payload.get("created_at", "")

                # Format date if present
                date_str = ""
                if created_at:
                    try:
                        date_obj = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                        date_str = date_obj.strftime("%d/%m/%Y")
                    except (ValueError, TypeError, AttributeError):
                        pass

                formatted_results.append(
                    f"ID: {memory_id} | [{category}] {memory_text}"
                    + (f" [{date_str}]" if date_str else "")
                )

            return "\n".join(formatted_results)

        except (ValueError, TypeError, AttributeError, Exception) as e:
            logger.error("Failed to search memories for %s: %s", user_email, e)
            return "❌ Erro ao buscar memórias. Tente novamente."

    return search_memory


def create_update_memory_tool(qdrant_client: QdrantClient, user_email: str):
    """
    Factory function to create an update_memory tool with injected dependencies.

    Args:
        qdrant_client: Qdrant client for vector updates
        user_email: User email for filtering
    """

    @tool
    def update_memory(memory_id: str, new_content: str) -> str:
        """
        Atualiza o conteúdo de uma memória existente.

        Argumentos:
        - memory_id: ID da memória a atualizar (obtido via search_memory)
        - new_content: Novo conteúdo da memória

        Exemplo:
        - update_memory(memory_id="abc123", new_content="Agora treina de tarde")
        """
        try:
            collection_name = _get_collection_name(user_email)

            # Retrieve existing point
            points = qdrant_client.retrieve(collection_name, ids=[memory_id])

            if not points:
                return f"Memória não encontrada: {memory_id}"

            point = points[0]
            payload = point.payload or {}

            # Verify ownership
            if payload.get("user_id") != user_email:
                return "❌ Você não tem permissão para atualizar esta memória."

            # Generate new embedding with Gemini + dimensionality reduction
            new_embedding = _embed_text(new_content)

            # Update payload
            now = datetime.utcnow().isoformat()
            updated_payload = {
                **payload,
                "memory": new_content,
                "updated_at": now,
            }

            # Create updated point
            updated_point = PointStruct(
                id=memory_id,
                vector=new_embedding,
                payload=updated_payload,
            )

            # Upsert updated point
            qdrant_client.upsert(collection_name, points=[updated_point])
            logger.info("Updated memory %s for user %s", memory_id, user_email)

            return f"✅ Memória atualizada (ID: {memory_id}): {new_content[:60]}..."

        except (ValueError, TypeError, AttributeError, Exception) as e:
            logger.error("Failed to update memory %s for %s: %s", memory_id, user_email, e)
            return "❌ Erro ao atualizar memória. Tente novamente."

    return update_memory


def create_delete_memory_tool(qdrant_client: QdrantClient, user_email: str):
    """
    Factory function to create a delete_memory tool with injected dependencies.

    Args:
        qdrant_client: Qdrant client for deletion
        user_email: User email for filtering
    """

    @tool
    def delete_memory(memory_id: str) -> str:
        """
        Deleta uma memória existente.

        Argumentos:
        - memory_id: ID da memória a deletar (obtido via search_memory)

        Exemplo:
        - delete_memory(memory_id="abc123")
        """
        try:
            collection_name = _get_collection_name(user_email)

            # Retrieve to verify ownership
            points = qdrant_client.retrieve(collection_name, ids=[memory_id])

            if not points:
                return f"Memória não encontrada: {memory_id}"

            point = points[0]
            payload = point.payload or {}

            # Verify ownership
            if payload.get("user_id") != user_email:
                return "❌ Você não tem permissão para deletar esta memória."

            # Delete point
            qdrant_client.delete(collection_name, points_selector=[memory_id])
            logger.info("Deleted memory %s for user %s", memory_id, user_email)

            return f"✅ Memória deletada (ID: {memory_id})"

        except (ValueError, TypeError, AttributeError, Exception) as e:
            logger.error("Failed to delete memory %s for %s: %s", memory_id, user_email, e)
            return "❌ Erro ao deletar memória. Tente novamente."

    return delete_memory


def create_list_raw_memories_tool(qdrant_client: QdrantClient, user_email: str):
    """
    Factory function to create a list_raw_memories tool with injected dependencies.

    Args:
        qdrant_client: Qdrant client for retrieving memories
        user_email: User email for filtering
    """

    @tool
    def list_raw_memories(limit: int = 50) -> str:
        # pylint: disable=too-many-locals
        """
        Lista todas as memórias brutas do usuário (últimas X criadas).

        Argumentos:
        - limit: Número máximo de memórias a retornar (default: 50, max: 200)

        Exemplo:
        - list_raw_memories(limit=10)

        Retorna as memórias ordenadas por data de criação (mais recentes primeiro),
        com todos os detalhes necessários para revisar, editar ou deletar.
        """
        try:
            # pylint: disable=import-outside-toplevel
            from qdrant_client import models as qdrant_models

            # Validate limit
            limit = max(1, min(int(limit), 200))  # Between 1 and 200

            collection_name = _get_collection_name(user_email)

            # Check if collection exists
            try:
                qdrant_client.get_collection(collection_name)
            except (ValueError, TypeError, AttributeError, Exception):  # pylint: disable=broad-exception-caught
                return "Nenhuma memória encontrada."

            # Filter by user_id
            user_filter = qdrant_models.Filter(
                must=[
                    qdrant_models.FieldCondition(
                        key="user_id", match=qdrant_models.MatchValue(value=user_email)
                    )
                ]
            )

            from src.utils.qdrant_utils import scroll_all_user_points  # pylint: disable=import-outside-toplevel
            all_points = scroll_all_user_points(qdrant_client, collection_name, user_filter)

            # Sort by created_at descending (newest first)
            all_points.sort(
                key=lambda p: p.payload.get("created_at", "") if p.payload else "",
                reverse=True,
            )

            # Apply limit
            limited_points = all_points[:limit]

            if not limited_points:
                return "Nenhuma memória encontrada."

            # Format results with all necessary details for review/edit/delete
            formatted_results = []
            for idx, point in enumerate(limited_points, 1):
                payload = point.payload or {}
                memory_id = payload.get("id", str(point.id))
                memory_text = payload.get("memory", "")
                category = payload.get("category", "")
                created_at = payload.get("created_at", "")
                updated_at = payload.get("updated_at", "")

                # Format dates
                created_str = ""
                updated_str = ""
                try:
                    if created_at:
                        created_obj = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                        created_str = created_obj.strftime("%d/%m/%Y %H:%M")
                    if updated_at:
                        updated_obj = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                        updated_str = updated_obj.strftime("%d/%m/%Y %H:%M")
                except (ValueError, TypeError, AttributeError):
                    pass

                formatted_results.append(
                    f"{idx}. ID: {memory_id}\n"
                    f"   [{category}] {memory_text}\n"
                    f"   Criada: {created_str}\n"
                    f"   {'Atualizada: ' + updated_str if updated_str else ''}"
                )

            result_str = "\n".join(formatted_results)
            return f"📋 Últimas {len(limited_points)} memórias:\n\n{result_str}"

        except (ValueError, TypeError, AttributeError, Exception) as e:
            logger.error("Failed to list raw memories for %s: %s", user_email, e)
            return "❌ Erro ao listar memórias. Tente novamente."

    return list_raw_memories


def create_delete_memories_batch_tool(qdrant_client: QdrantClient, user_email: str):
    """
    Factory function to create a delete_memories_batch tool with injected dependencies.

    Args:
        qdrant_client: Qdrant client for batch deletion
        user_email: User email for filtering
    """

    @tool
    def delete_memories_batch(memory_ids: list[str]) -> str:
        """
        Deleta múltiplas memórias em uma única operação (batch).

        Argumentos:
        - memory_ids: Lista de IDs das memórias a deletar

        Exemplo:
        - delete_memories_batch(memory_ids=["id1", "id2", "id3"])

        Retorna um resumo de quantas foram deletadas com sucesso
        e quantas falharam (não encontradas ou não pertencentes ao usuário).
        """
        try:
            collection_name = _get_collection_name(user_email)

            if not memory_ids:
                return "❌ Nenhum ID fornecido para deletar."

            if len(memory_ids) > 100:
                return f"❌ Máximo de 100 IDs por operação. Você forneceu {len(memory_ids)}."

            # Retrieve all memory IDs to verify ownership
            points = qdrant_client.retrieve(collection_name, ids=memory_ids)

            if not points:
                return "❌ Nenhuma memória encontrada com os IDs fornecidos."

            # Verify ownership and collect IDs to delete
            authorized_ids = []
            unauthorized_count = 0

            for point in points:
                payload = point.payload or {}
                if payload.get("user_id") == user_email:
                    authorized_ids.append(str(point.id))
                else:
                    unauthorized_count += 1

            # Check for missing IDs
            found_ids = {str(p.id) for p in points}
            provided_ids = set(str(id) for id in memory_ids)
            missing_ids = provided_ids - found_ids
            missing_count = len(missing_ids)

            if not authorized_ids:
                return "❌ Você não tem permissão para deletar nenhuma dessas memórias."

            # Delete all authorized memories
            qdrant_client.delete(collection_name, points_selector=authorized_ids)
            logger.info(
                "Batch deleted %d memories for user %s (unauthorized: %d, missing: %d)",
                len(authorized_ids),
                user_email,
                unauthorized_count,
                missing_count,
            )

            # Build response message
            msg_parts = [f"✅ {len(authorized_ids)} memória(s) deletada(s)"]

            if unauthorized_count > 0:
                msg_parts.append(f"⚠️  {unauthorized_count} não autorizada(s)")

            if missing_count > 0:
                msg_parts.append(f"⚠️  {missing_count} não encontrada(s)")

            return " | ".join(msg_parts)

        except (ValueError, TypeError, AttributeError, Exception) as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to batch delete memories for %s: %s", user_email, e)
            return "❌ Erro ao deletar memórias. Tente novamente."

    return delete_memories_batch
