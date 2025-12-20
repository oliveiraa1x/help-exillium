import discord
from discord.ext import commands
from discord import app_commands, ui
from typing import Optional, Dict, List

class HelpPageView(ui.View):
    """Navegação interativa entre páginas de ajuda"""
    
    def __init__(self, embeds: Dict[str, discord.Embed], categories: List[str], timeout: int = 300):
        super().__init__(timeout=timeout)
        self.embeds = embeds
        self.categories = categories
        self.current_page = 0
        self.message = None
        self.update_buttons()
    
    def update_buttons(self):
        """Atualiza o estilo dos botões baseado na página atual"""
        # Limpar botões antigos
        for item in self.children[:]:
            self.remove_item(item)
        
        # Botão anterior
        anterior = ui.Button(
            label="⬅️ Anterior",
            style=discord.ButtonStyle.secondary,
            disabled=(self.current_page == 0)
        )
        anterior.callback = self.anterior_callback
        self.add_item(anterior)
        
        # Botões de categoria dinâmicos
        for idx, category in enumerate(self.categories):
            button = ui.Button(
                label=category.split()[0][:10],
                style=discord.ButtonStyle.primary if idx == self.current_page else discord.ButtonStyle.secondary,
                custom_id=f"help_cat_{idx}"
            )
            button.callback = lambda interaction, idx=idx: self.categoria_callback(interaction, idx)
            self.add_item(button)
        
        # Botão próximo
        proximo = ui.Button(
            label="Próximo ➡️",
            style=discord.ButtonStyle.secondary,
            disabled=(self.current_page == len(self.categories) - 1)
        )
        proximo.callback = self.proximo_callback
        self.add_item(proximo)
    
    async def anterior_callback(self, interaction: discord.Interaction):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            category = self.categories[self.current_page]
            await interaction.response.edit_message(embed=self.embeds[category], view=self)
    
    async def proximo_callback(self, interaction: discord.Interaction):
        if self.current_page < len(self.categories) - 1:
            self.current_page += 1
            self.update_buttons()
            category = self.categories[self.current_page]
            await interaction.response.edit_message(embed=self.embeds[category], view=self)
    
    async def categoria_callback(self, interaction: discord.Interaction, idx: int):
        self.current_page = idx
        self.update_buttons()
        category = self.categories[self.current_page]
        await interaction.response.edit_message(embed=self.embeds[category], view=self)

