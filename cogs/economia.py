import discord
import random
import datetime
import asyncio
from discord import app_commands
from discord.ext import commands, tasks


def calculate_level(xp: int) -> int:
    """Calcula o nível baseado na XP"""
    level = 1
    required_xp = 100
    current_xp = xp
    
    while current_xp >= required_xp:
        current_xp -= required_xp
        level += 1
        required_xp = int(required_xp * 1.5)  # Aumenta 50% a cada nível
    
    return level


def get_xp_for_level(level: int) -> int:
    """Retorna a XP total necessária para alcançar um nível"""
    total_xp = 0
    required_xp = 100
    
    for _ in range(1, level):
        total_xp += required_xp
        required_xp = int(required_xp * 1.5)
    
    return total_xp


def get_xp_for_next_level(level: int) -> int:
    """Retorna a XP necessária para o próximo nível"""
    if level == 1:
        return 100
    required_xp = 100
    for _ in range(1, level):
        required_xp = int(required_xp * 1.5)
    return required_xp


class Economia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mine_cooldown = 300  # 5 minutos (300 segundos) entre minerações
        self.daily_cooldown = 86400  # 24 horas
        self.caca_cooldown = 120  # 2 minutos entre caças rápidas
        self.caca_longa_duration = 43200  # 12 horas em segundos
        self.check_cacas_longas.start()

    def ensure_user(self, user_id: int):
        """Garante que o usuário existe no banco de dados"""
        uid = str(user_id)
        db = self.bot.db()
        if uid not in db:
            db[uid] = {
                "sobre": None,
                "tempo_total": 0,
                "soul": 0,
                "xp": 0,
                "level": 1,
                "last_daily": None,
                "last_mine": None,
                "mine_streak": 0,
                "last_caca": None,
                "caca_streak": 0,
                "caca_longa_ativa": None,
                "missoes": [],
                "missoes_completas": []
            }
            self.bot.save_db(db)
        else:
            defaults = {
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
            for key, value in defaults.items():
                if key not in db[uid]:
                    db[uid][key] = value
            self.bot.save_db(db)
        return uid

    def add_xp(self, user_id: int, amount: int):
        """Adiciona XP e atualiza o nível se necessário"""
        uid = self.ensure_user(user_id)
        db = self.bot.db()
        
        old_level = db[uid].get("level", 1)
        db[uid]["xp"] = db[uid].get("xp", 0) + amount
        new_level = calculate_level(db[uid]["xp"])
        db[uid]["level"] = new_level
        
        self.bot.save_db(db)
        
        # Retorna se subiu de nível
        return new_level > old_level, new_level

    def add_soul(self, user_id: int, amount: int):
        """Adiciona almas ao usuário"""
        uid = self.ensure_user(user_id)
        db = self.bot.db()
        db[uid]["soul"] = db[uid].get("soul", 0) + amount
        self.bot.save_db(db)
    
    def update_missao_progresso(self, db: dict, uid: str, tipo: str, quantidade: int = 1):
        """Atualiza o progresso de missões"""
        missoes = db[uid].get("missoes", [])
        for missao in missoes:
            if missao.get("tipo") == tipo:
                missao["progresso"] = missao.get("progresso", 0) + quantidade

    @app_commands.command(name="daily", description="Receba sua recompensa diária de almas e XP!")
    async def daily(self, interaction: discord.Interaction):
        uid = self.ensure_user(interaction.user.id)
        db = self.bot.db()
        
        last_daily = db[uid].get("last_daily")
        now = datetime.datetime.now()
        
        streak = db[uid].get("daily_streak", 0)
        
        if last_daily:
            last_daily_dt = datetime.datetime.fromisoformat(last_daily)
            time_diff = (now - last_daily_dt).total_seconds()
            
            if time_diff < self.daily_cooldown:
                remaining = self.daily_cooldown - time_diff
                hours = int(remaining // 3600)
                minutes = int((remaining % 3600) // 60)
                seconds = int(remaining % 60)
                
                embed = discord.Embed(
                    title="⏰ Daily já coletado!",
                    description=f"Você já coletou seu daily hoje!\n"
                              f"Próximo daily disponível em: **{hours}h {minutes}m {seconds}s**",
                    color=discord.Color.orange()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            elif time_diff >= self.daily_cooldown * 2:
                # Se passou mais de 48 horas, resetar streak
                streak = 0
        else:
            streak = 0
        
        # Incrementar streak
        streak += 1
        
        # Recompensas do daily
        base_souls = random.randint(50, 150)
        base_xp = random.randint(20, 50)
        bonus_souls = int(base_souls * (1 + streak * 0.1))  # 10% de bônus por streak
        bonus_xp = int(base_xp * (1 + streak * 0.1))
        
        # Adicionar recompensas
        self.add_soul(interaction.user.id, bonus_souls)
        leveled_up, new_level = self.add_xp(interaction.user.id, bonus_xp)
        
        # Recarregar DB e atualizar last_daily e streak
        db = self.bot.db()
        db[uid]["last_daily"] = now.isoformat()
        db[uid]["daily_streak"] = streak
        
        # Atualizar progresso de missões
        self.update_missao_progresso(db, uid, "daily", 1)
        
        self.bot.save_db(db)
        
        embed = discord.Embed(
            title="🎁 Daily Coletado!",
            description=f"**{interaction.user.mention}** coletou sua recompensa diária!",
            color=discord.Color.gold()
        )
        embed.add_field(name="💰 Almas ganhas", value=f"**{bonus_souls}** 🔮", inline=True)
        embed.add_field(name="⭐ XP ganho", value=f"**{bonus_xp}** XP", inline=True)
        embed.add_field(name="🔥 Streak", value=f"**{streak}** dias consecutivos", inline=True)
        
        if leveled_up:
            embed.add_field(
                name="🎉 Level Up!",
                value=f"Você subiu para o nível **{new_level}**!",
                inline=False
            )
        
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="Aeternum Exilium • Sistema de Economia")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="mine", description="Mine e ganhe almas! (Cooldown: 60s)")
    async def mine(self, interaction: discord.Interaction):
        uid = self.ensure_user(interaction.user.id)
        db = self.bot.db()
        
        last_mine = db[uid].get("last_mine")
        now = datetime.datetime.now()
        
        if last_mine:
            last_mine_dt = datetime.datetime.fromisoformat(last_mine)
            time_diff = (now - last_mine_dt).total_seconds()
            
            if time_diff < self.mine_cooldown:
                remaining = self.mine_cooldown - time_diff
                embed = discord.Embed(
                    title="⏰ Aguarde!",
                    description=f"Você precisa esperar **{int(remaining)}s** para minerar novamente!",
                    color=discord.Color.orange()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        
        # Recompensas da mineração
        base_souls = random.randint(10, 50)
        base_xp = random.randint(5, 15)
        
        # Bônus por streak de mineração
        streak = db[uid].get("mine_streak", 0) + 1
        bonus_multiplier = min(1 + (streak * 0.05), 2.0)  # Máximo 2x de bônus
        bonus_souls = int(base_souls * bonus_multiplier)
        bonus_xp = int(base_xp * bonus_multiplier)
        
        # Chance de encontrar itens raros
        rare_chance = random.random()
        rare_bonus = 0
        rare_message = ""
        
        if rare_chance < 0.05:  # 5% de chance
            rare_bonus = random.randint(100, 300)
            bonus_souls += rare_bonus
            rare_message = "🔮 **Você encontrou uma gema rara!**"
        elif rare_chance < 0.15:  # 10% de chance
            rare_bonus = random.randint(50, 150)
            bonus_souls += rare_bonus
            rare_message = "✨ **Você encontrou um cristal especial!**"
        
        # Adicionar recompensas
        self.add_soul(interaction.user.id, bonus_souls)
        leveled_up, new_level = self.add_xp(interaction.user.id, bonus_xp)
        
        # Recarregar DB e atualizar last_mine e streak
        db = self.bot.db()
        db[uid]["last_mine"] = now.isoformat()
        db[uid]["mine_streak"] = streak
        
        # Atualizar progresso de missões
        self.update_missao_progresso(db, uid, "mine", 1)
        
        self.bot.save_db(db)
        
        # Emojis aleatórios para a mineração
        mine_emojis = ["⛏️", "🔨", "🔮", "⚒️", "🪨"]
        mine_emoji = random.choice(mine_emojis)
        
        embed = discord.Embed(
            title=f"{mine_emoji} Mineração Concluída!",
            description=f"**{interaction.user.mention}** minerou com sucesso!",
            color=discord.Color.blue()
        )
        embed.add_field(name="💰 Almas ganhas", value=f"**{bonus_souls}** 🔮", inline=True)
        embed.add_field(name="⭐ XP ganho", value=f"**{bonus_xp}** XP", inline=True)
        embed.add_field(name="🔥 Streak", value=f"**{streak}** minerações", inline=True)
        
        if rare_message:
            embed.add_field(name="🎁 Achado Especial!", value=rare_message, inline=False)
        
        if leveled_up:
            embed.add_field(
                name="🎉 Level Up!",
                value=f"Você subiu para o nível **{new_level}**!",
                inline=False
            )
        
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="Aeternum Exilium • Sistema de Mineração")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="balance", description="Veja quantas almas você possui")
    @app_commands.describe(membro="Membro para ver o saldo (opcional)")
    async def balance(self, interaction: discord.Interaction, membro: discord.Member = None):
        membro = membro or interaction.user
        uid = self.ensure_user(membro.id)
        db = self.bot.db()
        
        souls = db[uid].get("soul", 0)
        xp = db[uid].get("xp", 0)
        level = db[uid].get("level", 1)
        
        xp_for_next = get_xp_for_next_level(level)
        xp_for_current = get_xp_for_level(level)
        current_xp_progress = xp - xp_for_current
        progress_percent = int((current_xp_progress / xp_for_next) * 100)
        
        embed = discord.Embed(
            title=f"💰 Carteira de {membro.display_name}",
            color=discord.Color.green()
        )
        embed.add_field(name="🔮 Almas", value=f"**{souls:,}** 🔮", inline=True)
        embed.add_field(name="⭐ Nível", value=f"**{level}**", inline=True)
        embed.add_field(name="📊 XP", value=f"**{xp:,}** XP", inline=True)
        embed.add_field(
            name="📈 Progresso para próximo nível",
            value=f"**{current_xp_progress}/{xp_for_next}** XP ({progress_percent}%)",
            inline=False
        )
        
        # Barra de progresso visual
        bar_length = 20
        filled = int((current_xp_progress / xp_for_next) * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        embed.add_field(name="Progresso", value=f"`{bar}`", inline=False)
        
        embed.set_thumbnail(url=membro.display_avatar.url)
        embed.set_footer(text="Aeternum Exilium • Sistema de Economia")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="top-souls", description="Ranking dos mais ricos em almas")
    async def top_souls(self, interaction: discord.Interaction):
        db = self.bot.db()
        
        ranking_items = []
        for uid, data in db.items():
            try:
                user_id = int(uid)
                member = interaction.guild.get_member(user_id) if interaction.guild else None
                if member and not member.bot:
                    souls = data.get("soul", 0)
                    ranking_items.append((uid, souls))
                elif not member:
                    user = await self.bot.fetch_user(user_id)
                    if not user.bot:
                        souls = data.get("soul", 0)
                        ranking_items.append((uid, souls))
            except (ValueError, discord.NotFound, discord.HTTPException):
                continue
        
        ranking = sorted(ranking_items, key=lambda x: x[1], reverse=True)[:10]
        
        embed = discord.Embed(
            title="🏆 Top 10 — Mais Ricos em Almas",
            color=discord.Color.gold()
        )
        
        if not ranking:
            embed.description = "Ainda não há registros."
        else:
            for pos, (uid, souls) in enumerate(ranking, start=1):
                member = interaction.guild.get_member(int(uid)) if interaction.guild else None
                if member:
                    nome = member.display_name
                else:
                    try:
                        user = await self.bot.fetch_user(int(uid))
                        nome = user.name
                    except:
                        nome = f"Usuário {uid}"
                embed.add_field(
                    name=f"{pos}. {nome}",
                    value=f"**{souls:,}** 🔮",
                    inline=False
                )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="top-level", description="Ranking dos maiores níveis")
    async def top_level(self, interaction: discord.Interaction):
        db = self.bot.db()
        
        ranking_items = []
        for uid, data in db.items():
            try:
                user_id = int(uid)
                member = interaction.guild.get_member(user_id) if interaction.guild else None
                if member and not member.bot:
                    level = data.get("level", 1)
                    xp = data.get("xp", 0)
                    ranking_items.append((uid, level, xp))
                elif not member:
                    user = await self.bot.fetch_user(user_id)
                    if not user.bot:
                        level = data.get("level", 1)
                        xp = data.get("xp", 0)
                        ranking_items.append((uid, level, xp))
            except (ValueError, discord.NotFound, discord.HTTPException):
                continue
        
        ranking = sorted(ranking_items, key=lambda x: (x[1], x[2]), reverse=True)[:10]
        
        embed = discord.Embed(
            title="🏆 Top 10 — Maiores Níveis",
            color=discord.Color.purple()
        )
        
        if not ranking:
            embed.description = "Ainda não há registros."
        else:
            for pos, (uid, level, xp) in enumerate(ranking, start=1):
                member = interaction.guild.get_member(int(uid)) if interaction.guild else None
                if member:
                    nome = member.display_name
                else:
                    try:
                        user = await self.bot.fetch_user(int(uid))
                        nome = user.name
                    except:
                        nome = f"Usuário {uid}"
                embed.add_field(
                    name=f"{pos}. {nome}",
                    value=f"Nível **{level}** | **{xp:,}** XP",
                    inline=False
                )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="missoes", description="Veja suas missões disponíveis")
    async def missoes(self, interaction: discord.Interaction):
        uid = self.ensure_user(interaction.user.id)
        db = self.bot.db()
        
        # Tipos de missões disponíveis
        tipos_missoes = {
            "daily": {
                "nome": "Daily Completo",
                "descricao": "Colete seu daily",
                "recompensa_soul": 25,
                "recompensa_xp": 15
            },
            "mine": {
                "nome": "Mineração",
                "descricao": "Mine 5 vezes",
                "recompensa_soul": 50,
                "recompensa_xp": 30,
                "objetivo": 5
            },
            "mensagens": {
                "nome": "Comunicador",
                "descricao": "Envie 20 mensagens",
                "recompensa_soul": 40,
                "recompensa_xp": 25,
                "objetivo": 20
            },
            "call": {
                "nome": "Social",
                "descricao": "Fique 30 minutos em call",
                "recompensa_soul": 60,
                "recompensa_xp": 40,
                "objetivo": 1800  # 30 minutos em segundos
            }
        }
        
        missoes_ativas = db[uid].get("missoes", [])
        missoes_completas = db[uid].get("missoes_completas", [])
        
        # Se não houver missões ativas, criar novas
        if not missoes_ativas:
            # Criar 3 missões aleatórias
            tipos_disponiveis = list(tipos_missoes.keys())
            missoes_ativas = []
            for _ in range(3):
                tipo = random.choice(tipos_disponiveis)
                missao = tipos_missoes[tipo].copy()
                missao["tipo"] = tipo
                missao["progresso"] = 0
                missoes_ativas.append(missao)
            db[uid]["missoes"] = missoes_ativas
            self.bot.save_db(db)
        
        embed = discord.Embed(
            title="📋 Suas Missões",
            description=f"**{interaction.user.mention}** - Missões disponíveis",
            color=discord.Color.blue()
        )
        
        for idx, missao in enumerate(missoes_ativas, start=1):
            objetivo = missao.get("objetivo", 1)
            progresso = missao.get("progresso", 0)
            status = "✅" if progresso >= objetivo else "⏳"
            
            embed.add_field(
                name=f"{status} {idx}. {missao['nome']}",
                value=f"{missao['descricao']}\n"
                      f"Progresso: **{progresso}/{objetivo}**\n"
                      f"Recompensa: **{missao['recompensa_soul']}** 🔮 + **{missao['recompensa_xp']}** XP",
                inline=False
            )
        
        embed.add_field(
            name="📊 Estatísticas",
            value=f"Missões completas: **{len(missoes_completas)}**",
            inline=False
        )
        
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="Aeternum Exilium • Sistema de Missões")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="claim-missao", description="Reivindique a recompensa de uma missão completa")
    @app_commands.describe(numero="Número da missão para reivindicar (1, 2 ou 3)")
    async def claim_missao(self, interaction: discord.Interaction, numero: int):
        if numero < 1 or numero > 3:
            await interaction.response.send_message(
                "❌ Número inválido! Use um número entre 1 e 3.",
                ephemeral=True
            )
            return
        
        uid = self.ensure_user(interaction.user.id)
        db = self.bot.db()
        
        missoes_ativas = db[uid].get("missoes", [])
        
        if not missoes_ativas or len(missoes_ativas) < numero:
            await interaction.response.send_message(
                "❌ Missão não encontrada!",
                ephemeral=True
            )
            return
        
        missao = missoes_ativas[numero - 1]
        objetivo = missao.get("objetivo", 1)
        progresso = missao.get("progresso", 0)
        
        if progresso < objetivo:
            await interaction.response.send_message(
                f"❌ Esta missão ainda não foi completada! Progresso: **{progresso}/{objetivo}**",
                ephemeral=True
            )
            return
        
        # Dar recompensas
        recompensa_soul = missao.get("recompensa_soul", 0)
        recompensa_xp = missao.get("recompensa_xp", 0)
        
        self.add_soul(interaction.user.id, recompensa_soul)
        leveled_up, new_level = self.add_xp(interaction.user.id, recompensa_xp)
        
        # Remover missão e adicionar às completas
        missoes_ativas.pop(numero - 1)
        missoes_completas = db[uid].get("missoes_completas", [])
        missoes_completas.append(missao.get("tipo", "unknown"))
        db[uid]["missoes"] = missoes_ativas
        db[uid]["missoes_completas"] = missoes_completas
        self.bot.save_db(db)
        
        embed = discord.Embed(
            title="🎉 Missão Reivindicada!",
            description=f"Você reivindicou a recompensa da missão **{missao['nome']}**!",
            color=discord.Color.green()
        )
        embed.add_field(name="💰 Almas ganhas", value=f"**{recompensa_soul}** 🔮", inline=True)
        embed.add_field(name="⭐ XP ganho", value=f"**{recompensa_xp}** XP", inline=True)
        
        if leveled_up:
            embed.add_field(
                name="🎉 Level Up!",
                value=f"Você subiu para o nível **{new_level}**!",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="caça", description="Caçe almas na floresta escura! (Cooldown: 2min)")
    async def caca(self, interaction: discord.Interaction):
        uid = self.ensure_user(interaction.user.id)
        db = self.bot.db()
        
        last_caca = db[uid].get("last_caca")
        now = datetime.datetime.now()
        
        if last_caca:
            last_caca_dt = datetime.datetime.fromisoformat(last_caca)
            time_diff = (now - last_caca_dt).total_seconds()
            
            if time_diff < self.caca_cooldown:
                remaining = self.caca_cooldown - time_diff
                minutes = int(remaining // 60)
                seconds = int(remaining % 60)
                embed = discord.Embed(
                    title="⏰ Aguarde!",
                    description=f"Você precisa esperar **{minutes}m {seconds}s** para caçar novamente!",
                    color=discord.Color.orange()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        
        # Verificar se está em caça longa
        caca_longa = db[uid].get("caca_longa_ativa")
        if caca_longa:
            embed = discord.Embed(
                title="⏰ Caça Longa em Andamento!",
                description="Você já está em uma caça longa! Use `/caça-longa` para ver o status.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Iniciar caçada
        embed_inicio = discord.Embed(
            title="🌲 Caçada Iniciada!",
            description=f"**{interaction.user.mention}** entrou na floresta escura em busca de almas...",
            color=discord.Color.dark_green()
        )
        # Imagem de floresta escura à noite com luz da lua
        embed_inicio.set_image(url="https://i.pinimg.com/736x/15/29/ab/1529abc5be2e4c2a4392ef693503b7db.jpg")
        await interaction.response.send_message(embed=embed_inicio)
        
        # Aguardar 5 segundos
        await asyncio.sleep(5)
        
        # Calcular recompensas
        base_souls = random.randint(15, 60)
        base_xp = random.randint(8, 20)
        
        # Bônus por streak de caça
        streak = db[uid].get("caca_streak", 0) + 1
        bonus_multiplier = min(1 + (streak * 0.06), 2.2)  # Máximo 2.2x de bônus
        bonus_souls = int(base_souls * bonus_multiplier)
        bonus_xp = int(base_xp * bonus_multiplier)
        
        # Chance de encontrar almas raras
        rare_chance = random.random()
        rare_bonus = 0
        rare_message = ""
        
        if rare_chance < 0.04:  # 4% de chance
            rare_bonus = random.randint(120, 350)
            bonus_souls += rare_bonus
            rare_message = "👻 **Você encontrou uma alma rara poderosa!**"
        elif rare_chance < 0.12:  # 8% de chance
            rare_bonus = random.randint(60, 180)
            bonus_souls += rare_bonus
            rare_message = "✨ **Você encontrou uma alma especial!**"
        
        # Adicionar recompensas
        self.add_soul(interaction.user.id, bonus_souls)
        leveled_up, new_level = self.add_xp(interaction.user.id, bonus_xp)
        
        # Recarregar DB e atualizar last_caca e streak
        db = self.bot.db()
        db[uid]["last_caca"] = now.isoformat()
        db[uid]["caca_streak"] = streak
        self.bot.save_db(db)
        
        # Embed de resultado
        embed_resultado = discord.Embed(
            title="🌲 Caçada Concluída!",
            description=f"**{interaction.user.mention}** retornou da floresta escura!",
            color=discord.Color.dark_purple()
        )
        embed_resultado.add_field(name="💰 Almas ganhas", value=f"**{bonus_souls}** 🔮", inline=True)
        embed_resultado.add_field(name="⭐ XP ganho", value=f"**{bonus_xp}** XP", inline=True)
        embed_resultado.add_field(name="🔥 Streak", value=f"**{streak}** caçadas", inline=True)
        
        if rare_message:
            embed_resultado.add_field(name="🎁 Achado Especial!", value=rare_message, inline=False)
        
        if leveled_up:
            embed_resultado.add_field(
                name="🎉 Level Up!",
                value=f"Você subiu para o nível **{new_level}**!",
                inline=False
            )
        
        embed_resultado.set_thumbnail(url=interaction.user.display_avatar.url)
        embed_resultado.set_footer(text="Aeternum Exilium • Sistema de Caça")
        
        # Editar a mensagem original
        await interaction.edit_original_response(embed=embed_resultado)

    @app_commands.command(name="caça-longa", description="Inicie uma caçada longa de 12 horas por almas valiosas!")
    async def caca_longa(self, interaction: discord.Interaction):
        uid = self.ensure_user(interaction.user.id)
        db = self.bot.db()
        
        # Verificar se já está em uma caça longa
        caca_longa = db[uid].get("caca_longa_ativa")
        if caca_longa:
            inicio_dt = datetime.datetime.fromisoformat(caca_longa["inicio"])
            agora = datetime.datetime.now()
            tempo_decorrido = (agora - inicio_dt).total_seconds()
            tempo_restante = self.caca_longa_duration - tempo_decorrido
            
            if tempo_restante > 0:
                horas = int(tempo_restante // 3600)
                minutos = int((tempo_restante % 3600) // 60)
                segundos = int(tempo_restante % 60)
                
                embed = discord.Embed(
                    title="🌲 Caça Longa em Andamento",
                    description=f"Você já está em uma caça longa!\n"
                              f"Tempo restante: **{horas}h {minutos}m {segundos}s**",
                    color=discord.Color.blue()
                )
                embed.set_image(url="https://i.pinimg.com/736x/15/29/ab/1529abc5be2e4c2a4392ef693503b7db.jpg")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            else:
                # Caça longa já terminou, processar recompensas
                await self.processar_caca_longa(interaction.user.id, interaction.channel_id)
                return
        
        # Iniciar nova caça longa
        agora = datetime.datetime.now()
        fim_caca = agora + datetime.timedelta(seconds=self.caca_longa_duration)
        
        db[uid]["caca_longa_ativa"] = {
            "inicio": agora.isoformat(),
            "fim": fim_caca.isoformat(),
            "channel_id": interaction.channel_id
        }
        self.bot.save_db(db)
        
        embed = discord.Embed(
            title="🌲 Caça Longa Iniciada!",
            description=f"**{interaction.user.mention}** partiu para uma caçada longa na floresta escura!\n\n"
                       f"⏰ Esta caçada levará **12 horas** para completar.\n"
                       f"📬 Você receberá uma notificação quando a caçada terminar!",
            color=discord.Color.dark_green()
        )
        embed.set_image(url="https://i.pinimg.com/736x/15/29/ab/1529abc5be2e4c2a4392ef693503b7db.jpg")
        embed.add_field(
            name="⏳ Tempo estimado",
            value=f"Termina em: <t:{int(fim_caca.timestamp())}:R>",
            inline=False
        )
        embed.set_footer(text="Aeternum Exilium • Sistema de Caça Longa")
        await interaction.response.send_message(embed=embed)

    async def processar_caca_longa(self, user_id: int, channel_id: int = None):
        """Processa uma caça longa concluída"""
        uid = self.ensure_user(user_id)
        db = self.bot.db()
        
        caca_longa = db[uid].get("caca_longa_ativa")
        if not caca_longa:
            return
        
        # Calcular recompensas (maiores que caça rápida)
        base_souls = random.randint(200, 500)
        base_xp = random.randint(100, 250)
        
        # Bônus extra por caça longa
        bonus_souls = int(base_souls * 1.5)
        bonus_xp = int(base_xp * 1.5)
        
        # Chance maior de encontrar almas raras
        rare_chance = random.random()
        rare_bonus = 0
        rare_message = ""
        
        if rare_chance < 0.15:  # 15% de chance
            rare_bonus = random.randint(300, 800)
            bonus_souls += rare_bonus
            rare_message = "👻 **Você encontrou uma alma lendária!**"
        elif rare_chance < 0.35:  # 20% de chance
            rare_bonus = random.randint(150, 400)
            bonus_souls += rare_bonus
            rare_message = "✨ **Você encontrou uma alma rara poderosa!**"
        
        # Adicionar recompensas
        self.add_soul(user_id, bonus_souls)
        leveled_up, new_level = self.add_xp(user_id, bonus_xp)
        
        # Recarregar DB e remover caça longa ativa
        db = self.bot.db()
        del db[uid]["caca_longa_ativa"]
        self.bot.save_db(db)
        
        # Criar embed de resultado
        embed = discord.Embed(
            title="🌲 Caça Longa Concluída!",
            description=f"<@{user_id}> retornou da floresta escura após 12 horas de caçada!",
            color=discord.Color.gold()
        )
        embed.add_field(name="💰 Almas ganhas", value=f"**{bonus_souls}** 🔮", inline=True)
        embed.add_field(name="⭐ XP ganho", value=f"**{bonus_xp}** XP", inline=True)
        
        if rare_message:
            embed.add_field(name="🎁 Achado Especial!", value=rare_message, inline=False)
        
        if leveled_up:
            embed.add_field(
                name="🎉 Level Up!",
                value=f"Você subiu para o nível **{new_level}**!",
                inline=False
            )
        
        embed.set_image(url="https://i.pinimg.com/736x/15/29/ab/1529abc5be2e4c2a4392ef693503b7db.jpg")
        embed.set_footer(text="Aeternum Exilium • Sistema de Caça Longa")
        
        # Tentar enviar mensagem no canal
        try:
            if channel_id:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    await channel.send(embed=embed)
                    return
        except:
            pass
        
        # Se não conseguir enviar no canal, tentar DM
        try:
            user = await self.bot.fetch_user(user_id)
            await user.send(embed=embed)
        except:
            pass

    @tasks.loop(seconds=60)  # Verificar a cada minuto
    async def check_cacas_longas(self):
        """Verifica e processa caças longas concluídas"""
        if not self.bot.is_ready():
            return
        
        db = self.bot.db()
        agora = datetime.datetime.now()
        
        for uid, data in db.items():
            caca_longa = data.get("caca_longa_ativa")
            if not caca_longa:
                continue
            
            try:
                fim_dt = datetime.datetime.fromisoformat(caca_longa["fim"])
                if agora >= fim_dt:
                    # Caça longa terminou
                    user_id = int(uid)
                    channel_id = caca_longa.get("channel_id")
                    await self.processar_caca_longa(user_id, channel_id)
            except (ValueError, KeyError):
                continue

    @check_cacas_longas.before_loop
    async def before_check_cacas_longas(self):
        await self.bot.wait_until_ready()

    def cog_unload(self):
        self.check_cacas_longas.cancel()


async def setup(bot):
    cog = Economia(bot)
    await bot.add_cog(cog)

