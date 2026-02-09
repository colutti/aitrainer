#!/usr/bin/env python3
"""
Memory Diagnostic Tool

Analyzes the memory system for a given user:
- MongoDB chat history size
- Mem0/Qdrant memory counts
- Long-term summary length
- Recent message timestamps

Usage:
    python scripts/diagnose_memory.py user@example.com
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.deps import get_mongo_database, get_mem0_client, get_qdrant_client
from src.core.config import settings
from datetime import datetime
import argparse


def diagnose_user_memory(user_email: str):
    """Diagnose memory system for a user."""
    print(f"\n{'='*70}")
    print(f"🔍 DIAGNÓSTICO DE MEMÓRIA - {user_email}")
    print(f"{'='*70}\n")

    # Get clients
    database = get_mongo_database()
    memory = get_mem0_client()
    qdrant = get_qdrant_client()

    # 1. User Profile & Summary
    print("📋 PERFIL DO USUÁRIO")
    print("-" * 70)
    profile = database.get_user_profile(user_email)
    if profile:
        print(f"✓ Nome: {user_email}")
        print(f"✓ Gênero: {profile.gender}")
        print(f"✓ Idade: {profile.age} anos")
        print(f"✓ Peso: {profile.weight}kg | Altura: {profile.height}cm")
        print(f"✓ Objetivo: {profile.goal_type} ({profile.weekly_rate}kg/semana)")

        if profile.long_term_summary:
            summary_len = len(profile.long_term_summary)
            print("\n📜 RESUMO DE LONGO PRAZO:")
            print(f"   Tamanho: {summary_len} caracteres")
            if profile.last_compaction_timestamp:
                last_comp = datetime.fromisoformat(profile.last_compaction_timestamp)
                age = datetime.now() - last_comp
                print(f"   Última compactação: {last_comp.strftime('%d/%m/%Y %H:%M')} ({age.days} dias atrás)")
            print("\n   Conteúdo (primeiros 300 chars):")
            print(f"   {profile.long_term_summary[:300]}...")
        else:
            print("\n⚠️  Nenhum resumo de longo prazo encontrado")
    else:
        print(f"❌ Perfil não encontrado para {user_email}")
        return

    # 2. MongoDB Chat History
    print("\n\n💬 HISTÓRICO DE CHAT (MongoDB)")
    print("-" * 70)
    all_history = database.get_chat_history(user_email, limit=1000)
    total_msgs = len(all_history)
    print(f"Total de mensagens: {total_msgs}")
    print(f"Janela ativa (MAX_SHORT_TERM_MEMORY_MESSAGES): {settings.MAX_SHORT_TERM_MEMORY_MESSAGES}")

    if total_msgs > 0:
        # Count by sender
        student_msgs = sum(1 for m in all_history if m.sender == "Student")
        trainer_msgs = sum(1 for m in all_history if m.sender == "Trainer")
        system_msgs = sum(1 for m in all_history if m.sender == "System")

        print(f"   - Aluno: {student_msgs}")
        print(f"   - Treinador: {trainer_msgs}")
        print(f"   - Sistema: {system_msgs}")

        # Recent messages
        recent_window = all_history[-settings.MAX_SHORT_TERM_MEMORY_MESSAGES:]
        print(f"\n📊 Últimas {len(recent_window)} mensagens (janela ativa):")
        for i, msg in enumerate(recent_window[-5:], start=max(0, len(recent_window) - 5)):
            ts = datetime.fromisoformat(msg.timestamp)
            sender_icon = "🧑" if msg.sender == "Student" else "🏋️" if msg.sender == "Trainer" else "⚙️"
            preview = msg.text[:60] + "..." if len(msg.text) > 60 else msg.text
            print(f"   [{i+1}] {sender_icon} {ts.strftime('%d/%m %H:%M')} - {preview}")

        # Messages outside window
        if total_msgs > settings.MAX_SHORT_TERM_MEMORY_MESSAGES:
            old_msgs = total_msgs - settings.MAX_SHORT_TERM_MEMORY_MESSAGES
            print(f"\n⚠️  {old_msgs} mensagens antigas FORA da janela ativa")
            if not profile.long_term_summary or not profile.last_compaction_timestamp:
                print("   ⚠️  AVISO: Essas mensagens não foram compactadas ainda!")
            else:
                last_comp = datetime.fromisoformat(profile.last_compaction_timestamp)
                oldest_msg = datetime.fromisoformat(all_history[0].timestamp)
                if oldest_msg > last_comp:
                    print("   ⚠️  AVISO: Há mensagens antigas não compactadas!")

    else:
        print("⚠️  Nenhuma mensagem encontrada")

    # 3. Mem0 Memories (Qdrant)
    print("\n\n💾 MEMÓRIAS MEM0 (Qdrant)")
    print("-" * 70)
    try:
        from qdrant_client import models as qdrant_models

        # Count memories for user
        user_filter = qdrant_models.Filter(
            must=[
                qdrant_models.FieldCondition(
                    key="user_id", match=qdrant_models.MatchValue(value=user_email)
                )
            ]
        )

        count_result = qdrant.count(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            count_filter=user_filter,
        )
        total_memories = count_result.count
        print(f"Total de memórias armazenadas: {total_memories}")

        # Search examples
        print("\n🔍 BUSCA HÍBRIDA (exemplo com query='treino'):")

        # Critical
        critical_keywords = (
            "alergia lesão dor objetivo meta restrição médico cirurgia "
            "preferência equipamento disponível horário treino experiência "
            "limitação físico histórico peso altura"
        )
        critical = memory.search(user_id=user_email, query=critical_keywords, limit=10)
        critical_results = critical.get("results", []) if isinstance(critical, dict) else critical
        print(f"   - Críticas: {len(critical_results)} (limit=10)")

        # Semantic
        semantic = memory.search(user_id=user_email, query="treino", limit=10)
        semantic_results = semantic.get("results", []) if isinstance(semantic, dict) else semantic
        print(f"   - Semânticas: {len(semantic_results)} (limit=10)")

        # Recent
        recent = memory.get_all(user_id=user_email, limit=10)
        recent_results = recent.get("results", []) if isinstance(recent, dict) else recent
        print(f"   - Recentes: {len(recent_results)} (limit=10)")

        print("\n📜 Amostra de memórias recentes:")
        for i, mem in enumerate(recent_results[:5], start=1):
            mem_text = mem.get("memory", "")
            created = mem.get("created_at", "")
            if created:
                try:
                    created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    created_str = created_dt.strftime("%d/%m/%Y")
                except Exception:
                    created_str = created
            else:
                created_str = "?"
            preview = mem_text[:70] + "..." if len(mem_text) > 70 else mem_text
            print(f"   [{i}] ({created_str}) {preview}")

    except Exception as e:
        print(f"❌ Erro ao acessar Qdrant: {e}")

    # 4. Summary
    print(f"\n\n{'='*70}")
    print("📊 RESUMO DO DIAGNÓSTICO")
    print(f"{'='*70}")

    status = []

    # Check 1: Summary exists
    if profile and profile.long_term_summary:
        status.append(("✅", f"Resumo de longo prazo: {len(profile.long_term_summary)} chars"))
    else:
        status.append(("⚠️ ", "Nenhum resumo de longo prazo"))

    # Check 2: Window sync
    if total_msgs <= settings.MAX_SHORT_TERM_MEMORY_MESSAGES:
        status.append(("✅", f"Histórico dentro da janela ({total_msgs}/{settings.MAX_SHORT_TERM_MEMORY_MESSAGES})"))
    else:
        old_count = total_msgs - settings.MAX_SHORT_TERM_MEMORY_MESSAGES
        status.append(("⚠️ ", f"{old_count} mensagens fora da janela (podem estar em limbo)"))

    # Check 3: Mem0 memories
    if total_memories > 0:
        status.append(("✅", f"{total_memories} memórias no Qdrant"))
    else:
        status.append(("⚠️ ", "Nenhuma memória no Qdrant"))

    # Check 4: Recent compaction
    if profile and profile.last_compaction_timestamp:
        last_comp = datetime.fromisoformat(profile.last_compaction_timestamp)
        age = datetime.now() - last_comp
        if age.days < 7:
            status.append(("✅", f"Compactação recente ({age.days} dias atrás)"))
        else:
            status.append(("⚠️ ", f"Compactação antiga ({age.days} dias atrás)"))
    else:
        if total_msgs > settings.MAX_SHORT_TERM_MEMORY_MESSAGES:
            status.append(("⚠️ ", "Nenhuma compactação realizada (necessária)"))

    print()
    for icon, msg in status:
        print(f"{icon} {msg}")

    print(f"\n{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Diagnose memory system for a user",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/diagnose_memory.py user@example.com
  python scripts/diagnose_memory.py --list-users
        """,
    )
    parser.add_argument("email", nargs="?", help="User email to diagnose")
    parser.add_argument("--list-users", action="store_true", help="List all users")

    args = parser.parse_args()

    if args.list_users:
        _ = get_mongo_database()
        from pymongo import MongoClient

        client = MongoClient(settings.MONGO_URI)
        db = client[settings.DB_NAME]
        users_collection = db["users"]

        print("\n📋 USUÁRIOS DISPONÍVEIS:")
        print("-" * 70)
        for user in users_collection.find({}, {"email": 1}):
            print(f"   - {user['email']}")
        print()
        return

    if not args.email:
        parser.print_help()
        return

    diagnose_user_memory(args.email)


if __name__ == "__main__":
    main()
