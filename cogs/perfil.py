
import discord
import json
import datetime
from pathlib import Path
from discord import app_commands
from discord.ext import commands

def format_time(seconds: int):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m {seconds}s"


# ==============================
# Sistema de Banco de Dados para Perfil e Tempo
# ==============================
PERFIL_DB_PATH = Path(__file__).parent.parent / "data" / "perfil.json"


def ensure_perfil_db_file() -> None:
    """Garante que o arquivo de banco de dados de perfil existe"""
    PERFIL_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not PERFIL_DB_PATH.exists():
        PERFIL_DB_PATH.write_text("{}", encoding="utf-8")


def load_perfil_db() -> dict:
    """Carrega o banco de dados de perfil"""
    ensure_perfil_db_file()
    try:
        with PERFIL_DB_PATH.open("r", encoding="utf-8") as fp:
            return json.load(fp)
    except json.JSONDecodeError:
        # Se o arquivo estiver corrompido, retorna um dicionário vazio
        return {}


def save_perfil_db(data: dict) -> None:
    """Salva o banco de dados de perfil"""
    ensure_perfil_db_file()
    with PERFIL_DB_PATH.open("w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)


class Perfil(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_unload(self):
        self.bot.tree.remove_command(self.perfil.name, type=self.perfil.type)

    async def get_user_rank(self, user_id: str, category: str, interaction: discord.Interaction):
        """Calcula o ranking do usuário em uma categoria específica"""
        if category == "call":
            # Importar funções do top_tempo para ler o banco de dados correto
            from cogs.top_tempo import load_top_tempo_db
            db = load_top_tempo_db()
        else:
            return None
        
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
                        ranking_items.append((uid, value))
                    else:
                        continue
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
        db = load_perfil_db()

        user_id = str(membro.id)

        # Criar conta no DB caso não exista
        if user_id not in db:
            db[user_id] = {
                "sobre": None,
                "casado_com": None
            }
            save_perfil_db(db)
        else:
            # Garantir que campos novos existam para usuários antigos
            defaults = {
                "sobre": None,
                "casado_com": None
            }
            for key, value in defaults.items():
                if key not in db[user_id]:
                    db[user_id][key] = value
            save_perfil_db(db)

        # SOBRE MIM
        sobre = db[user_id].get("sobre") or "❌ Nenhum Sobre Mim definido ainda."

        # TEMPO TOTAL (ler do banco de top_tempo)
        from cogs.top_tempo import load_top_tempo_db
        top_tempo_db = load_top_tempo_db()
        tempo_total = top_tempo_db.get(user_id, {}).get("tempo_total", 0)
        tempo_total_fmt = format_time(tempo_total)

        # TEMPO ATUAL NA CALL
        if membro.id in self.bot.active_users:
            start = self.bot.call_times.get(membro.id, datetime.datetime.now())
            elapsed = datetime.datetime.now() - start
            tempo_atual = format_time(int(elapsed.total_seconds()))
        else:
            tempo_atual = "❌ Não está em call"

        # Calcular ranking
        rank_call = await self.get_user_rank(user_id, "call", interaction)

        # EMBED
        embed = discord.Embed(
            title=f"👤 Perfil de {membro.display_name}",
            color=discord.Color.red()
        )

        # Avatar
        embed.set_thumbnail(url=(membro.avatar.url if membro.avatar else membro.display_avatar.url))

        # Datas da conta e casamento
        embed.add_field(
            name="📅 Conta criada em:",
            value=membro.created_at.strftime("%d/%m/%Y"),
            inline=True
        )

        # CASAMENTO
        casado_com_id = db[user_id].get("casado_com")
        if casado_com_id:
            try:
                casado_com_user = await self.bot.fetch_user(int(casado_com_id))
                embed.add_field(
                    name="💍 Casado(a) com:",
                    value=casado_com_user.mention,
                    inline=True
                )
            except:
                embed.add_field(
                    name="💍 Casado(a) com:",
                    value="Usuário não encontrado",
                    inline=True
                )
        else:
            embed.add_field(
                name="💍 Casado(a) com:",
                value="Solteiro(a)",
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
            inline=False
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

