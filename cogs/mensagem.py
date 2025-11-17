
import discord
from discord.ext import commands
from discord import app_commands

class Mensagem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_unload(self):
        self.bot.tree.remove_command(self.mensagem.name, type=self.mensagem.type)

    @app_commands.command(name="mensagem", description="Cria mensagens personalizadas.")
    async def mensagem(self, interaction: discord.Interaction, titulo: str, texto: str):
        embed = discord.Embed(
            title=titulo,
            description=texto,
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    cog = Mensagem(bot)
    await bot.add_cog(cog)
    bot.tree.add_command(cog.mensagem)
