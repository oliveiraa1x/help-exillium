
import discord
from discord.ext import commands
from discord import app_commands

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
        db = self.bot.db()

        ranking = sorted(
            [(uid, data.get("tempo_total", 0)) for uid, data in db.items()],
            key=lambda x: x[1],
            reverse=True
        )[:10]

        embed = discord.Embed(
            title="🏆 Top 10 — Tempo em Call",
            color=discord.Color.gold()
        )

        for pos, (uid, sec) in enumerate(ranking, start=1):
            user = interaction.guild.get_member(int(uid))
            nome = user.display_name if user else "Usuário desconhecido"
            embed.add_field(name=f"{pos}. {nome}", value=format_time(sec), inline=False)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    cog = TopTempo(bot)
    await bot.add_cog(cog)
    bot.tree.add_command(cog.top_tempo)
