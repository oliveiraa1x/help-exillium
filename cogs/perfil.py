
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

    def cog_unload(self):
        self.bot.tree.remove_command(self.perfil.name, type=self.perfil.type)

    async def get_user_rank(self, db: dict, user_id: str, category: str, interaction: discord.Interaction):
        """Calcula o ranking do usuário em uma categoria específica"""
        ranking_items = []
        checked_users = {}  # Cache de usuários já verificados
        
        for uid, data in db.items():
            try:
                uid_int = int(uid)
                is_bot = None
                
                # Verificar cache primeiro
                if uid in checked_users:
                    is_bot = checked_users[uid]
                else:
                    member = interaction.guild.get_member(uid_int) if interaction.guild else None
                    if member:
                        is_bot = member.bot
                        checked_users[uid] = is_bot
                    else:
                        try:
                            user = await self.bot.fetch_user(uid_int)
                            is_bot = user.bot
                            checked_users[uid] = is_bot
                        except:
                            checked_users[uid] = True  # Marcar como bot se não conseguir buscar
                            continue
                
                if not is_bot:
                    if category == "call":
                        value = data.get("tempo_total", 0)
                    elif category == "souls":
                        value = data.get("soul", 0)
                    elif category == "xp":
                        value = data.get("xp", 0)
                    else:
                        continue
                    ranking_items.append((uid, value))
            except (ValueError, discord.NotFound, discord.HTTPException):
                continue
        
        # Ordenar por valor (maior primeiro)
        ranking_items.sort(key=lambda x: x[1], reverse=True)
        
        # Encontrar posição do usuário
        for pos, (uid, _) in enumerate(ranking_items, start=1):
            if uid == user_id:
                return pos
        
        return None

    @app_commands.command(name="perfil", description="Mostra um perfil bonito e completo do usuário.")
    async def perfil(self, interaction: discord.Interaction, membro: discord.Member = None):
        membro = membro or interaction.user
        db = self.bot.db()

        user_id = str(membro.id)

        # Criar conta no DB caso não exista
        if user_id not in db:
            db[user_id] = {
                "sobre": None,
                "tempo_total": 0,
                "soul": 0,
                "xp": 0,
                "level": 1
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

        # ECONOMIA
        souls = db[user_id].get("soul", 0)
        xp = db[user_id].get("xp", 0)
        level = db[user_id].get("level", 1)

        # Calcular rankings
        rank_call = await self.get_user_rank(db, user_id, "call", interaction)
        rank_souls = await self.get_user_rank(db, user_id, "souls", interaction)
        rank_xp = await self.get_user_rank(db, user_id, "xp", interaction)

        # EMBED
        embed = discord.Embed(
            title=f"👤 Perfil de {membro.display_name}",
            color=discord.Color.red()
        )

        # Avatar
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

        embed.add_field(
            name="\u200b",
            value="\u200b",
            inline=True
        )

        # SOBRE MIM
        embed.add_field(
            name="📝 Sobre Mim:",
            value=sobre,
            inline=False
        )

        # TEMPO EM CALL
        rank_call_text = f"🏆 **#{rank_call}**" if rank_call else "❌ Sem ranking"
        embed.add_field(
            name="🎧 Tempo em Call",
            value=f"**Atual:** {tempo_atual}\n**Total:** {tempo_total_fmt}\n**Rank:** {rank_call_text}",
            inline=True
        )

        # ECONOMIA - Souls com ranking
        rank_souls_text = f"🏆 **#{rank_souls}**" if rank_souls else "❌ Sem ranking"
        embed.add_field(
            name="💎 Souls",
            value=f"**{souls:,}** 💎\n**Rank:** {rank_souls_text}",
            inline=True
        )

        # XP e Level com ranking
        rank_xp_text = f"🏆 **#{rank_xp}**" if rank_xp else "❌ Sem ranking"
        embed.add_field(
            name="⭐ Nível & XP",
            value=f"**Nível {level}**\n**{xp:,}** XP\n**Rank XP:** {rank_xp_text}",
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
    cog = Perfil(bot)
    await bot.add_cog(cog)
    bot.tree.add_command(cog.perfil)

