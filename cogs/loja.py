import discord
import json
import random
import asyncio
from datetime import datetime, timedelta
from discord import app_commands
from discord.ext import commands
from pathlib import Path


class Loja(commands.Cog):
    """Sistema de Loja, Compra e Venda de Items"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_path = Path("data")
        self.economia_file = self.data_path / "economia.json"
        self.inventario_file = self.data_path / "inventario.json"
    
    def load_json(self, file_path):
        """Carrega dados de um arquivo JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_json(self, file_path, data):
        """Salva dados em um arquivo JSON"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_user_inventory(self, user_id: str):
        """Obtém inventário do usuário (chama método de Inventario cog)"""
        inventario = self.load_json(self.inventario_file)
        user_id_str = str(user_id)
        
        if user_id_str not in inventario.get("usuarios", {}):
            inventario["usuarios"] = inventario.get("usuarios", {})
            inventario["usuarios"][user_id_str] = {
                "itens": {},
                "equipados": {},
                "almas": 0,
                "created_at": ""
            }
            self.save_json(self.inventario_file, inventario)
        
        return inventario["usuarios"][user_id_str]
    
    def add_item(self, user_id: str, item_id: str, quantidade: int = 1):
        """Adiciona item ao inventário"""
        inventario = self.load_json(self.inventario_file)
        user_id_str = str(user_id)
        user_inv = self.get_user_inventory(user_id)
        
        if item_id not in user_inv["itens"]:
            user_inv["itens"][item_id] = 0
        
        user_inv["itens"][item_id] += quantidade
        inventario["usuarios"][user_id_str] = user_inv
        self.save_json(self.inventario_file, inventario)
    
    def remove_item(self, user_id: str, item_id: str, quantidade: int = 1) -> bool:
        """Remove item do inventário"""
        inventario = self.load_json(self.inventario_file)
        user_id_str = str(user_id)
        user_inv = self.get_user_inventory(user_id)
        
        if item_id not in user_inv["itens"] or user_inv["itens"][item_id] < quantidade:
            return False
        
        user_inv["itens"][item_id] -= quantidade
        if user_inv["itens"][item_id] == 0:
            del user_inv["itens"][item_id]
        
        inventario["usuarios"][user_id_str] = user_inv
        self.save_json(self.inventario_file, inventario)
        return True
    
    def get_almas(self, user_id: str) -> int:
        """Obtém almas do usuário"""
        user_inv = self.get_user_inventory(user_id)
        return user_inv.get("almas", 0)
    
    def add_almas(self, user_id: str, quantidade: int):
        """Adiciona almas"""
        inventario = self.load_json(self.inventario_file)
        user_id_str = str(user_id)
        user_inv = self.get_user_inventory(user_id)
        user_inv["almas"] = user_inv.get("almas", 0) + quantidade
        inventario["usuarios"][user_id_str] = user_inv
        self.save_json(self.inventario_file, inventario)
    
    def remove_almas(self, user_id: str, quantidade: int) -> bool:
        """Remove almas se tiver quantidade suficiente"""
        user_inv = self.get_user_inventory(user_id)
        if user_inv.get("almas", 0) >= quantidade:
            inventario = self.load_json(self.inventario_file)
            user_id_str = str(user_id)
            user_inv["almas"] -= quantidade
            inventario["usuarios"][user_id_str] = user_inv
            self.save_json(self.inventario_file, inventario)
            return True
        return False
    
    def get_cor_embed(self, raridade: str):
        """Obtém cor do embed baseado na raridade"""
        cores = {
            "comum": 0x4A4A4A,
            "raro": 0x0099FF,
            "epico": 0x9933FF,
            "lendario": 0xFFD700,
            "ancestral": 0xFF4500
        }
        return cores.get(raridade, 0x808080)
    
    # ==================== COMANDOS ====================
    
    @app_commands.command(name="loja", description="Acesse a loja e compre itens com almas")
    async def loja(self, interaction: discord.Interaction):
        """Mostra loja de itens"""
        economia = self.load_json(self.economia_file)
        loja_items = economia.get("loja_items", {})
        
        user_almas = self.get_almas(interaction.user.id)
        
        # Categorizar itens
        categorias = {
            "consumivel": [],
            "lootbox": [],
            "especial": []
        }
        
        for item_id, item_data in loja_items.items():
            tipo = item_data.get("tipo", "consumivel")
            if tipo in categorias:
                categorias[tipo].append((item_id, item_data))
        
        # Criar view com buttons
        class LojaView(discord.ui.View):
            def __init__(self, ctx_self, items, economia):
                super().__init__(timeout=300)
                self.ctx = ctx_self
                self.items = items
                self.economia = economia
                self.current_category = "consumivel"
                self.page = 0
            
            @discord.ui.button(label="Consumíveis", style=discord.ButtonStyle.primary)
            async def consumivel_btn(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                self.current_category = "consumivel"
                self.page = 0
                await self.update_embed(button_interaction)
            
            @discord.ui.button(label="Lootboxes", style=discord.ButtonStyle.primary)
            async def lootbox_btn(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                self.current_category = "lootbox"
                self.page = 0
                await self.update_embed(button_interaction)
            
            @discord.ui.button(label="Especiais", style=discord.ButtonStyle.danger)
            async def especial_btn(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                self.current_category = "especial"
                self.page = 0
                await self.update_embed(button_interaction)
            
            async def update_embed(self, interaction: discord.Interaction):
                items = categorias[self.current_category]
                items_per_page = 5
                max_pages = (len(items) + items_per_page - 1) // items_per_page
                
                if self.page >= max_pages:
                    self.page = max_pages - 1
                
                embed = discord.Embed(
                    title=f"🏪 Loja - {self.current_category.upper()}",
                    description=f"Suas almas: **{user_almas}**\nPágina {self.page + 1}/{max_pages}",
                    color=0xFF6B9D
                )
                
                start_idx = self.page * items_per_page
                end_idx = start_idx + items_per_page
                
                for item_id, item_data in items[start_idx:end_idx]:
                    valor = item_data.get("valor", 0)
                    raridade = item_data.get("raridade", "comum")
                    emoji = item_data.get("emoji", "⭐")
                    descricao = item_data.get("descricao", "Sem descrição")
                    
                    embed.add_field(
                        name=f"{emoji} {item_data.get('nome', 'Item')}",
                        value=f"**Custo:** {valor} <:alma:1234567890>\n{descricao}",
                        inline=False
                    )
                
                await interaction.response.edit_message(embed=embed, view=self)
        
        view = LojaView(self, categorias, economia)
        
        embed = discord.Embed(
            title="🏪 Loja - CONSUMÍVEIS",
            description=f"Suas almas: **{user_almas}**\nPágina 1/1",
            color=0xFF6B9D
        )
        
        await interaction.response.send_message(embed=embed, view=view)
    
    @app_commands.command(name="comprar", description="Compre um item da loja")
    @app_commands.describe(item="ID do item para comprar", quantidade="Quantidade (padrão: 1)")
    async def comprar(self, interaction: discord.Interaction, item: str, quantidade: int = 1):
        """Compra um item da loja"""
        economia = self.load_json(self.economia_file)
        loja_items = economia.get("loja_items", {})
        
        if item not in loja_items:
            await interaction.response.send_message("❌ Item não existe na loja!", ephemeral=True)
            return
        
        item_data = loja_items[item]
        valor_unitario = item_data.get("valor", 0)
        custo_total = valor_unitario * quantidade
        
        user_almas = self.get_almas(interaction.user.id)
        
        if user_almas < custo_total:
            embed = discord.Embed(
                title="❌ Almas insuficientes",
                description=f"Você tem: **{user_almas}** almas\nNecessário: **{custo_total}** almas",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Fazer compra
        self.remove_almas(interaction.user.id, custo_total)
        self.add_item(interaction.user.id, item, quantidade)
        
        embed = discord.Embed(
            title="✅ Compra realizada!",
            description=f"Você comprou **{quantidade}x** {item_data.get('emoji', '')} **{item_data.get('nome', 'Item')}**",
            color=discord.Color.green()
        )
        embed.add_field(name="Custo", value=f"{custo_total} almas", inline=False)
        embed.set_footer(text=f"Almas restantes: {user_almas - custo_total}")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="craft", description="Crafta um item usando materiais")
    @app_commands.describe(item="ID do item para craftar")
    async def craft(self, interaction: discord.Interaction, item: str):
        """Crafta um item"""
        economia = self.load_json(self.economia_file)
        itens_craft = economia.get("itens_craft", {})
        user_inv = self.get_user_inventory(interaction.user.id)
        
        if item not in itens_craft:
            # Mostrar lista de items que podem ser craftados
            embed = discord.Embed(
                title="🔨 Craft - Items Disponíveis",
                description="Use `/craft item:nome_do_item`",
                color=0xFF9500
            )
            
            for craft_id, craft_data in list(itens_craft.items())[:10]:
                emoji = craft_data.get("emoji", "⭐")
                nome = craft_data.get("nome", craft_id)
                raridade = craft_data.get("raridade", "comum")
                embed.add_field(
                    name=f"{emoji} {nome}",
                    value=f"ID: `{craft_id}`\nRaridade: {raridade}",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        item_data = itens_craft[item]
        nome_item = item_data.get("nome", item)
        emoji = item_data.get("emoji", "⭐")
        
        embed = discord.Embed(
            title=f"🔨 Crafting: {emoji} {nome_item}",
            color=self.get_cor_embed(item_data.get("raridade", "comum"))
        )
        
        embed.description = f"Sistema de craft em desenvolvimento para: `{item}`"
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="forjar", description="Forja uma arma poderosa")
    @app_commands.describe(item="ID da arma para forjar")
    async def forjar(self, interaction: discord.Interaction, item: str):
        """Forja uma arma"""
        await interaction.response.defer()
        
        economia = self.load_json(self.economia_file)
        itens_forja = economia.get("itens_forja", {})
        user_inv = self.get_user_inventory(interaction.user.id)
        user_almas = user_inv.get("almas", 0)
        
        if item not in itens_forja:
            # Mostrar lista de itens que podem ser forjados
            embed = discord.Embed(
                title="⚒️ Forja - Armas Disponíveis",
                description="Use `/forjar item:nome_da_arma`",
                color=0xFF9500
            )
            
            for forja_id, forja_data in itens_forja.items():
                emoji = forja_data.get("emoji", "⚔️")
                nome = forja_data.get("nome", forja_id)
                raridade = forja_data.get("raridade", "lendario")
                custo = forja_data.get("custo_almas", 0)
                taxa_falha = forja_data.get("taxa_falha", 0) * 100
                
                embed.add_field(
                    name=f"{emoji} {nome}",
                    value=f"ID: `{forja_id}`\nCusto: {custo} almas | Falha: {taxa_falha:.0f}%",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        arma_data = itens_forja[item]
        nome_arma = arma_data.get("nome", item)
        emoji = arma_data.get("emoji", "⚔️")
        custo = arma_data.get("custo_almas", 0)
        ingredientes = arma_data.get("ingredientes", {})
        taxa_falha = arma_data.get("taxa_falha", 0.15)
        
        # Verificar almas
        if user_almas < custo:
            embed = discord.Embed(
                title="❌ Almas insuficientes",
                description=f"Você tem: **{user_almas}** almas\nNecessário: **{custo}** almas",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Verificar ingredientes
        itens_inv = user_inv.get("itens", {})
        ingredientes_ok = True
        faltando = []
        
        for ing_id, ing_qtd in ingredientes.items():
            qtd_user = itens_inv.get(ing_id, 0)
            if qtd_user < ing_qtd:
                ingredientes_ok = False
                faltando.append(f"{ing_id}: você tem {qtd_user}, precisa de {ing_qtd}")
        
        if not ingredientes_ok:
            embed = discord.Embed(
                title="❌ Ingredientes insuficientes",
                description="Você não tem todos os materiais necessários:\n\n" + "\n".join(faltando),
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Remover recursos
        for ing_id, ing_qtd in ingredientes.items():
            self.remove_item(interaction.user.id, ing_id, ing_qtd)
        self.remove_almas(interaction.user.id, custo)
        
        # Esperar um pouco para efeito dramático
        await asyncio.sleep(2)
        
        # Determinar sucesso
        sucesso = random.random() > taxa_falha
        
        if sucesso:
            # Adicionar arma
            self.add_item(interaction.user.id, item, 1)
            
            embed = discord.Embed(
                title="✨ FORJA BEM-SUCEDIDA! ✨",
                description=f"Você criou: **{emoji} {nome_arma}**",
                color=discord.Color.gold()
            )
            embed.add_field(name="Custo", value=f"{custo} almas", inline=True)
            embed.add_field(name="Taxa de Falha", value=f"{taxa_falha*100:.0f}%", inline=True)
            
        else:
            embed = discord.Embed(
                title="💥 FALHA NA FORJA! 💥",
                description=f"A forja de **{nome_arma}** falhou e seus materiais foram perdidos!",
                color=discord.Color.red()
            )
            embed.add_field(name="Taxa de Falha", value=f"{taxa_falha*100:.0f}%", inline=False)
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="inventario", description="Veja seu inventário")
    async def inventario(self, interaction: discord.Interaction):
        """Mostra inventário do usuário"""
        economia = self.load_json(self.economia_file)
        user_inv = self.get_user_inventory(interaction.user.id)
        
        itens = user_inv.get("itens", {})
        almas = user_inv.get("almas", 0)
        
        if not itens:
            embed = discord.Embed(
                title="📦 Seu Inventário",
                description="Seu inventário está vazio",
                color=0x9B59B6
            )
            embed.add_field(name="Almas", value=f"{almas}", inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Organizar itens por raridade
        itens_por_raridade = {}
        
        # Procurar em todas as categorias
        for categoria in ["itens_craft", "itens_forja", "itens_passivos", "loja_items"]:
            cat_items = economia.get(categoria, {})
            for item_id, item_data in cat_items.items():
                if item_id in itens:
                    raridade = item_data.get("raridade", "comum")
                    if raridade not in itens_por_raridade:
                        itens_por_raridade[raridade] = []
                    
                    emoji = item_data.get("emoji", "⭐")
                    nome = item_data.get("nome", item_id)
                    qtd = itens[item_id]
                    equipado = "✅" if user_inv.get("equipados", {}).get(item_id) else ""
                    
                    itens_por_raridade[raridade].append(f"{emoji} **{nome}** x{qtd} {equipado}")
        
        embed = discord.Embed(
            title="📦 Seu Inventário",
            color=0x9B59B6
        )
        
        ordem_raridade = ["ancestral", "lendario", "epico", "raro", "comum"]
        
        for raridade in ordem_raridade:
            if raridade in itens_por_raridade:
                items_list = "\n".join(itens_por_raridade[raridade])
                embed.add_field(
                    name=f"{'⭐' if raridade == 'ancestral' else '🟡' if raridade == 'lendario' else '🟣'} {raridade.upper()}",
                    value=items_list,
                    inline=False
                )
        
        embed.add_field(name="💜 Almas", value=f"**{almas}**", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=False)
    
    @app_commands.command(name="vender", description="Venda um item para a loja")
    @app_commands.describe(item="ID do item para vender", quantidade="Quantidade (padrão: 1)")
    async def vender(self, interaction: discord.Interaction, item: str, quantidade: int = 1):
        """Vende um item para a loja"""
        economia = self.load_json(self.economia_file)
        user_inv = self.get_user_inventory(interaction.user.id)
        itens_inv = user_inv.get("itens", {})
        
        # Procurar item em todas as categorias
        item_data = None
        valor_unitario = 0
        
        for categoria in ["itens_craft", "itens_forja", "itens_passivos", "loja_items"]:
            cat_items = economia.get(categoria, {})
            if item in cat_items:
                item_data = cat_items[item]
                raridade = item_data.get("raridade", "comum")
                valor_base = item_data.get("valor_base", item_data.get("valor", 0))
                multiplicador = economia.get("raridades", {}).get(raridade, {}).get("valor_multiplicador", 1.0)
                valor_unitario = int(valor_base * multiplicador * 0.7)  # 70% do valor
                break
        
        if not item_data:
            await interaction.response.send_message("❌ Item não encontrado!", ephemeral=True)
            return
        
        if item not in itens_inv or itens_inv[item] < quantidade:
            await interaction.response.send_message(
                f"❌ Você não tem {quantidade}x desse item!",
                ephemeral=True
            )
            return
        
        valor_total = valor_unitario * quantidade
        
        # Fazer venda
        self.remove_item(interaction.user.id, item, quantidade)
        self.add_almas(interaction.user.id, valor_total)
        
        emoji = item_data.get("emoji", "⭐")
        nome = item_data.get("nome", item)
        
        embed = discord.Embed(
            title="✅ Venda realizada!",
            description=f"Você vendeu **{quantidade}x** {emoji} **{nome}**",
            color=discord.Color.green()
        )
        embed.add_field(name="Valor unitário", value=f"{valor_unitario} almas", inline=True)
        embed.add_field(name="Valor total", value=f"{valor_total} almas", inline=True)
        embed.set_footer(text="Você recebeu 70% do valor base do item")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="mercado", description="Sistema de mercado entre players")
    async def mercado(self, interaction: discord.Interaction):
        """Mercado entre players (em desenvolvimento)"""
        embed = discord.Embed(
            title="🏪 Mercado Global",
            description="""
