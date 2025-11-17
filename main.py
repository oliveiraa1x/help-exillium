import datetime
import json
import os
from pathlib import Path
from itertools import cycle

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv


# ==============================
# Configurações básicas
# ==============================
BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data" / "db.json"
CONFIG_PATH = BASE_DIR / "config.json"


def ensure_data_file() -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_PATH.exists():
        DATA_PATH.write_text("{}", encoding="utf-8")


def load_db() -> dict:
    ensure_data_file()
    with DATA_PATH.open("r", encoding="utf-8") as fp:
        try:
            return json.load(fp)
        except json.JSONDecodeError:
            # Corrige arquivos corrompidos
            return {}


def save_db(data: dict) -> None:
    ensure_data_file()
    with DATA_PATH.open("w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)


def resolve_token() -> str:
    load_dotenv()
    token = os.getenv("TOKEN")

    if token:
        return token

    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("r", encoding="utf-8") as fp:
            try:
                cfg = json.load(fp)
            except json.JSONDecodeError:
                cfg = {}
        token = cfg.get("TOKEN")

    if not token:
        raise RuntimeError(
            "TOKEN não encontrado. Configure a variável de ambiente ou o arquivo config.json."
        )

    return token


TOKEN = resolve_token()


# ==============================
# Cria o BOT e variáveis globais
# ==============================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=".", intents=intents)
bot.start_time = datetime.datetime.now()

bot.call_times: dict[int, datetime.datetime] = {}
bot.active_users: set[int] = set()
bot.db = load_db
bot.save_db = save_db

status_messages = [
    "Bot in Dev... 🚧",
    "Suporte",
    "Olhando os canais",
    "Monitorando o servidor",
    "Base de apoio Exilium."
]
status_cycle = cycle(status_messages)


def format_elapsed(delta: datetime.timedelta) -> str:
    seconds = int(delta.total_seconds())
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{secs:02}"


async def load_cogs() -> None:
    cogs_dir = BASE_DIR / "cogs"
    if not cogs_dir.exists():
        return

    for file in cogs_dir.glob("*.py"):
        await bot.load_extension(f"cogs.{file.stem}")


def ensure_user_record(user_id: int) -> tuple[dict, str]:
    uid = str(user_id)
    db = bot.db()
    if uid not in db:
        db[uid] = {"sobre": None, "tempo_total": 0}
        bot.save_db(db)
    return db, uid


@tasks.loop(seconds=10)
async def update_status():
    base_status = next(status_cycle)

    if bot.active_users:
        user_id = next(iter(bot.active_users))
        start = bot.call_times.get(user_id, datetime.datetime.now())
        tempo = format_elapsed(datetime.datetime.now() - start)
        await bot.change_presence(
            activity=discord.Game(name=f"{base_status} | {tempo} em call")
        )
        return

    await bot.change_presence(activity=discord.Game(name=base_status))


@bot.event
async def on_voice_state_update(member, before, after):
    joined_channel = after.channel and not before.channel
    left_channel = before.channel and not after.channel

    if joined_channel:
        bot.active_users.add(member.id)
        bot.call_times[member.id] = datetime.datetime.now()
        return

    if left_channel:
        bot.active_users.discard(member.id)
        start = bot.call_times.pop(member.id, None)
        if start is None:
            return

        delta = datetime.datetime.now() - start
        elapsed = int(delta.total_seconds())
        if elapsed <= 0:
            return

        db, uid = ensure_user_record(member.id)
        db[uid]["tempo_total"] = db[uid].get("tempo_total", 0) + elapsed
        bot.save_db(db)


@bot.event
async def setup_hook():
    await load_cogs()
    update_status.start()
    await bot.tree.sync()


@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user} (ID: {bot.user.id})")


bot.run(TOKEN)