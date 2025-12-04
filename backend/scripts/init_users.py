import argparse
import logging
import os
import sys

import bcrypt
import pymongo

from ..config import DB_NAME, MONGO_URI

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("init_users")

# Script para criar usuário admin no MongoDB para o Treinador Pessoal IA.
# Uso: python3 scripts/init_users.py --username meuusuario --password minhasenha

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def main():
    """Função principal para criar usuário admin no MongoDB."""
    parser = argparse.ArgumentParser(description="Cria usuário admin no MongoDB.")
    parser.add_argument("--email", required=True, help="E-mail do usuário")
    parser.add_argument("--password", required=True, help="Senha do usuário")
    args = parser.parse_args()

    logger.info("Connecting to MongoDB at URI: %s, DB: %s", MONGO_URI, DB_NAME)
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DB_NAME]  # type: ignore[arg-type]
    users = db.users

    logger.info("Checking if user already exists: %s", args.email)
    if users.find_one({"email": args.email}):
        logger.warning("User '%s' already exists.", args.email)
        print(f"Usuário '{args.email}' já existe.")
        sys.exit(0)

    logger.info("Hashing password and creating user: %s", args.email)
    password_hash = bcrypt.hashpw(args.password.encode(), bcrypt.gensalt()).decode()
    users.insert_one({
        "email": args.email,
        "password_hash": password_hash
    })
    logger.info("User '%s' created successfully.", args.email)
    print(f"Usuário '{args.email}' criado com sucesso.")


if __name__ == "__main__":
    main()
