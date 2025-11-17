
import discord
from discord.ext import commands
from discord import app_commands
import datetime

class Uptime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="uptime", description="Mostra há quanto tempo o bot está online.")
    async def uptime(self, interaction: discord.Interaction):
        now = datetime.datetime.now()
        diff = now - self.bot.start_time
        h, r = divmod(int(diff.total_seconds()), 3600)
        m, s = divmod(r, 60)

        await interaction.response.send_message(f"⏳ Uptime: **{h}h {m}m {s}s**")

async def setup(bot):
    await bot.add_cog(Uptime(bot))
