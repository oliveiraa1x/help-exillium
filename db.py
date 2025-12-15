import os
import json
from pathlib import Path

# ==============================
# Configuração MongoDB (Opcional)
# ==============================
try:
    from pymongo import MongoClient
    from pymongo.errors import ConfigurationError
    MONGO_URI = os.getenv("MONGO_URI")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME") or os.getenv("MONGO_DB")

    if MONGO_URI:
        client = MongoClient(MONGO_URI)
        try:
            # Tenta obter o banco padrão a partir da URI
            db = client.get_default_database()
            print("✅ Conectado ao MongoDB (default DB from URI).")
        except ConfigurationError:
            # Se a URI não contém um database padrão, usar MONGO_DB_NAME se fornecido
            if MONGO_DB_NAME:
                db = client[MONGO_DB_NAME]
                print(f"✅ Conectado ao MongoDB (db: {MONGO_DB_NAME}).")
            else:
                print("⚠️ MONGO_URI não contém default DB e MONGO_DB_NAME não definido. Usando JSON localmente.")
                db = None
    else:
        print("⚠️ MongoDB não configurado. Usando JSON localmente.")
        db = None
except ImportError:
    print("⚠️ pymongo não instalado. Usando JSON localmente.")
    db = None

# ==============================
# Configuração de Caminhos JSON
# ==============================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

ECONOMIA_DB_PATH = DATA_DIR / "economia.json"
PERFIL_DB_PATH = DATA_DIR / "perfil.json"
TOP_TEMPO_DB_PATH = DATA_DIR / "top_tempo.json"
DB_JSON_PATH = DATA_DIR / "db.json"

# ==============================
# Funções Auxiliares
# ==============================
def ensure_data_dir() -> None:
    """Garante que o diretório de dados existe"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


# ==============================
# Sistema de Banco de Dados para Economia
# ==============================
def ensure_economia_db_file() -> None:
    """Garante que o arquivo de banco de dados de economia existe"""
    ensure_data_dir()
    if not ECONOMIA_DB_PATH.exists():
        ECONOMIA_DB_PATH.write_text("{}", encoding="utf-8")


def load_economia_db() -> dict:
    """Carrega o banco de dados de economia"""
    ensure_economia_db_file()
    try:
        with ECONOMIA_DB_PATH.open("r", encoding="utf-8") as fp:
            return json.load(fp)
    except json.JSONDecodeError:
        return {}


def save_economia_db(data: dict) -> None:
    """Salva o banco de dados de economia"""
    ensure_economia_db_file()
    with ECONOMIA_DB_PATH.open("w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)


# ==============================
# Sistema de Banco de Dados para Perfil
# ==============================
def ensure_perfil_db_file() -> None:
    """Garante que o arquivo de banco de dados de perfil existe"""
    ensure_data_dir()
    if not PERFIL_DB_PATH.exists():
        PERFIL_DB_PATH.write_text("{}", encoding="utf-8")


def load_perfil_db() -> dict:
    """Carrega o banco de dados de perfil"""
    ensure_perfil_db_file()
    try:
        with PERFIL_DB_PATH.open("r", encoding="utf-8") as fp:
            return json.load(fp)
    except json.JSONDecodeError:
        return {}


def save_perfil_db(data: dict) -> None:
    """Salva o banco de dados de perfil"""
    ensure_perfil_db_file()
    with PERFIL_DB_PATH.open("w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)


# ==============================
# Sistema de Banco de Dados para Top Tempo
# ==============================
def ensure_top_tempo_db_file() -> None:
    """Garante que o arquivo de banco de dados de top tempo existe"""
    ensure_data_dir()
    if not TOP_TEMPO_DB_PATH.exists():
        TOP_TEMPO_DB_PATH.write_text("{}", encoding="utf-8")


def load_top_tempo_db() -> dict:
    """Carrega o banco de dados de top tempo"""
    ensure_top_tempo_db_file()
    try:
        with TOP_TEMPO_DB_PATH.open("r", encoding="utf-8") as fp:
            return json.load(fp)
    except json.JSONDecodeError:
        return {}


def save_top_tempo_db(data: dict) -> None:
    """Salva o banco de dados de top tempo"""
    ensure_top_tempo_db_file()
    with TOP_TEMPO_DB_PATH.open("w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)


# ==============================
# Sistema de Banco de Dados Geral (db.json)
# ==============================
def ensure_db_file() -> None:
    """Garante que o arquivo de banco de dados geral existe"""
    ensure_data_dir()
    if not DB_JSON_PATH.exists():
        DB_JSON_PATH.write_text("{}", encoding="utf-8")


def load_db() -> dict:
    """Carrega o banco de dados geral"""
    ensure_db_file()
    try:
        with DB_JSON_PATH.open("r", encoding="utf-8") as fp:
            return json.load(fp)
    except json.JSONDecodeError:
        return {}


def save_db(data: dict) -> None:
    """Salva o banco de dados geral"""
    ensure_db_file()
    with DB_JSON_PATH.open("w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)


# ==============================
# Função de Sincronização de Dados
# ==============================
def sync_all_databases() -> None:
    """
    Sincroniza todos os bancos de dados.
    Use esta função para salvar todos os dados de uma vez.
    """
    try:
        # Verifica e valida cada banco de dados
        economia = load_economia_db()
        save_economia_db(economia)
        
        perfil = load_perfil_db()
        save_perfil_db(perfil)
        
        top_tempo = load_top_tempo_db()
        save_top_tempo_db(top_tempo)
        
        db_geral = load_db()
        save_db(db_geral)
        
        print("✅ Todos os bancos de dados foram sincronizados com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao sincronizar bancos de dados: {e}")
