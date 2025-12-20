
import discord
import json
from pathlib import Path
from discord.ext import commands
from discord import app_commands

# ==============================
# Funções de Banco de Dados
# ==============================
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
PERFIL_DB_PATH = DATA_DIR / "perfil.json"

def ensure_perfil_db_file() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not PERFIL_DB_PATH.exists():
        PERFIL_DB_PATH.write_text("{}", encoding="utf-8")

def load_perfil_db() -> dict:
    ensure_perfil_db_file()
    try:
        with PERFIL_DB_PATH.open("r", encoding="utf-8") as fp:
            return json.load(fp)
    except json.JSONDecodeError:
        return {}

def save_perfil_db(data: dict) -> None:
    ensure_perfil_db_file()
    with PERFIL_DB_PATH.open("w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)


class SetSobre(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_unload(self):
        self.bot.tree.remove_command(self.set_sobre.name, type=self.set_sobre.type)

    @app_commands.command(name="set-sobre", description="Define seu Sobre Mim.")
    async def set_sobre(self, interaction: discord.Interaction, texto: str):
        db = load_perfil_db()
        uid = str(interaction.user.id)

        if uid not in db:
            db[uid] = {
                "sobre": None,
                "tempo_total": 0,
                "casado_com": None
            }

        db[uid]["sobre"] = texto
        save_perfil_db(db)

        await interaction.response.send_message(f"✅ Sobre Mim atualizado!")

async def setup(bot):
    cog = SetSobre(bot)
    await bot.add_cog(cog)
    bot.tree.add_command(cog.set_sobre)
