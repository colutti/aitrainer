#!/usr/bin/env python3
"""
Script para promover usuário a admin.
Funciona em ambiente local (via podman-compose) e produção (via env vars).

Uso:
    python promote_admin.py <email>

Exemplos:
    python promote_admin.py rafacolucci@gmail.com
    python promote_admin.py admin@example.com
"""
import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv


def promote_admin(email: str):
    """Promove usuário a admin."""
    # Detectar ambiente
    running_in_container = os.getenv("RUNNING_IN_CONTAINER") == "true"

    if not running_in_container:
        # Local: carregar .env
        env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
        if os.path.exists(env_path):
            load_dotenv(env_path)
            print(f"📁 Carregado .env de: {env_path}")
        else:
            print(f"⚠️  Arquivo .env não encontrado em: {env_path}")
            print("   Tentando usar variáveis de ambiente do sistema...")

    # Obter credenciais MongoDB
    mongo_uri = os.getenv("MONGO_URI")
    db_name = os.getenv("DB_NAME", "aitrainer")

    if not mongo_uri:
        print("❌ MONGO_URI não configurado")
        print("   Configure a variável de ambiente MONGO_URI")
        sys.exit(1)

    print(f"🔗 Conectando ao MongoDB: {db_name}")

    try:
        # Conectar ao MongoDB
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)

        # Testar conexão
        client.admin.command('ping')
        print("✅ Conexão estabelecida")

        db = client[db_name]

        # Verificar se usuário existe
        print(f"🔍 Buscando usuário: {email}")
        user = db.users.find_one({"email": email})

        if not user:
            print(f"❌ Usuário {email} não encontrado")
            print(f"   Certifique-se que o usuário está registrado no sistema")
            sys.exit(1)

        # Verificar se já é admin
        current_role = user.get("role", "user")
        if current_role == "admin":
            print(f"ℹ️  Usuário {email} já é admin")
            print(f"   Nenhuma ação necessária")
            return

        # Promover a admin
        print(f"⬆️  Promovendo {email} de '{current_role}' para 'admin'...")
        result = db.users.update_one(
            {"email": email},
            {"$set": {"role": "admin"}}
        )

        if result.modified_count > 0:
            print(f"✅ Usuário {email} promovido a admin com sucesso!")

            # Verificação
            updated_user = db.users.find_one({"email": email})
            verified_role = updated_user.get("role")
            print(f"   ✓ Role verificado: {verified_role}")

            if verified_role != "admin":
                print(f"   ⚠️  AVISO: Role não está correto após atualização!")
        else:
            print(f"❌ Falha ao promover {email}")
            print(f"   Nenhum documento foi modificado")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Erro ao conectar ou atualizar banco de dados:")
        print(f"   {type(e).__name__}: {e}")
        sys.exit(1)
    finally:
        if 'client' in locals():
            client.close()
            print("🔌 Conexão fechada")


def main():
    """Ponto de entrada do script."""
    if len(sys.argv) != 2:
        print("Uso: python promote_admin.py <email>")
        print()
        print("Exemplos:")
        print("  python promote_admin.py rafacolucci@gmail.com")
        print("  python promote_admin.py admin@example.com")
        sys.exit(1)

    email = sys.argv[1]

    # Validação básica de email
    if "@" not in email or "." not in email:
        print(f"❌ Email inválido: {email}")
        sys.exit(1)

    print("=" * 60)
    print("🔐 Script de Promoção de Admin")
    print("=" * 60)
    print()

    promote_admin(email)

    print()
    print("=" * 60)
    print("✅ Processo concluído")
    print("=" * 60)


if __name__ == "__main__":
    main()
