
import discord
from discord.ext import commands
from discord import app_commands

class Mensagem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="mensagem", description="Cria mensagens personalizadas.")
    async def mensagem(self, interaction: discord.Interaction, titulo: str, texto: str):
        embed = discord.Embed(
            title=titulo,
            description=texto,
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Mensagem(bot))
