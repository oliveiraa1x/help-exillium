import discord
import random
import datetime
import asyncio
import json
from pathlib import Path
from discord import app_commands
from discord.ext import commands, tasks


# ==================== BALANCEAMENTO ====================
# Ajuste esses valores para balancear a economia
class BalanceConfig:
    """Configuração de balanceamento da economia"""
    
    # Moedas (Almas)
    DAILY_MIN = 50
    DAILY_MAX = 150
    MINE_MIN = 10
    MINE_MAX = 50
    CACA_MIN = 15
    CACA_MAX = 60
    CACA_LONGA_MIN = 200
    CACA_LONGA_MAX = 500
    
    # Raridades (multiplicadores para items)
    RARIDADE_COMUM = 1.0
    RARIDADE_RARO = 2.5
    RARIDADE_EPICO = 5.0
    RARIDADE_LENDARIO = 10.0
    RARIDADE_ANCESTRAL = 20.0
    
    # Forja (taxa de falha)
    FORJA_TOTEM_FALHA = 0.12  # 12%
    FORJA_LAMINA_FALHA = 0.15  # 15%
    FORJA_PUNHAL_FALHA = 0.18  # 18%
    FORJA_ORBE_FALHA = 0.20    # 20%
    FORJA_CORACAO_FALHA = 0.22 # 22%
    FORJA_MARTELO_FALHA = 0.25 # 25%
    
    # Venda de items
    VENDA_PENALIDADE = 0.30  # Perde 30%, recebe 70%
    
    # Mercado
    MERCADO_TAX = 0.05  # Taxa de 5% em transações
    
    # Cooldowns (em segundos)
    MINE_COOLDOWN = 300  # 5 minutos
    CACA_COOLDOWN = 120  # 2 minutos
    DAILY_COOLDOWN = 86400  # 24 horas
    TRABALHO_COOLDOWN = 3600  # 1 hora
    CACA_LONGA_DURATION = 43200  # 12 horas

