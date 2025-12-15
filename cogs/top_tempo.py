
import discord
import json
from pathlib import Path
from discord.ext import commands
from discord import app_commands

# Importar funções de banco de dados do db.py centralizado
from db import load_top_tempo_db, save_top_tempo_db

def format_time(sec):
    h, r = divmod(sec, 3600)
    m, s = divmod(r, 60)
    return f"{h}h {m}m {s}s"


class TopTempo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_unload(self):
        self.bot.tree.remove_command(self.top_tempo.name, type=self.top_tempo.type)

    @app_commands.command(name="top-tempo", description="Mostra o ranking de tempo em call.")
    async def top_tempo(self, interaction: discord.Interaction):
        db = load_top_tempo_db()

        # Filtrar apenas membros reais (não bots)
        ranking_items = []
        for uid, data in db.items():
            try:
                user_id = int(uid)
                # Tenta buscar o membro no servidor
                member = interaction.guild.get_member(user_id) if interaction.guild else None
                if member:
                    # Se encontrou o membro, verifica se não é bot
                    if not member.bot:
                        ranking_items.append((uid, data.get("tempo_total", 0)))
                else:
                    # Se não encontrou no servidor, tenta buscar o usuário globalmente
                    user = await self.bot.fetch_user(user_id)
                    if not user.bot:
                        ranking_items.append((uid, data.get("tempo_total", 0)))
            except (ValueError, discord.NotFound, discord.HTTPException):
                # Se não conseguir buscar, pula este usuário
                continue

        ranking = sorted(
            ranking_items,
            key=lambda x: x[1],
            reverse=True
        )[:10]

        embed = discord.Embed(
            title="🏆 Top 10 — Tempo em Call",
            color=discord.Color.gold()
        )

        if not ranking:
            embed.description = "Ainda não há registros."
        else:
            for pos, (uid, sec) in enumerate(ranking, start=1):
                user = interaction.guild.get_member(int(uid)) if interaction.guild else None
                if not user:
                    try:
                        user = await self.bot.fetch_user(int(uid))
                    except:
                        nome = f"Usuário {uid}"
                    else:
                        nome = user.display_name if hasattr(user, 'display_name') else user.name
                else:
                    nome = user.display_name
                embed.add_field(name=f"{pos}. {nome}", value=format_time(sec), inline=False)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    cog = TopTempo(bot)
    await bot.add_cog(cog)
    bot.tree.add_command(cog.top_tempo)
