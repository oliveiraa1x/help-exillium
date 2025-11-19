import datetime
import importlib
import json
import os
from itertools import cycle
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands, tasks


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
bot = commands.Bot(command_prefix=".", intents=intents)
bot.start_time = datetime.datetime.now()

bot.call_times: dict[int, datetime.datetime] = {}
bot.active_users: set[int] = set()
bot.db = load_db
bot.save_db = save_db

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
    uid = str(user_id)
    db = bot.db()
    if uid not in db:
        db[uid] = {"sobre": None, "tempo_total": 0}
        bot.save_db(db)
    return db, uid


@bot.tree.command(name="help", description="Lista os comandos disponíveis do Help Exilium.")
async def slash_help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📖 Help Exilium",
        description="Comandos disponíveis:",
        color=discord.Color.blurple(),
    )
    embed.add_field(name="/perfil [membro]", value="Mostra os detalhes do perfil.", inline=False)
    embed.add_field(name="/mensagem <título> <texto>", value="Cria uma embed simples.", inline=False)
    embed.add_field(name="/set-sobre <texto>", value="Define seu 'Sobre Mim'.", inline=False)
    embed.add_field(name="/top-tempo", value="Exibe o ranking de tempo em call.", inline=False)
    embed.add_field(name="/callstatus", value="Mostra seu tempo atual em call.", inline=False)
    embed.add_field(name="/uptime", value="Mostra há quanto tempo o bot está online.", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="perfil", description="Mostra um perfil completo do usuário.")
@app_commands.describe(membro="Membro que terá o perfil exibido")
async def slash_perfil(interaction: discord.Interaction, membro: discord.Member | None = None):
    membro = membro or interaction.user
    db, uid = ensure_user_record(membro.id)

    sobre = db[uid].get("sobre") or "❌ Nenhum Sobre Mim definido ainda."
    tempo_total = db[uid].get("tempo_total", 0)
    tempo_total_fmt = format_time(tempo_total)

    if membro.id in bot.active_users:
        start = bot.call_times.get(membro.id, datetime.datetime.now())
        elapsed = datetime.datetime.now() - start
        tempo_atual = format_time(int(elapsed.total_seconds()))
    else:
        tempo_atual = "❌ Não está em call"

    embed = discord.Embed(
        title=f"👤 Perfil de {membro.display_name}",
        color=discord.Color.red(),
    )
    embed.set_thumbnail(url=(membro.avatar.url if membro.avatar else membro.display_avatar.url))
    embed.add_field(name="📅 Conta criada em:", value=membro.created_at.strftime("%d/%m/%Y"), inline=True)
    joined_at = membro.joined_at.strftime("%d/%m/%Y") if membro.joined_at else "Desconhecido"
    embed.add_field(name="📥 Entrou no servidor:", value=joined_at, inline=True)
    embed.add_field(name="📝 Sobre Mim:", value=sobre, inline=False)
    embed.add_field(name="🎧 Tempo atual em call:", value=tempo_atual, inline=True)
    embed.add_field(name="⏲️ Tempo total acumulado:", value=tempo_total_fmt, inline=True)

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
    embed = discord.Embed(title=titulo, description=texto, color=discord.Color.blurple())
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="set-sobre", description="Define o seu 'Sobre Mim'.")
@app_commands.describe(texto="Conteúdo do seu Sobre Mim")
async def slash_set_sobre(interaction: discord.Interaction, texto: str):
    db, uid = ensure_user_record(interaction.user.id)
    db[uid]["sobre"] = texto
    bot.save_db(db)
    await interaction.response.send_message("✅ Sobre Mim atualizado!")


@bot.tree.command(name="top-tempo", description="Mostra o ranking de tempo em call.")
async def slash_top_tempo(interaction: discord.Interaction):
    db = bot.db()
    
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


@tasks.loop(seconds=10)
async def update_status():
    if not bot.is_ready():
        return
    base_status = next(status_cycle)

    if bot.active_users:
        user_id = next(iter(bot.active_users))
        start = bot.call_times.get(user_id, datetime.datetime.now())
        tempo = format_elapsed(datetime.datetime.now() - start)
        await bot.change_presence(
            activity=discord.Game(name=f"{base_status} | {tempo} em call")
        )
        return

    await bot.change_presence(activity=discord.Game(name=base_status))


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

        db, uid = ensure_user_record(member.id)
        db[uid]["tempo_total"] = db[uid].get("tempo_total", 0) + elapsed
        bot.save_db(db)


@bot.event
async def setup_hook():
    update_status.start()
    await bot.tree.sync()


@update_status.before_loop
async def before_update_status():
    await bot.wait_until_ready()


@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user} (ID: {bot.user.id})")


bot.run(TOKEN)