**Mercado em desenvolvimento!**

Este será um sistema onde você pode:
- 📤 Colocar itens à venda
- 📥 Comprar itens de outros players
- 💰 Negociar preços
- 📊 Ver histórico de vendas

**Funcionalidades:**
- Taxa de imposto: 5% das vendas
- Sistema de oferta/contra-oferta
- Ranking de vendedores
- Histórico de transações
            """,
            color=0x2ECC71
        )
        embed.set_footer(text="Volte em breve!")
        
        await interaction.response.send_message(embed=embed, ephemeral=False)
    
    @app_commands.command(name="ranking", description="Veja o ranking de almas")
    async def ranking(self, interaction: discord.Interaction):
        """Mostra ranking de almas"""
        await interaction.response.defer()
        
        inventario = self.load_json(self.inventario_file)
        usuarios = inventario.get("usuarios", {})
        
        # Ordenar por almas
        ranking = sorted(
            usuarios.items(),
            key=lambda x: x[1].get("almas", 0),
            reverse=True
        )[:10]
        
        embed = discord.Embed(
            title="🏆 Ranking de Almas",
            description="Top 10 mais ricos",
            color=0xFFD700
        )
        
        for idx, (user_id, user_data) in enumerate(ranking, 1):
            almas = user_data.get("almas", 0)
            
            try:
                user = await self.bot.fetch_user(int(user_id))
                nome = user.name
            except:
                nome = f"User {user_id}"
            
            medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"#{idx}"
            embed.add_field(
                name=f"{medal} {nome}",
                value=f"**{almas:,}** almas",
                inline=False
            )
        
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Loja(bot))
