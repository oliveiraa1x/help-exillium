
import discord
from discord.ext import commands
from discord import app_commands

class SetSobre(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_unload(self):
        self.bot.tree.remove_command(self.set_sobre.name, type=self.set_sobre.type)

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
    cog = SetSobre(bot)
    await bot.add_cog(cog)
    bot.tree.add_command(cog.set_sobre)
