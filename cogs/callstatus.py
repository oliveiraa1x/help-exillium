
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
            embed = discord.Embed(
                title="❌ Não está em call",
                description="Você precisa estar em uma call de voz para usar este comando.",
                color=discord.Color.red()
            )
            embed.set_thumbnail(url=(user.avatar.url if user.avatar else user.display_avatar.url))
            embed.set_footer(text="Aeternum Exilium • Sistema de Call Status")
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        start = self.bot.call_times.get(user.id, datetime.datetime.now())
        elapsed = int((datetime.datetime.now() - start).total_seconds())
        tempo_formatado = format_time(elapsed)

        embed = discord.Embed(
            title="🎧 Status da Call",
            description=f"**{user.mention}** está em call!",
            color=discord.Color.blue()
        )
        
        embed.set_thumbnail(url=(user.avatar.url if user.avatar else user.display_avatar.url))
        
        embed.add_field(
            name="⏱️ Tempo na call:",
            value=f"**{tempo_formatado}**",
            inline=False
        )
        
        embed.set_footer(text="Aeternum Exilium • Sistema de Call Status")
        embed.timestamp = datetime.datetime.now()

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    cog = CallStatus(bot)
    await bot.add_cog(cog)
    bot.tree.add_command(cog.callstatus)
