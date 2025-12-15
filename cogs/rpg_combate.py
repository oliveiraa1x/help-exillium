# rpg_combate.py - Mini game de RPG com combate contra mobs integrado com economia

import discord
import json
import random
from pathlib import Path
from discord.ext import commands
from discord import app_commands

# Importar funções de banco de dados do db.py centralizado
from db import load_economia_db, save_economia_db


def ensure_user_economia(user_id: int):
    """Garante que o usuário existe no banco de dados de economia"""
    uid = str(user_id)
    db = load_economia_db()
    if uid not in db:
        db[uid] = {
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
        save_economia_db(db)
    return uid


def add_soul(user_id: int, amount: int):
    """Adiciona almas (soul) ao usuário"""
    uid = ensure_user_economia(user_id)
    db = load_economia_db()
    db[uid]["soul"] = db[uid].get("soul", 0) + amount
    save_economia_db(db)


# ==============================
# Dados dos Mobs
# ==============================
MOBS = {
    "lobo": {
        "emoji": "🐺",
        "nome": "Lobo Selvagem",
        "vida": 3,
        "ataques": ["Mordida", "Arranho", "Investida"],
        "gif_ataque": "https://media.giphy.com/media/3o6ZsYq8d0pgLRZQXm/giphy.gif",
        "gif_morte": "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif"
    },
    "urso": {
        "emoji": "🐻",
        "nome": "Urso Feroz",
        "vida": 3,
        "ataques": ["Golpe de Garra", "Investida Poderosa", "Urro"],
        "gif_ataque": "https://media.giphy.com/media/l0HlDtKo5lWXtKlVm/giphy.gif",
        "gif_morte": "https://media.giphy.com/media/l0MYtKKzpmxvH4XbS/giphy.gif"
    }
}


# ==============================
# View com os Botões de Combate
# ==============================
class CombateButtons(discord.ui.View):
    def __init__(self, user_id: int, mob_type: str, timeout: float = 600.0):
        super().__init__(timeout=timeout)
        self.user_id = user_id
        self.mob_type = mob_type
        self.mob = MOBS[mob_type].copy()
        self.player_vida = 3
        self.mob_vida = self.mob["vida"]
        self.turno_atual = "jogador"
        self.jogador_derrotado = False
        self.mob_derrotado = False
        self.historico = []
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ Apenas o jogador original pode interagir!",
                ephemeral=True
            )
            return False
        
        if self.mob_derrotado or self.jogador_derrotado:
            await interaction.response.send_message(
                "❌ O combate já terminou!",
                ephemeral=True
            )
            return False
        
        return True

    @discord.ui.button(label="🗡️ Ataque", style=discord.ButtonStyle.danger)
    async def atacar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.interaction_check(interaction):
            return
        
        # Defer a interação imediatamente
        await interaction.response.defer()
        
        # Jogador ataca
        dano_jogador = random.randint(1, 2)
        self.mob_vida -= dano_jogador
        self.historico.append(f"⚔️ Você atacou com sua **Espada**! Causou **{dano_jogador} de dano**!")
        
        if self.mob_vida <= 0:
            self.mob_derrotado = True
            await self.enviar_resultado_vitoria(interaction)
            return
        
        # Mob ataca
        ataque_mob = random.choice(self.mob["ataques"])
        dano_mob = random.randint(1, 2)
        self.player_vida -= dano_mob
        self.historico.append(f"🐾 {self.mob['nome']} usou **{ataque_mob}**! Causou **{dano_mob} de dano**!")
        
        if self.player_vida <= 0:
            self.jogador_derrotado = True
            await self.enviar_resultado_derrota(interaction)
            return
        
        await self.atualizar_combate(interaction)

    @discord.ui.button(label="🛡️ Defesa", style=discord.ButtonStyle.primary)
    async def defender(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.interaction_check(interaction):
            return
        
        # Defer a interação imediatamente
        await interaction.response.defer()
        
        # Jogador se defende
        self.historico.append(f"🛡️ Você se protegeu com seu **Escudo**! Reduzindo dano em 1.")
        
        # Mob ataca
        ataque_mob = random.choice(self.mob["ataques"])
        dano_mob = max(0, random.randint(1, 2) - 1)  # Reduz 1 de dano
        self.player_vida -= dano_mob
        self.historico.append(f"🐾 {self.mob['nome']} usou **{ataque_mob}**! Causou **{dano_mob} de dano**!")
        
        if self.player_vida <= 0:
            self.jogador_derrotado = True
            await self.enviar_resultado_derrota(interaction)
            return
        
        await self.atualizar_combate(interaction)

    @discord.ui.button(label="⚔️ Ataque Duplo", style=discord.ButtonStyle.danger)
    async def ataque_duplo(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.interaction_check(interaction):
            return
        
        # Defer a interação imediatamente
        await interaction.response.defer()
        
        # Jogador faz ataque duplo
        dano_jogador = random.randint(2, 3)
        self.mob_vida -= dano_jogador
        self.historico.append(f"⚔️ Você atacou com **Ataques Rápidos**! Causou **{dano_jogador} de dano**!")
        
        if self.mob_vida <= 0:
            self.mob_derrotado = True
            await self.enviar_resultado_vitoria(interaction)
            return
        
        # Mob contra-ataca
        ataque_mob = random.choice(self.mob["ataques"])
        dano_mob = random.randint(1, 2)
        self.player_vida -= dano_mob
        self.historico.append(f"🐾 {self.mob['nome']} usou **{ataque_mob}**! Causou **{dano_mob} de dano**!")
        
        if self.player_vida <= 0:
            self.jogador_derrotado = True
            await self.enviar_resultado_derrota(interaction)
            return
        
        await self.atualizar_combate(interaction)

    async def atualizar_combate(self, interaction: discord.Interaction):
        """Atualiza a mensagem de combate"""
        embed = self.criar_embed_combate()
        try:
            await interaction.edit_original_response(embed=embed, view=self)
        except discord.NotFound:
            # Se a mensagem foi deletada ou expirou, usar follow_up
            await interaction.followup.send(embed=embed, view=self)

    def criar_embed_combate(self) -> discord.Embed:
        """Cria o embed com o status do combate"""
        embed = discord.Embed(
            title="⚔️ COMBATE RPG ⚔️",
            color=discord.Color.gold()
        )
        
        # Barra de vida do jogador
        vida_jogador_str = "❤️ " * self.player_vida + "🖤 " * (3 - self.player_vida)
        embed.add_field(
            name="👤 Sua Vida",
            value=f"{vida_jogador_str} ({self.player_vida}/3)",
            inline=False
        )
        
        # Barra de vida do mob
        vida_mob_str = "❤️ " * max(0, self.mob_vida) + "🖤 " * max(0, 3 - self.mob_vida)
        embed.add_field(
            name=f"{self.mob['emoji']} {self.mob['nome']}",
            value=f"{vida_mob_str} ({max(0, self.mob_vida)}/3)",
            inline=False
        )
        
        # Histórico dos últimos ataques
        historico_texto = "\n".join(self.historico[-3:]) if self.historico else "Combate iniciado!"
        embed.add_field(
            name="📜 Histórico",
            value=historico_texto,
            inline=False
        )
        
        # Adicionar GIF do mob atacando
        embed.set_image(url=self.mob.get("gif_ataque", ""))
        
        return embed

    async def enviar_resultado_vitoria(self, interaction: discord.Interaction):
        """Envia o resultado da vitória"""
        embed = discord.Embed(
            title="🎉 VITÓRIA! 🎉",
            description=f"Você derrotou o **{self.mob['nome']}**!",
            color=discord.Color.green()
        )
        
        # Adiciona almas ao jogador
        add_soul(self.user_id, 100)
        
        embed.add_field(
            name="💰 Recompensa",
            value="✨ **+100 Almas**",
            inline=False
        )
        
        # Mostra estatísticas finais
        embed.add_field(
            name="📊 Resultado Final",
            value=f"Sua Vida: {self.player_vida}/3\n{self.mob['emoji']} Vida do Inimigo: 0/3",
            inline=False
        )
        
        # Adicionar GIF de morte do mob
        embed.set_image(url=self.mob.get("gif_morte", ""))
        
        # Remove os buttons
        self.clear_items()
        
        try:
            await interaction.edit_original_response(embed=embed, view=self)
        except discord.NotFound:
            await interaction.followup.send(embed=embed, view=self)

    async def enviar_resultado_derrota(self, interaction: discord.Interaction):
        """Envia o resultado da derrota"""
        embed = discord.Embed(
            title="💀 DERROTA! 💀",
            description=f"Você foi derrotado pelo **{self.mob['nome']}**!",
            color=discord.Color.red()
        )
        
        embed.add_field(
            name="⚠️ Resultado",
            value="Nenhuma recompensa foi obtida...",
            inline=False
        )
        
        # Mostra estatísticas finais
        embed.add_field(
            name="📊 Resultado Final",
            value=f"Sua Vida: {self.player_vida}/3\n{self.mob['emoji']} Vida do Inimigo: {max(0, self.mob_vida)}/3",
            inline=False
        )
        
        # Adicionar GIF de morte do mob
        embed.set_image(url=self.mob.get("gif_morte", ""))
        
        # Remove os buttons
        self.clear_items()
        
        try:
            await interaction.edit_original_response(embed=embed, view=self)
        except discord.NotFound:
            await interaction.followup.send(embed=embed, view=self)


# ==============================
# Cog com os Comandos
# ==============================
class RPGCombate(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="combate", description="Inicie um combate contra um mob de RPG!")
    async def combate(self, interaction: discord.Interaction):
        """Inicia um combate contra um mob aleatório (lobo ou urso)"""
        
        # Escolhe aleatoriamente entre lobo e urso
        mob_type = random.choice(list(MOBS.keys()))
        
        # Cria a view com os botões
        view = CombateButtons(interaction.user.id, mob_type)
        
        # Cria o embed inicial
        embed = discord.Embed(
            title="⚔️ COMBATE RPG ⚔️",
            description=f"Um **{MOBS[mob_type]['nome']}** apareceu!",
            color=discord.Color.gold()
        )
        
        # Barra de vida do jogador
        vida_jogador_str = "❤️ " * 3
        embed.add_field(
            name="👤 Sua Vida",
            value=f"{vida_jogador_str} (3/3)",
            inline=False
        )
        
        # Barra de vida do mob
        vida_mob_str = "❤️ " * 3
        embed.add_field(
            name=f"{MOBS[mob_type]['emoji']} {MOBS[mob_type]['nome']}",
            value=f"{vida_mob_str} (3/3)",
            inline=False
        )
        
        embed.add_field(
            name="📜 Informações do Combate",
            value="Escolha uma ação para atacar o inimigo!\n\n"
                  "🗡️ **Ataque**: Dano normal (1-2)\n"
                  "🛡️ **Defesa**: Reduz dano em 1 (0-1)\n"
                  "⚔️ **Ataque Duplo**: Dano maior (2-3)\n\n"
                  "📍 **Vitória**: Derrote o mob em 3 ataques\n"
                  "📍 **Derrota**: Se receber 3 danos\n"
                  "💰 **Recompensa**: 100 Almas",
            inline=False
        )
        
        # Adicionar GIF do mob aparecendo
        embed.set_image(url=MOBS[mob_type].get("gif_ataque", ""))
        
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(RPGCombate(bot))
