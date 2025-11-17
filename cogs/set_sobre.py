
import discord
from discord.ext import commands
from discord import app_commands

class SetSobre(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="set-sobre", description="Define seu Sobre Mim.")
    async def set_sobre(self, interaction: discord.Interaction, texto: str):
        db = self.bot.db()
        uid = str(interaction.user.id)

        if uid not in db:
            db[uid] = {"sobre": None, "tempo_total": 0}

        db[uid]["sobre"] = texto
        self.bot.save_db(db)

        await interaction.response.send_message(f"✅ Sobre Mim atualizado!")

async def setup(bot):
    await bot.add_cog(SetSobre(bot))
