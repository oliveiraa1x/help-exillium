import discord
from discord import app_commands
from discord.ext import commands, tasks

import datetime
import importlib
import json
import os
import random
import asyncio

from itertools import cycle
from pathlib import Path

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

def _resolve_load_dotenv():
    try:
        return importlib.import_module("dotenv").load_dotenv
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Dependência ausente: python-dotenv. "
            "Instale-a conforme descrito no requirements.txt."
        ) from exc


load_dotenv = _resolve_load_dotenv()


# ==============================
# Configurações básicas
# ==============================
BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data" / "db.json"
PERFIL_DB_PATH = BASE_DIR / "data" / "perfil.json"
TOP_TEMPO_DB_PATH = BASE_DIR / "data" / "top_tempo.json"
CONFIG_PATH = BASE_DIR / "config.json"


def ensure_data_file() -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_PATH.exists():
        DATA_PATH.write_text("{}", encoding="utf-8")


def load_db() -> dict:
    ensure_data_file()
    with DATA_PATH.open("r", encoding="utf-8") as fp:
        try:
            return json.load(fp)
        except json.JSONDecodeError:
            # Corrige arquivos corrompidos
            return {}


def save_db(data: dict) -> None:
    ensure_data_file()
    with DATA_PATH.open("w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)


# ==============================
# Sistema de Banco de Dados para Perfil
# ==============================
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
        return {}


def save_perfil_db(data: dict) -> None:
    """Salva o banco de dados de perfil"""
    ensure_perfil_db_file()
    with PERFIL_DB_PATH.open("w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)


# ==============================
# Sistema de Banco de Dados para Top Tempo
# ==============================
def ensure_top_tempo_db_file() -> None:
    """Garante que o arquivo de banco de dados de top tempo existe"""
    TOP_TEMPO_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not TOP_TEMPO_DB_PATH.exists():
        TOP_TEMPO_DB_PATH.write_text("{}", encoding="utf-8")


def load_top_tempo_db() -> dict:
    """Carrega o banco de dados de top tempo"""
    ensure_top_tempo_db_file()
    try:
        with TOP_TEMPO_DB_PATH.open("r", encoding="utf-8") as fp:
            return json.load(fp)
    except json.JSONDecodeError:
        return {}


def save_top_tempo_db(data: dict) -> None:
    """Salva o banco de dados de top tempo"""
    ensure_top_tempo_db_file()
    with TOP_TEMPO_DB_PATH.open("w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)


def resolve_token() -> str:
    load_dotenv()
    token = os.getenv("TOKEN")

    if token:
        return token

    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("r", encoding="utf-8") as fp:
            try:
                cfg = json.load(fp)
            except json.JSONDecodeError:
                cfg = {}
        token = cfg.get("TOKEN")

    if not token:
        raise RuntimeError(
            "TOKEN não encontrado. Configure a variável de ambiente ou o arquivo config.json."
        )

    return token

TOKEN = resolve_token()

# ==============================
# Cria o BOT e variáveis globais
# ==============================
intents = discord.Intents.all()
# Usar o prefixo do servidor conforme pedido: "sprt!"
bot = commands.Bot(command_prefix="sprt!", intents=intents)
bot.start_time = datetime.datetime.now()

# Remove default help command so custom `sprt!help` can be registered without collision
try:
    bot.remove_command('help')
except Exception:
    pass

# Track last presence to avoid unnecessary change_presence calls
# bot._last_presence: str | None = None
# bot.call_times: dict[int, datetime.datetime] = {}
# bot.active_users: set[int] = set()
# bot.db = load_db
# bot.save_db = save_db
# Inicializar estruturas de dados em memória e ligar às funções de persistência
bot._last_presence = None
bot.call_times = {}
bot.active_users = set()
bot.db = load_db
bot.save_db = save_db
bot.load_top_tempo_db = load_top_tempo_db
bot.save_top_tempo_db = save_top_tempo_db

status_messages = [
    "Bot in Dev... 🚧",
    "Suporte",
    "Olhando os canais",
    "Monitorando o servidor",
    "Base de apoio Exilium."
]
status_cycle = cycle(status_messages)


def format_elapsed(delta: datetime.timedelta) -> str:
    seconds = int(delta.total_seconds())
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{secs:02}"


def format_time(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}h {minutes}m {secs}s"


def ensure_user_record(user_id: int) -> tuple[dict, str]:
    """Garante que o usuário existe no banco de dados principal"""
    uid = str(user_id)
    db = bot.db()
    if uid not in db:
        db[uid] = {}
        bot.save_db(db)
    return db, uid


def ensure_perfil_record(user_id: int) -> tuple[dict, str]:
    """Garante que o usuário existe no banco de dados de perfil"""
    uid = str(user_id)
    db = load_perfil_db()
    if uid not in db:
        db[uid] = {
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
            if key not in db[uid]:
                db[uid][key] = value
        save_perfil_db(db)
    return db, uid


def ensure_top_tempo_record(user_id: int) -> tuple[dict, str]:
    """Garante que o usuário existe no banco de dados de top tempo"""
    uid = str(user_id)
    db = load_top_tempo_db()
    if uid not in db:
        db[uid] = {
            "tempo_total": 0
        }
        save_top_tempo_db(db)
    else:
        # Garantir que campos novos existam para usuários antigos
        if "tempo_total" not in db[uid]:
            db[uid]["tempo_total"] = 0
            save_top_tempo_db(db)
    return db, uid


@bot.tree.command(name="help", description="Lista os comandos disponíveis do Help Exilium.")
async def slash_help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📖 Help Exilium",
        description="Comandos disponíveis:",
        color=discord.Color.blurple(),
    )
    embed.add_field(name="👤 Perfil", value="/perfil [membro] - Mostra os detalhes do perfil", inline=False)
    embed.add_field(name="💬 Mensagens", value="/mensagem <título> <texto> - Cria uma embed simples", inline=False)
    embed.add_field(name="📝 Sobre Mim", value="/set-sobre <texto> - Define seu 'Sobre Mim'", inline=False)
    embed.add_field(name="🎧 Call", value="/top-tempo - Ranking de tempo em call\n/callstatus - Seu tempo atual em call", inline=False)
    embed.add_field(name="💰 Economia", value="/daily - Recompensa diária\n/mine - Minerar e ganhar almas\n/caça - Caça rápida (5s)\n/caça-longa - Caça longa (12h)\n/balance [membro] - Ver saldo de almas\n/top-souls - Ranking de almas\n/top-level - Ranking de níveis", inline=False)
    embed.add_field(name="⚔️ RPG Combate", value="/combate - Inicie um combate contra um mob aleatório!", inline=False)
    embed.add_field(name="📋 Missões", value="/missoes - Ver suas missões\n/claim-missao <número> - Reivindicar recompensa", inline=False)
    embed.add_field(name="ℹ️ Info", value="/uptime - Tempo online do bot", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


async def get_user_rank_call(user_id: str, interaction: discord.Interaction):
    """Calcula o ranking do usuário em tempo de call"""
    db = load_top_tempo_db()
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
                        user = await bot.fetch_user(uid_int)
                        is_bot = user.bot
                        checked_users[uid] = is_bot
                    except:
                        checked_users[uid] = True  # Marcar como bot se não conseguir buscar
                        continue
            
            if not is_bot:
                value = data.get("tempo_total", 0)
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


@bot.tree.command(name="perfil", description="Mostra um perfil completo do usuário.")
@app_commands.describe(membro="Membro que terá o perfil exibido")
async def slash_perfil(interaction: discord.Interaction, membro: discord.Member | None = None):
    membro = membro or interaction.user
    db, uid = ensure_perfil_record(membro.id)

    sobre = db[uid].get("sobre") or "❌ Nenhum Sobre Mim definido ainda."
    # Ler tempo_total do banco de top_tempo
    top_tempo_db = load_top_tempo_db()
    tempo_total = top_tempo_db.get(uid, {}).get("tempo_total", 0)
    tempo_total_fmt = format_time(tempo_total)

    if membro.id in bot.active_users:
        start = bot.call_times.get(membro.id, datetime.datetime.now())
        elapsed = datetime.datetime.now() - start
        tempo_atual = format_time(int(elapsed.total_seconds()))
    else:
        tempo_atual = "❌ Não está em call"

    # Calcular ranking
    rank_call = await get_user_rank_call(uid, interaction)

    embed = discord.Embed(
        title=f"👤 Perfil de {membro.display_name}",
        color=discord.Color.red(),
    )
    embed.set_thumbnail(url=(membro.avatar.url if membro.avatar else membro.display_avatar.url))
    
    # Datas da conta e casamento
    embed.add_field(
        name="📅 Conta criada em:",
        value=membro.created_at.strftime("%d/%m/%Y"),
        inline=True
    )

    # CASAMENTO
    casado_com_id = db[uid].get("casado_com")
    if casado_com_id:
        try:
            casado_com_user = await bot.fetch_user(int(casado_com_id))
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

    embed.add_field(name="📝 Sobre Mim:", value=sobre, inline=False)
    
    # TEMPO EM CALL
    rank_call_text = f"🏆 **#{rank_call}**" if rank_call else "❌ Sem ranking"
    embed.add_field(
        name="🎧 Tempo em Call",
        value=f"**Atual:** {tempo_atual}\n**Total:** {tempo_total_fmt}\n**Rank:** {rank_call_text}",
        inline=False
    )

    try:
        user = await bot.fetch_user(membro.id)
        if user.banner:
            embed.set_image(url=user.banner.url)
    except discord.HTTPException:
        pass

    embed.set_footer(text="Aeternum Exilium • Sistema de Perfil")
    await interaction.response.send_message(embed=embed)




@bot.tree.command(name="mensagem", description="Cria mensagens personalizadas.")
@app_commands.describe(titulo="Título da embed", texto="Texto principal da embed")
async def slash_mensagem(interaction: discord.Interaction, titulo: str, texto: str):

    # Deferir para ocultar totalmente o uso do comando
    await interaction.response.defer(ephemeral=True)

    embed = discord.Embed(
        title=titulo,
        description=texto,
        color=discord.Color.blurple(),
    )

    # Envia a embed no canal sem mostrar que veio do comando
    await interaction.channel.send(embed=embed)

    # NÃO enviar followup para permanecer invisível



@bot.tree.command(name="set-sobre", description="Define o seu 'Sobre Mim'.")
@app_commands.describe(texto="Conteúdo do seu Sobre Mim")
async def slash_set_sobre(interaction: discord.Interaction, texto: str):
    db, uid = ensure_perfil_record(interaction.user.id)
    db[uid]["sobre"] = texto
    save_perfil_db(db)
    await interaction.response.send_message("✅ Sobre Mim atualizado!")


@bot.tree.command(name="top-tempo", description="Mostra o ranking de tempo em call.")
async def slash_top_tempo(interaction: discord.Interaction):
    db = load_top_tempo_db()
    
    # Filtrar apenas membros reais (não bots)
    ranking_items = []
    for uid, data in db.items():
        try:
            user_id = int(uid)
            # Tenta buscar o membro no servidor
            member = interaction.guild.get_member(user_id) if interaction.guild else None
            if member:
                # Se encontrou o membro, verifica se não é bot
                if not member.bot:
                    ranking_items.append((uid, data.get("tempo_total", 0)))
            else:
                # Se não encontrou no servidor, tenta buscar o usuário globalmente
                user = await bot.fetch_user(user_id)
                if not user.bot:
                    ranking_items.append((uid, data.get("tempo_total", 0)))
        except (ValueError, discord.NotFound, discord.HTTPException):
            # Se não conseguir buscar, pula este usuário
            continue

    ranking = sorted(
        ranking_items,
        key=lambda item: item[1],
        reverse=True,
    )[:10]

    embed = discord.Embed(title="🏆 Top 10 — Tempo em Call", color=discord.Color.gold())
    if not ranking:
        embed.description = "Ainda não há registros."
    else:
        for pos, (uid, seconds) in enumerate(ranking, start=1):
            member = interaction.guild.get_member(int(uid)) if interaction.guild else None
            if member:
                nome = member.display_name
            else:
                try:
                    user = await bot.fetch_user(int(uid))
                    nome = user.name
                except:
                    nome = f"Usuário {uid}"
            embed.add_field(name=f"{pos}. {nome}", value=format_time(seconds), inline=False)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="callstatus", description="Mostra seu tempo atual na call.")
async def slash_callstatus(interaction: discord.Interaction):
    user = interaction.user
    if user.id not in bot.active_users:
        embed = discord.Embed(
            title="❌ Não está em call",
            description="Você precisa estar em uma call de voz para usar este comando.",
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=(user.avatar.url if user.avatar else user.display_avatar.url))
        embed.set_footer(text="Aeternum Exilium • Sistema de Call Status")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    start = bot.call_times.get(user.id, datetime.datetime.now())
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


@bot.tree.command(name="uptime", description="Mostra há quanto tempo o bot está online.")
async def slash_uptime(interaction: discord.Interaction):
    diff = datetime.datetime.now() - bot.start_time
    hours, remainder = divmod(int(diff.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    tempo_formatado = f"{hours}h {minutes}m {seconds}s"

    embed = discord.Embed(
        title="⏳ Uptime do Bot",
        description=f"**{bot.user.name}** está online!",
        color=discord.Color.green()
    )
    
    embed.set_thumbnail(url=(bot.user.avatar.url if bot.user.avatar else bot.user.display_avatar.url))
    
    embed.add_field(
        name="🕐 Tempo online:",
        value=f"**{tempo_formatado}**",
        inline=False
    )
    
    embed.add_field(
        name="📅 Iniciado em:",
        value=f"<t:{int(bot.start_time.timestamp())}:F>",
        inline=False
    )
    
    embed.set_footer(text="Aeternum Exilium • Sistema de Uptime")
    embed.timestamp = datetime.datetime.now()

    await interaction.response.send_message(embed=embed)


@tasks.loop(seconds=60)
async def update_status():
    if not bot.is_ready():
        return
    base_status = next(status_cycle)

    if bot.active_users:
        user_id = next(iter(bot.active_users))
        start = bot.call_times.get(user_id, datetime.datetime.now())
        tempo = format_elapsed(datetime.datetime.now() - start)
        desired = f"{base_status} | {tempo} em call"
        if getattr(bot, '_last_presence', None) != desired:
            try:
                await bot.change_presence(activity=discord.Game(name=desired))
                bot._last_presence = desired
            except Exception:
                # Ignore errors (rate limits will be handled by Discord library)
                pass
        return

    desired = base_status
    if getattr(bot, '_last_presence', None) != desired:
        try:
            await bot.change_presence(activity=discord.Game(name=base_status))
            bot._last_presence = desired
        except Exception:
            pass


@bot.event
async def on_message(message):
    # Ignorar mensagens de bots
    if message.author.bot:
        return
    
    # Não ignorar mensagens que começam com o prefixo — deixamos o processamento
    # de comandos para `bot.process_commands(message)` abaixo.
    
    # Ganhar XP por mensagem
    db, uid = ensure_user_record(message.author.id)
    
    # Cooldown de XP por mensagem (30 segundos)
    last_message_xp = db[uid].get("last_message_xp")
    now = datetime.datetime.now()
    
    if not last_message_xp or (now - datetime.datetime.fromisoformat(last_message_xp)).total_seconds() >= 30:
        # Ganhar XP aleatória (1-5 XP)
        xp_gain = random.randint(1, 5)
        
        # Calcular nível antigo
        old_xp = db[uid].get("xp", 0)
        old_level = calculate_level_from_xp(old_xp)
        
        # Adicionar XP
        db[uid]["xp"] = old_xp + xp_gain
        db[uid]["last_message_xp"] = now.isoformat()
        
        # Calcular novo nível
        new_level = calculate_level_from_xp(db[uid]["xp"])
        db[uid]["level"] = new_level
        
        # Atualizar progresso de missões
        update_missao_progresso(db, uid, "mensagens", 1)
        
        bot.save_db(db)
    
    await bot.process_commands(message)


def calculate_level_from_xp(xp: int) -> int:
    """Calcula o nível baseado na XP"""
    level = 1
    required_xp = 100
    current_xp = xp
    
    while current_xp >= required_xp:
        current_xp -= required_xp
        level += 1
        required_xp = int(required_xp * 1.5)
    
    return level


def update_missao_progresso(db: dict, uid: str, tipo: str, quantidade: int = 1):
    """Atualiza o progresso de missões"""
    missoes = db[uid].get("missoes", [])
    for missao in missoes:
        if missao.get("tipo") == tipo:
            missao["progresso"] = missao.get("progresso", 0) + quantidade


@bot.event
async def on_voice_state_update(member, before, after):
    joined_channel = after.channel and not before.channel
    left_channel = before.channel and not after.channel

    if joined_channel:
        bot.active_users.add(member.id)
        bot.call_times[member.id] = datetime.datetime.now()
        return

    if left_channel:
        bot.active_users.discard(member.id)
        start = bot.call_times.pop(member.id, None)
        if start is None:
            return

        delta = datetime.datetime.now() - start
        elapsed = int(delta.total_seconds())
        if elapsed <= 0:
            return

        db, uid = ensure_top_tempo_record(member.id)
        db[uid]["tempo_total"] = db[uid].get("tempo_total", 0) + elapsed
        save_top_tempo_db(db)
        
        # Atualizar progresso de missão de call (no banco de economia)
        from cogs.economia import load_economia_db, save_economia_db
        economia_db = load_economia_db()
        # Garantir que o usuário exista no banco de economia antes de atualizar missões
        if uid not in economia_db:
            economia_db[uid] = {
                "soul": 0,
                "xp": 0,
                "level": 1,
                "last_daily": None,
                "last_mine": None,
                "mine_streak": 0,
                "daily_streak": 0,
                "last_caca": None,
                "caca_streak": 0,
                "caca_longa_ativa": None,
                "missoes": [],
                "missoes_completas": []
            }

        update_missao_progresso(economia_db, uid, "call", elapsed)
        save_economia_db(economia_db)


@bot.event
async def setup_hook():
    import importlib

    # Carregar cog economia
    try:
        economia = importlib.import_module("cogs.economia")
        await economia.setup(bot)
    except Exception as e:
        print(f"Erro ao carregar cog economia: {e}")

    # Carregar mod
    try:
        mod = importlib.import_module("cogs.mod")
        await mod.setup(bot)
    except Exception as e:
        print(f"Erro ao carregar cog mod: {e}")

    # ==============================
    # NOVO: carregar painel.py
    # ==============================
    try:
        painel = importlib.import_module("cogs.painel")
        await painel.setup(bot)
        print("Painel carregado com sucesso!")
    except Exception as e:
        print(f"Erro ao carregar cog painel: {e}")

    # Carregar casamento
    try:
        casamento = importlib.import_module("cogs.casamento")
        await casamento.setup(bot)
        print("Casamento carregado com sucesso!")
    except Exception as e:
        print(f"Erro ao carregar cog casamento: {e}")

    # Carregar frase
    try:
        frase = importlib.import_module("cogs.frase")
        await frase.setup(bot)
        print("Frase carregado com sucesso!")
    except Exception as e:
        print(f"Erro ao carregar cog frase: {e}")

    # Carregar RPG Combate
    try:
        rpg_combate = importlib.import_module("cogs.rpg_combate")
        await rpg_combate.setup(bot)
        print("RPG Combate carregado com sucesso!")
    except Exception as e:
        print(f"Erro ao carregar cog RPG Combate: {e}")

    update_status.start()
    await bot.tree.sync()

async def main():
    await bot.load_extension("voice_timer")
    await bot.start("SEU_TOKEN_AQUI")

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user} (ID: {bot.user.id})")

bot.run(TOKEN)