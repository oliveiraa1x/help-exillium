
import discord
from discord import app_commands
from discord.ext import commands
import datetime

def format_time(seconds: int):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m {seconds}s"

class Perfil(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="perfil", description="Mostra um perfil bonito e completo do usuário.")
    async def perfil(self, interaction: discord.Interaction, membro: discord.Member = None):
        membro = membro or interaction.user
        db = self.bot.db()

        user_id = str(membro.id)

        # Criar conta no DB caso não exista
        if user_id not in db:
            db[user_id] = {
                "sobre": None,
                "tempo_total": 0
            }
            self.bot.save_db(db)

        # SOBRE MIM
        sobre = db[user_id].get("sobre") or "❌ Nenhum Sobre Mim definido ainda."

        # TEMPO TOTAL
        tempo_total = db[user_id].get("tempo_total", 0)
        tempo_total_fmt = format_time(tempo_total)

        # TEMPO ATUAL NA CALL
        if membro.id in self.bot.active_users:
            start = self.bot.call_times.get(membro.id, datetime.datetime.now())
            elapsed = datetime.datetime.now() - start
            tempo_atual = format_time(int(elapsed.total_seconds()))
        else:
            tempo_atual = "❌ Não está em call"

        # EMBED
        embed = discord.Embed(
            title=f"👤 Perfil de {membro.name}",
            color=discord.Color.red()
        )

        # Avatar
        avatar_url = getattr(membro, "avatar", None)
        embed.set_thumbnail(url=(membro.avatar.url if membro.avatar else membro.display_avatar.url))

        # Datas da conta
        embed.add_field(
            name="📅 Conta criada em:",
            value=membro.created_at.strftime("%d/%m/%Y"),
            inline=True
        )

        embed.add_field(
            name="📥 Entrou no servidor:",
            value=membro.joined_at.strftime("%d/%m/%Y") if membro.joined_at else "Desconhecido",
            inline=True
        )

        # SOBRE MIM
        embed.add_field(
            name="📝 Sobre Mim:",
            value=sobre,
            inline=False
        )

        # TEMPO EM CALL
        embed.add_field(
            name="🎧 Tempo atual em call:",
            value=tempo_atual,
            inline=True
        )

        embed.add_field(
            name="⏲️ Tempo total acumulado:",
            value=tempo_total_fmt,
            inline=True
        )

        # Banner
        try:
            user = await self.bot.fetch_user(membro.id)
            if user.banner:
                embed.set_image(url=user.banner.url)
        except:
            pass

        embed.set_footer(text="Aeternum Exilium • Sistema de Perfil")

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Perfil(bot))