# =====================================================

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
        # Usar valores do BalanceConfig
        self.mine_cooldown = BalanceConfig.MINE_COOLDOWN
        self.daily_cooldown = BalanceConfig.DAILY_COOLDOWN
        self.caca_cooldown = BalanceConfig.CACA_COOLDOWN
        self.caca_longa_duration = BalanceConfig.CACA_LONGA_DURATION
        self.trabalho_cooldown = BalanceConfig.TRABALHO_COOLDOWN
        
        # Definição dos trabalhos disponíveis
        self.trabalhos = {
            "programador": {
                "nome": "💻 Programador",
                "souls_min": 80,
                "souls_max": 120,
                "xp_min": 70,
                "xp_max": 100,
                "descricao": "Desenvolva sistemas e ganhe boas recompensas!"
            },
            "médico": {
                "nome": "⚕️ Médico",
                "souls_min": 100,
                "souls_max": 150,
                "xp_min": 80,
                "xp_max": 120,
                "descricao": "Cure os feridos e seja bem recompensado!"
            },
            "engenheiro": {
                "nome": "🔧 Engenheiro",
                "souls_min": 85,
                "souls_max": 130,
                "xp_min": 75,
                "xp_max": 110,
                "descricao": "Construa e projete grandes obras!"
            },
            "professor": {
                "nome": "📚 Professor",
                "souls_min": 70,
                "souls_max": 110,
                "xp_min": 90,
                "xp_max": 130,
                "descricao": "Ensine e ganhe muita experiência!"
            },
            "pintor": {
                "nome": "🎨 Pintor",
                "souls_min": 60,
                "souls_max": 100,
                "xp_min": 50,
                "xp_max": 80,
                "descricao": "Crie obras de arte e seja recompensado!"
            },
            "porteiro": {
                "nome": "🚪 Porteiro",
                "souls_min": 50,
                "souls_max": 80,
                "xp_min": 40,
                "xp_max": 70,
                "descricao": "Proteja a entrada e ganhe sua recompensa!"
            },
            "cozinheiro": {
                "nome": "👨‍🍳 Cozinheiro",
                "souls_min": 65,
                "souls_max": 105,
                "xp_min": 55,
                "xp_max": 85,
                "descricao": "Prepare deliciosas refeições!"
            },
            "motorista": {
                "nome": "🚗 Motorista",
                "souls_min": 55,
                "souls_max": 90,
                "xp_min": 45,
                "xp_max": 75,
                "descricao": "Transporte pessoas e mercadorias!"
            },
            "músico": {
                "nome": "🎵 Músico",
                "souls_min": 60,
                "souls_max": 95,
                "xp_min": 70,
                "xp_max": 100,
                "descricao": "Encante com sua música!"
            },
            "comerciante": {
                "nome": "🏪 Comerciante",
                "souls_min": 75,
                "souls_max": 115,
                "xp_min": 60,
                "xp_max": 90,
                "descricao": "Venda produtos e lucre!"
            }
        }
        
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
                "trabalho_atual": None,
                "last_trabalho": None,
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
                "trabalho_atual": None,
                "last_trabalho": None,
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
        embed.add_field(name="💰 Almas ganhas", value=f"**{bonus_souls}** <:alma:1443647166399909998>", inline=True)
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

    @app_commands.command(name="pay", description="Pague outro membro. Requer confirmação do destinatário.")
    @app_commands.describe(membro="Membro destinatário", valor="Quantidade de almas a enviar")
    async def pay(self, interaction: discord.Interaction, membro: discord.Member, valor: int):
        # Validações iniciais
        if membro.bot:
            await interaction.response.send_message("❌ Você não pode enviar almas para bots.", ephemeral=True)
            return

        if membro.id == interaction.user.id:
            await interaction.response.send_message("❌ Você não pode enviar almas para si mesmo.", ephemeral=True)
            return

        if valor <= 0:
            await interaction.response.send_message("❌ O valor deve ser maior que zero.", ephemeral=True)
            return

        sender_uid = self.ensure_user(interaction.user.id)
        db = self.bot.db()
        balance = db.get(sender_uid, {}).get("soul", 0)

        if balance < valor:
            await interaction.response.send_message("❌ Saldo insuficiente.", ephemeral=True)
            return

        # Criar view de confirmação para o destinatário
        class TransferConfirmView(discord.ui.View):
            def __init__(self, bot, sender_id: int, recipient_id: int, amount: int, timeout: int = 120):
                super().__init__(timeout=timeout)
                self.bot = bot
                self.sender_id = sender_id
                self.recipient_id = recipient_id
                self.amount = amount
                self.confirmed = False

            def disable_all_items(self):
                """Compat shim: desabilita todos os itens do view."""
                for item in list(self.children):
                    try:
                        item.disabled = True
                    except Exception:
                        pass

            @discord.ui.button(label="Confirmar Transferência", style=discord.ButtonStyle.success)
            async def confirm(self, interaction_button: discord.Interaction, button: discord.ui.Button):
                if interaction_button.user.id != self.recipient_id:
                    await interaction_button.response.send_message("Somente o destinatário pode confirmar esta transferência.", ephemeral=True)
                    return

                # Recarregar DB e checar saldo do remetente novamente
                db_local = self.bot.db()
                sender_uid_local = str(self.sender_id)
                recipient_uid_local = str(self.recipient_id)

                if sender_uid_local not in db_local:
                    await interaction_button.response.send_message("❌ Dados do remetente não encontrados.", ephemeral=True)
                    self.disable_all_items()
                    try:
                        await interaction_button.message.edit(view=self)
                    except:
                        pass
                    return

                if db_local[sender_uid_local].get("soul", 0) < self.amount:
                    await interaction_button.response.send_message("❌ Transferência falhou: remetente não tem saldo suficiente.", ephemeral=True)
                    self.disable_all_items()
                    try:
                        await interaction_button.message.edit(view=self)
                    except:
                        pass
                    return

                # Garantir que o destinatário possui entrada no DB
                if recipient_uid_local not in db_local:
                    db_local[recipient_uid_local] = {
                        "sobre": None,
                        "tempo_total": 0,
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

                # Efetuar transferência
                db_local[sender_uid_local]["soul"] = db_local[sender_uid_local].get("soul", 0) - self.amount
                db_local[recipient_uid_local]["soul"] = db_local[recipient_uid_local].get("soul", 0) + self.amount
                self.bot.save_db(db_local)

                self.confirmed = True
                self.disable_all_items()
                try:
                    await interaction_button.response.send_message(f"✅ Transferência de **{self.amount:,}** almas confirmada por {interaction_button.user.mention}.")
                except:
                    pass
                try:
                    await interaction_button.message.edit(view=self)
                except:
                    pass

        view = TransferConfirmView(self.bot, interaction.user.id, membro.id, valor)

        embed = discord.Embed(
            title="🔁 Pedido de Transferência",
            description=f"{interaction.user.mention} quer enviar **{valor:,}** almas para {membro.mention}.",
            color=discord.Color.blurple()
        )
        embed.set_footer(text="Clique em 'Confirmar Transferência' para aceitar. (2 minutos)")

        await interaction.response.send_message(embed=embed, view=view)

        # Aguardar confirmação; se não confirmado em tempo, desabilitar botões e notificar remetente
        await view.wait()

        if not view.confirmed:
            try:
                view.disable_all_items()
                await interaction.edit_original_response(view=view)
            except:
                pass
            try:
                await interaction.followup.send("❌ A transferência não foi confirmada a tempo.", ephemeral=True)
            except:
                pass

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
            rare_message = "<:alma:1443647166399909998> **Você encontrou uma gema rara!**"
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
        mine_emojis = ["⛏️", "🔨", "<:alma:1443647166399909998>", "⚒️", "🪨"]
        mine_emoji = random.choice(mine_emojis)
        
        embed = discord.Embed(
            title=f"{mine_emoji} Mineração Concluída!",
            description=f"**{interaction.user.mention}** minerou com sucesso!",
            color=discord.Color.blue()
        )
        embed.add_field(name="💰 Almas ganhas", value=f"**{bonus_souls}** <:alma:1443647166399909998>", inline=True)
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
        trabalho_atual = db[uid].get("trabalho_atual")
        
        xp_for_next = get_xp_for_next_level(level)
        xp_for_current = get_xp_for_level(level)
        current_xp_progress = xp - xp_for_current
        progress_percent = int((current_xp_progress / xp_for_next) * 100)
        
        embed = discord.Embed(
            title=f"💰 Carteira de {membro.display_name}",
            color=discord.Color.green()
        )
        embed.add_field(name="<:alma:1443647166399909998> Almas", value=f"**{souls:,}** <:alma:1443647166399909998>", inline=True)
        embed.add_field(name="⭐ Nível", value=f"**{level}**", inline=True)
        embed.add_field(name="📊 XP", value=f"**{xp:,}** XP", inline=True)
        embed.add_field(
            name="📈 Progresso para próximo nível",
            value=f"**{current_xp_progress}/{xp_for_next}** XP ({progress_percent}%)",
            inline=False
        )
        
        # Mostrar emprego ao invés da barra de progresso
        if trabalho_atual and trabalho_atual in self.trabalhos:
            trabalho_info = self.trabalhos[trabalho_atual]
            emprego_texto = trabalho_info["nome"]
        else:
            emprego_texto = "❌ Desempregado"
        
        embed.add_field(name="Emprego", value=emprego_texto, inline=False)
        
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
                    value=f"**{souls:,}** <:alma:1443647166399909998>",
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
                      f"Recompensa: **{missao['recompensa_soul']}** <:alma:1443647166399909998> + **{missao['recompensa_xp']}** XP",
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
        embed.add_field(name="💰 Almas ganhas", value=f"**{recompensa_soul}** <:alma:1443647166399909998>", inline=True)
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
        embed_resultado.add_field(name="💰 Almas ganhas", value=f"**{bonus_souls}** <:alma:1443647166399909998>", inline=True)
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
        embed.add_field(name="💰 Almas ganhas", value=f"**{bonus_souls}** <:alma:1443647166399909998>", inline=True)
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

    @app_commands.command(name="escolher-trabalho", description="Escolha sua profissão para ganhar almas e XP!")
    async def escolher_trabalho(self, interaction: discord.Interaction):
        uid = self.ensure_user(interaction.user.id)
        db = self.bot.db()
        
        trabalho_atual = db[uid].get("trabalho_atual")
        
        embed = discord.Embed(
            title="💼 Escolha sua Profissão",
            description="Selecione uma profissão para começar a trabalhar e ganhar recompensas!\n\n"
                       "**Profissões disponíveis:**\n",
            color=discord.Color.blue()
        )
        
        # Listar todos os trabalhos
        for key, trabalho in self.trabalhos.items():
            embed.add_field(
                name=trabalho["nome"],
                value=f"{trabalho['descricao']}\n"
                      f"💰 **{trabalho['souls_min']}-{trabalho['souls_max']}** almas\n"
                      f"⭐ **{trabalho['xp_min']}-{trabalho['xp_max']}** XP",
                inline=True
            )
        
        if trabalho_atual:
            trabalho_info = self.trabalhos.get(trabalho_atual, {})
            embed.add_field(
                name="📋 Profissão Atual",
                value=f"{trabalho_info.get('nome', trabalho_atual)}",
                inline=False
            )
        
        embed.set_footer(text="Use o menu abaixo para selecionar sua profissão!")
        
        # Criar select menu
        class TrabalhoSelect(discord.ui.Select):
            def __init__(self, cog_self):
                self.cog_self = cog_self
                options = [
                    discord.SelectOption(
                        label=trabalho["nome"],
                        value=key,
                        description=f"{trabalho['souls_min']}-{trabalho['souls_max']} souls • {trabalho['xp_min']}-{trabalho['xp_max']} XP",
                        emoji=trabalho["nome"].split()[0]
                    )
                    for key, trabalho in self.cog_self.trabalhos.items()
                ]
                super().__init__(
                    placeholder="Selecione sua profissão...",
                    options=options,
                    min_values=1,
                    max_values=1
                )
            
            async def callback(self, interaction: discord.Interaction):
                trabalho_escolhido = self.values[0]
                uid = self.cog_self.ensure_user(interaction.user.id)
                db = self.cog_self.bot.db()
                
                db[uid]["trabalho_atual"] = trabalho_escolhido
                self.cog_self.bot.save_db(db)
                
                trabalho_info = self.cog_self.trabalhos[trabalho_escolhido]
                
                embed = discord.Embed(
                    title="✅ Profissão Escolhida!",
                    description=f"**{interaction.user.mention}** agora trabalha como **{trabalho_info['nome']}**!",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="💼 Sua Profissão",
                    value=f"{trabalho_info['nome']}\n{trabalho_info['descricao']}",
                    inline=False
                )
                embed.add_field(
                    name="💰 Recompensas",
                    value=f"**{trabalho_info['souls_min']}-{trabalho_info['souls_max']}** almas\n"
                          f"**{trabalho_info['xp_min']}-{trabalho_info['xp_max']}** XP",
                    inline=False
                )
                embed.add_field(
                    name="⏰ Próximos passos",
                    value="Use `/trabalhar` para começar a trabalhar e ganhar recompensas!",
                    inline=False
                )
                embed.set_thumbnail(url=interaction.user.display_avatar.url)
                embed.set_footer(text="Aeternum Exilium • Sistema de Trabalho")
                
                await interaction.response.edit_message(embed=embed, view=None)
        
        class TrabalhoView(discord.ui.View):
            def __init__(self, cog_self):
                super().__init__(timeout=60)
                self.add_item(TrabalhoSelect(cog_self))
        
        await interaction.response.send_message(embed=embed, view=TrabalhoView(self))

    @app_commands.command(name="trabalhar", description="Trabalhe e ganhe almas e XP!")
    async def trabalhar(self, interaction: discord.Interaction):
        uid = self.ensure_user(interaction.user.id)
        db = self.bot.db()
        
        trabalho_atual = db[uid].get("trabalho_atual")
        
        # Verificar se o usuário escolheu uma profissão
        if not trabalho_atual or trabalho_atual not in self.trabalhos:
            embed = discord.Embed(
                title="❌ Sem Profissão",
                description="Você ainda não escolheu uma profissão!\n"
                          "Use `/escolher-trabalho` para selecionar sua profissão primeiro.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Verificar cooldown
        last_trabalho = db[uid].get("last_trabalho")
        now = datetime.datetime.now()
        
        if last_trabalho:
            last_trabalho_dt = datetime.datetime.fromisoformat(last_trabalho)
            time_diff = (now - last_trabalho_dt).total_seconds()
            
            if time_diff < self.trabalho_cooldown:
                remaining = self.trabalho_cooldown - time_diff
                hours = int(remaining // 3600)
                minutes = int((remaining % 3600) // 60)
                seconds = int(remaining % 60)
                
                embed = discord.Embed(
                    title="⏰ Descansando",
                    description=f"Você está cansado de trabalhar!\n"
                              f"Poderá trabalhar novamente em: **{hours}h {minutes}m {seconds}s**",
                    color=discord.Color.orange()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        
        # Processar trabalho
        trabalho_info = self.trabalhos[trabalho_atual]
        souls_ganhos = random.randint(trabalho_info["souls_min"], trabalho_info["souls_max"])
        xp_ganho = random.randint(trabalho_info["xp_min"], trabalho_info["xp_max"])
        
        # Adicionar recompensas
        self.add_soul(interaction.user.id, souls_ganhos)
        leveled_up, new_level = self.add_xp(interaction.user.id, xp_ganho)
        
        # Atualizar last_trabalho
        db = self.bot.db()
        db[uid]["last_trabalho"] = now.isoformat()
        
        # Atualizar progresso de missões
        self.update_missao_progresso(db, uid, "trabalhar", 1)
        
        self.bot.save_db(db)
        
        # Mensagens aleatórias de trabalho
        mensagens_trabalho = [
            "trabalhou duro e foi bem recompensado!",
            "completou suas tarefas com excelência!",
            "teve um dia produtivo de trabalho!",
            "se destacou no trabalho hoje!",
            "deu o seu melhor e foi reconhecido!"
        ]
        
        embed = discord.Embed(
            title=f"{trabalho_info['nome']} em Ação!",
            description=f"**{interaction.user.mention}** {random.choice(mensagens_trabalho)}",
            color=discord.Color.gold()
        )
        embed.add_field(
            name="💰 Almas ganhas",
            value=f"**{souls_ganhos}** <:alma:1443647166399909998>",
            inline=True
        )
        embed.add_field(
            name="⭐ XP ganho",
            value=f"**{xp_ganho}** XP",
            inline=True
        )
        embed.add_field(
            name="⏰ Próximo trabalho",
            value="Disponível em **1 hora**",
            inline=True
        )
        
        if leveled_up:
            embed.add_field(
                name="🎉 Level Up!",
                value=f"Você subiu para o nível **{new_level}**!",
                inline=False
            )
        
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="Aeternum Exilium • Sistema de Trabalho")
        
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    cog = Economia(bot)
    await bot.add_cog(cog)