class Help(commands.Cog):
    """Sistema de Help com informações de todos os comandos"""
    
    def __init__(self, bot):
        self.bot = bot
    
    def cog_unload(self):
        self.bot.tree.remove_command(self.help.name, type=self.help.type)
    
    def criar_embeds(self) -> tuple[Dict[str, discord.Embed], List[str]]:
        """Cria todos os embeds de ajuda"""
        embeds = {}
        
        # ==================== PERFIL ====================
        embed_perfil = discord.Embed(
            title="👤 PERFIL",
            description="Comandos para gerenciar seu perfil e relacionamentos",
            color=discord.Color.blue()
        )
        embed_perfil.add_field(
            name="/perfil [membro]",
            value="**Mostra:** Perfil completo do usuário\n**Exibe:** Sobre Mim, status de casamento, avatar\n**Cooldown:** Nenhum",
            inline=False
        )
        embed_perfil.add_field(
            name="/set-sobre <texto>",
            value="**Define:** Seu 'Sobre Mim' no perfil\n**Limite:** Até 100 caracteres\n**Cooldown:** Nenhum",
            inline=False
        )
        embed_perfil.add_field(
            name="/casar <membro>",
            value="**Ação:** Propõe casamento a alguém\n**Resultado:** Membro tem 2 min para aceitar\n**Cooldown:** Nenhum",
            inline=False
        )
        embed_perfil.add_field(
            name="/divorciar",
            value="**Ação:** Divorcia de seu parceiro(a)\n**Aviso:** Irá notificar o outro membro\n**Cooldown:** Nenhum",
            inline=False
        )
        embed_perfil.set_footer(text="🌙 Rede Exilium • /help")
        embeds["👤 PERFIL"] = embed_perfil
        
        # ==================== MENSAGENS ====================
        embed_msgs = discord.Embed(
            title="💬 MENSAGENS",
            description="Comandos para criar mensagens personalizadas",
            color=discord.Color.purple()
        )
        embed_msgs.add_field(
            name="/mensagem <título> <texto>",
            value="**Cria:** Uma embed personalizada\n**Uso:** Para anúncios ou recados no chat\n**Cooldown:** Nenhum",
            inline=False
        )
        embed_msgs.add_field(
            name="/frase <texto>",
            value="**Envia:** Uma frase ou poesia para o servidor\n**Limite:** Sem limite de caracteres\n**Cooldown:** Nenhum",
            inline=False
        )
        embed_msgs.set_footer(text="🌙 Rede Exilium • /help")
        embeds["💬 MENSAGENS"] = embed_msgs
        
        # ==================== ECONOMIA ====================
        embed_eco = discord.Embed(
            title="💰 ECONOMIA",
            description="Sistema de moeda (Almas) e ganhos",
            color=discord.Color.gold()
        )
        embed_eco.add_field(
            name="/daily",
            value="**Ganha:** 50-150 almas + XP\n**Cooldown:** 24 horas\n**Dica:** Use todos os dias!",
            inline=False
        )
        embed_eco.add_field(
            name="/mine",
            value="**Ganha:** 10-50 almas\n**Cooldown:** 5 minutos\n**Rápido:** Para farming constante",
            inline=False
        )
        embed_eco.add_field(
            name="/caça",
            value="**Ganha:** 15-60 almas\n**Cooldown:** 2 minutos\n**Balanceado:** Entre speed e lucro",
            inline=False
        )
        embed_eco.add_field(
            name="/caça-longa",
            value="**Ganha:** 200-500 almas\n**Cooldown:** 12 horas\n**Premium:** Maior recompensa, maior espera",
            inline=False
        )
        embed_eco.add_field(
            name="/balance [membro]",
            value="**Mostra:** Seu saldo de almas e XP\n**Ranking:** Sua posição\n**Cooldown:** Nenhum",
            inline=False
        )
        embed_eco.set_footer(text="🌙 Rede Exilium • /help")
        embeds["💰 ECONOMIA"] = embed_eco
        
        # ==================== LOJA ====================
        embed_loja = discord.Embed(
            title="🛍️ LOJA & VENDAS",
            description="Compre, venda e gerencie itens com almas",
            color=discord.Color.red()
        )
        embed_loja.add_field(
            name="/loja",
            value="**Acessa:** Catálogo completo de itens\n**Filtra:** Por raridade e tipo\n**Moeda:** Almas",
            inline=False
        )
        embed_loja.add_field(
            name="/comprar <item>",
            value="**Compra:** Um item da loja\n**Preço:** Varia por raridade\n**Estoque:** Ilimitado",
            inline=False
        )
        embed_loja.add_field(
            name="/vender <item>",
            value="**Vende:** Item para a loja (70% do valor)\n**Penalidade:** 30% de perda\n**Rápido:** Para desopilar",
            inline=False
        )
        embed_loja.add_field(
            name="/inventario",
            value="**Lista:** Todos os itens que possui\n**Equip:** Mostra itens equipados\n**Raridades:** Coloridas por nível",
            inline=False
        )
        embed_loja.add_field(
            name="/equipar <item>",
            value="**Equipa:** Itens passivos (Amuletos, Anéis)\n**Bônus:** +5% de ganho por item\n**Max:** 4 itens simultâneos",
            inline=False
        )
        embed_loja.add_field(
            name="/desequipar <item>",
            value="**Remove:** Item equipado\n**Volta:** Para o inventário\n**Penalidade:** Nenhuma",
            inline=False
        )
        embed_loja.set_footer(text="🌙 Rede Exilium • /help")
        embeds["🛍️ LOJA & VENDAS"] = embed_loja
        
        # ==================== CRAFT & FORJA ====================
        embed_craft = discord.Embed(
            title="⚒️ CRAFT & FORJA",
            description="Crie itens poderosos a partir de materiais",
            color=discord.Color.orange()
        )
        embed_craft.add_field(
            name="/craft <item>",
            value="**Crafta:** Itens usando materiais\n**Receitas:** Diferentes por item\n**Lucro:** Valor maior que os materiais",
            inline=False
        )
        embed_craft.add_field(
            name="/forjar <arma>",
            value="**Forja:** Armas poderosas (Almas necessárias)\n**Raridade:** Até Ancestral\n**Risco:** 12-25% de falha (perde almas)",
            inline=False
        )
        embed_craft.add_field(
            name="Armas Forjáveis:",
            value="🔷 **Totem do Vazio** - 5000 almas (12% falha)\n⚔️ **Lâmina Sombria** - 8000 almas (15% falha)\n🗡️ **Punhal Ancilar** - 6000 almas (18% falha)\n💎 **Orbe Cósmica** - 7000 almas (20% falha)\n❤️ **Coração Escuro** - 9000 almas (22% falha)\n🔨 **Martelo Aniquilador** - 10000 almas (25% falha)",
            inline=False
        )
        embed_craft.set_footer(text="🌙 Rede Exilium • /help")
        embeds["⚒️ CRAFT & FORJA"] = embed_craft
        
        # ==================== MERCADO ====================
        embed_mercado = discord.Embed(
            title="🏪 MERCADO",
            description="Compre e venda itens com outros membros",
            color=discord.Color.green()
        )
        embed_mercado.add_field(
            name="/mercado",
            value="**Acessa:** Todas as listagens de itens\n**Ofertas:** De outros jogadores\n**Sistema:** Sem taxa (negociação direta)",
            inline=False
        )
        embed_mercado.add_field(
            name="Como Funciona:",
            value="1️⃣ Veja ofertas de outros players\n2️⃣ Negocie preço diretamente\n3️⃣ Confirme a transação\n4️⃣ Itens são transferidos\n\n**Taxa:** 5% em todas as transações",
            inline=False
        )
        embed_mercado.set_footer(text="🌙 Rede Exilium • /help")
        embeds["🏪 MERCADO"] = embed_mercado
        
        # ==================== RANKING ====================
        embed_rank = discord.Embed(
            title="🏆 RANKING",
            description="Veja os tops do servidor",
            color=discord.Color.yellow()
        )
        embed_rank.add_field(
            name="/ranking",
            value="**Mostra:** Top 10 jogadores por almas\n**Atualização:** Em tempo real\n**Seu Lugar:** Destacado no ranking",
            inline=False
        )
        embed_rank.add_field(
            name="/top-tempo",
            value="**Mostra:** Top 10 membros em calls\n**Ordenação:** Tempo total em voz\n**Atualização:** A cada 6 horas",
            inline=False
        )
        embed_rank.set_footer(text="🌙 Rede Exilium • /help")
        embeds["🏆 RANKING"] = embed_rank
        
        # ==================== VOZ ====================
        embed_voz = discord.Embed(
            title="🎧 VOICE & CALL",
            description="Comandos relacionados a canais de voz",
            color=discord.Color.blurple()
        )
        embed_voz.add_field(
            name="/callstatus",
            value="**Mostra:** Seu tempo atual na call\n**Formato:** Horas, minutos e segundos\n**Atualização:** Em tempo real",
            inline=False
        )
        embed_voz.add_field(
            name="/stay-voice",
            value="**Conecta:** Bot ao seu canal de voz\n**Duração:** Permanece indefinidamente\n**Uso:** Para ambientes musicais",
            inline=False
        )
        embed_voz.add_field(
            name="/leave-voice",
            value="**Desconecta:** Bot do canal de voz\n**Imediato:** Sai na hora\n**Nenhum:** Efeito colateral",
            inline=False
        )
        embed_voz.add_field(
            name="/uptime",
            value="**Mostra:** Há quanto tempo o bot está online\n**Informação:** Tempo de atividade contínua\n**Cooldown:** Nenhum",
            inline=False
        )
        embed_voz.set_footer(text="🌙 Rede Exilium • /help")
        embeds["🎧 VOICE & CALL"] = embed_voz
        
        # ==================== RPG ====================
        embed_rpg = discord.Embed(
            title="⚔️ RPG & COMBATE",
            description="Sistema de combate contra inimigos",
            color=discord.Color.red()
        )
        embed_rpg.add_field(
            name="/combate",
            value="**Inicia:** Uma batalha contra um mob\n**Sistema:** Turn-based\n**Recompensa:** Vitória = Almas + XP\n**Risco:** Derrota = Nenhuma penalidade",
            inline=False
        )
        embed_rpg.add_field(
            name="Tipos de Inimigos:",
            value="🐺 **Lobo das Sombras**\n🧟 **Zumbi Antigo**\n🐉 **Dragão Menor**\n👻 **Espectro da Floresta**\n🧌 **Gigante de Gelo**",
            inline=False
        )
        embed_rpg.set_footer(text="🌙 Rede Exilium • /help")
        embeds["⚔️ RPG & COMBATE"] = embed_rpg
        
        # ==================== SISTEMAS ====================
        embed_sist = discord.Embed(
            title="ℹ️ SISTEMAS",
            description="Informações sobre os sistemas de jogo",
            color=discord.Color.teal()
        )
        embed_sist.add_field(
            name="💎 Raridades de Itens",
            value="🟦 **Comum** - 1.0x valor\n🟩 **Raro** - 2.5x valor\n🟪 **Épico** - 5.0x valor\n🟨 **Lendário** - 10.0x valor\n⭐ **Ancestral** - 20.0x valor",
            inline=False
        )
        embed_sist.add_field(
            name="✨ Itens Passivos",
            value="🔮 **Amuleto da Sorte** (+5% almas)\n💍 **Anel da Ganância** (+5% almas)\n📿 **Colar da Proteção** (+5% almas)\n🎩 **Chapéu da Sabedoria** (+5% XP)",
            inline=False
        )
        embed_sist.add_field(
            name="💰 Moeda Principal",
            value="**Almas** = Moeda do servidor\n**Uso:** Comprar itens, forjar, craftar\n**Ganho:** Daily, Mine, Caça, Combate",
            inline=False
        )
        embed_sist.set_footer(text="🌙 Rede Exilium • /help")
        embeds["ℹ️ SISTEMAS"] = embed_sist
        
        categories = list(embeds.keys())
        return embeds, categories
    
    @app_commands.command(name="help", description="📚 Veja todos os comandos disponíveis no servidor!")
    async def help(self, interaction: discord.Interaction):
        """Comando de ajuda com navegação por botões - Visível para todos"""
        embeds, categories = self.criar_embeds()
        
        view = HelpPageView(embeds, categories)
        
        # Enviar mensagem visível para todos (não ephemeral)
        await interaction.response.send_message(
            embed=embeds[categories[0]],
            view=view,
            ephemeral=False  # Visível para todos no chat
        )
    
    @app_commands.command(name="info-loja", description="Informações detalhadas sobre o sistema de loja")
    async def info_loja(self, interaction: discord.Interaction):
        """Mostra informações detalhadas sobre a loja"""
        embed = discord.Embed(
            title="🏪 Sistema de Loja",
            description="Tudo que você precisa saber sobre compra, venda e forja",
            color=discord.Color.from_rgb(255, 107, 157)
        )
        
        embed.add_field(
            name="📦 Items Disponíveis (34 total)",
            value="""**Craft (9):** Materiais para crafting
**Forja (6):** Armas lendárias (Totem, Lâmina, Punhal, Orbe, Coração, Martelo)
**Passivos (4):** Equipáveis com bônus (Anel da Ganância 2x almas!)
**Consumíveis (6):** Poções, elixires, pergaminhos
**Caixas (4):** Comum, Rara, Ancestral, Vazio
**Especiais (5):** Alma Corrompida, Fragmento, Relíquia, Selo, Essência""",
            inline=False
        )
        
        embed.add_field(
            name="💎 Raridades & Valores",
            value="""⚪ **Comum** → 1.0x
🔵 **Raro** → 2.5x
🟣 **Épico** → 5.0x
🟡 **Lendário** → 10.0x
🔴 **Ancestral** → 20.0x

*Multiplicadores aplicados ao valor base*""",
            inline=False
        )
        
        embed.add_field(
            name="⚒️ Sistema de Forja",
            value="""**Taxa de Falha por arma:**
• 🔷 Totem do Vazio: 12%
• ⚔️ Lâmina Sombria: 15%
• 🗡️ Punhal Ancilar: 18%
• 💎 Orbe Cósmica: 20%
• ❤️ Coração Escuro: 22%
• 🔨 Martelo Aniquilador: 25%

**Se falhar:** Perde TUDO (almas + ingredientes)
**Se suceder:** Item valioso (até 70.000 almas)""",
            inline=False
        )
        
        embed.add_field(
            name="💰 Economia Balanceada",
            value="""✅ Venda com penalidade (70% retorno)
✅ Taxa de falha controla inflação
✅ Custo duplo (almas + materiais)
✅ Sem farm infinito
✅ Progresso controlado e satisfatório""",
            inline=False
        )
        
        embed.add_field(
            name="🎯 Comandos Relacionados",
            value="`/loja` - Acessar a loja\n`/comprar` - Comprar itens\n`/vender` - Vender itens\n`/forjar` - Forjar armas\n`/craft` - Craftar itens",
            inline=False
        )
        
        embed.set_footer(text="🌙 Rede Exilium • Sistema de Economia")
        await interaction.response.send_message(embed=embed, ephemeral=False)
    
    @app_commands.command(name="info-raridade", description="Informações detalhadas sobre sistema de raridades")
    async def info_raridade(self, interaction: discord.Interaction):
        """Mostra informações sobre raridades"""
        embed = discord.Embed(
            title="💎 Sistema de Raridades",
            description="Como as raridades afetam o valor dos items",
            color=discord.Color.gold()
        )
        
        raridades = [
            ("⚪ **COMUM**", "1.0x", "Fácil de conseguir, baixo valor", "Itens básicos, loot comum"),
            ("🔵 **RARO**", "2.5x", "Materiais básicos de crafting", "2.5x mais valioso que comum"),
            ("🟣 **ÉPICO**", "5.0x", "Componentes importantes", "5.0x mais valioso que comum"),
            ("🟡 **LENDÁRIO**", "10.0x", "Armas poderosas", "10.0x mais valioso que comum"),
            ("🔴 **ANCESTRAL**", "20.0x", "Itens extremos, muito raros", "20.0x mais valioso que comum")
        ]
        
        for nome, mult, desc, info in raridades:
            embed.add_field(
                name=f"{nome} - {mult}",
                value=f"**Descrição:** {desc}\n**Info:** {info}",
                inline=False
            )
        
        embed.add_field(
            name="📊 Exemplo de Cálculo",
            value="""**Cenário:** Item base de 100 almas, raridade Épico

Valor final = 100 × 5.0 = **500 almas**

**Ao comprar:** Custa 500 almas na loja

**Ao vender (70% retorno):**
500 × 0.7 = **350 almas recebidos**

**Perda na venda:** 150 almas (30%)""",
            inline=False
        )
        
        embed.add_field(
            name="🎯 Dicas",
            value="""💡 Itens Ancestrais são raríssimos e muito valiosos
💡 Vender items com penalidade não compensa - prefira craftar
💡 Forjar armas de raridade alta é muito arriscado
💡 Organize seu inventário por raridade para mais organização""",
            inline=False
        )
        
        embed.set_footer(text="🌙 Rede Exilium • Sistema de Raridades")
        await interaction.response.send_message(embed=embed, ephemeral=False)

async def setup(bot):
    await bot.add_cog(Help(bot))
