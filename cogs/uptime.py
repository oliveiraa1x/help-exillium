
import discord
from discord.ext import commands
from discord import app_commands
import datetime

class Uptime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_unload(self):
        self.bot.tree.remove_command(self.uptime.name, type=self.uptime.type)

    @app_commands.command(name="uptime", description="Mostra há quanto tempo o bot está online.")
    async def uptime(self, interaction: discord.Interaction):
        now = datetime.datetime.now()
        diff = now - self.bot.start_time
        h, r = divmod(int(diff.total_seconds()), 3600)
        m, s = divmod(r, 60)
        tempo_formatado = f"{h}h {m}m {s}s"

        embed = discord.Embed(
            title="⏳ Uptime do Bot",
            description=f"**{self.bot.user.name}** está online!",
            color=discord.Color.green()
        )
        
        embed.set_thumbnail(url=(self.bot.user.avatar.url if self.bot.user.avatar else self.bot.user.display_avatar.url))
        
        embed.add_field(
            name="🕐 Tempo online:",
            value=f"**{tempo_formatado}**",
            inline=False
        )
        
        embed.add_field(
            name="📅 Iniciado em:",
            value=f"<t:{int(self.bot.start_time.timestamp())}:F>",
            inline=False
        )
        
        embed.set_footer(text="Aeternum Exilium • Sistema de Uptime")
        embed.timestamp = datetime.datetime.now()

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    cog = Uptime(bot)
    await bot.add_cog(cog)
    bot.tree.add_command(cog.uptime)
