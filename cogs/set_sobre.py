
import discord
import json
from pathlib import Path
from discord.ext import commands
from discord import app_commands

# Importar funções de banco de dados do db.py centralizado
from db import load_perfil_db, save_perfil_db


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
