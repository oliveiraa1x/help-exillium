
import discord
from discord.ext import commands
from discord import app_commands
import datetime

def format_time(sec):
    h, r = divmod(sec, 3600)
    m, s = divmod(r, 60)
    return f"{h}h {m}m {s}s"

class CallStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_unload(self):
        self.bot.tree.remove_command(self.callstatus.name, type=self.callstatus.type)

    @app_commands.command(name="callstatus", description="Mostra seu tempo atual na call.")
    async def callstatus(self, interaction: discord.Interaction):
        user = interaction.user

        if user.id not in self.bot.active_users:
            return await interaction.response.send_message("❌ Você não está em call.")

        start = self.bot.call_times.get(user.id, datetime.datetime.now())
        elapsed = int((datetime.datetime.now() - start).total_seconds())

        await interaction.response.send_message(
            f"🎧 Você está há **{format_time(elapsed)}** na call."
        )

async def setup(bot):
    cog = CallStatus(bot)
    await bot.add_cog(cog)
    bot.tree.add_command(cog.callstatus)
