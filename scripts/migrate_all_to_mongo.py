"""
Migra todos os JSONs locais em `data/` para coleções separadas no MongoDB:
 - `data/economia.json` -> coleção `economia` (documento por usuário, _id = uid)
 - `data/perfil.json` -> coleção `perfil`
 - `data/top_tempo.json` -> coleção `top_tempo`
 - `data/db.json` -> coleção `db` (documento único com _id='db')

Uso:
  - Defina `MONGO_URI` e opcionalmente `MONGO_DB_NAME` nas variáveis de ambiente.
  - Execute: `python scripts/migrate_all_to_mongo.py`
"""

import os
import json
from pathlib import Path

try:
    from pymongo import MongoClient
except ImportError:
    print("pymongo não está instalado. Instale com: pip install pymongo")
    raise

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME") or os.getenv("MONGO_DB")

if not MONGO_URI:
    print("Erro: variável de ambiente MONGO_URI não definida.")
    raise SystemExit(1)

client = MongoClient(MONGO_URI)
if MONGO_DB_NAME:
    mdb = client[MONGO_DB_NAME]
else:
    mdb = client.get_default_database()

print(f"Conectado ao MongoDB (db: {mdb.name})")

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

FILES = {
    "economia": DATA_DIR / "economia.json",
    "perfil": DATA_DIR / "perfil.json",
    "top_tempo": DATA_DIR / "top_tempo.json",
    "db": DATA_DIR / "db.json",
}

for coll_name, path in FILES.items():
    if not path.exists():
        print(f"Pular {path} (não existe)")
        continue
    try:
        with path.open("r", encoding="utf-8") as fp:
            data = json.load(fp)
    except json.JSONDecodeError:
        print(f"Arquivo inválido: {path}")
        continue

    coll = mdb.get_collection(coll_name)

    if coll_name == "db":
        coll.update_one({"_id": "db"}, {"$set": {"data": data}}, upsert=True)
        print(f"Migrado {path} -> coleção {coll_name} (documento único)")
        continue

    # Para as coleções por usuário: data deve ser um dict {uid: value}
    count = 0
    for uid, value in data.items():
        if isinstance(value, dict):
            coll.update_one({"_id": str(uid)}, {"$set": value}, upsert=True)
        else:
            coll.update_one({"_id": str(uid)}, {"$set": {"value": value}}, upsert=True)
        count += 1
    print(f"Migrado {count} documentos para coleção {coll_name}")

print("Migração completa.")
