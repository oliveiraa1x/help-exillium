import discord
import json
from pathlib import Path
from discord import app_commands
from discord.ext import commands


class Inventario(commands.Cog):
    """Sistema de Inventário e Gerenciamento de Items"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_path = Path("data")
        self.inventario_file = self.data_path / "inventario.json"
        self.economia_file = self.data_path / "economia.json"
    
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
        """Obtém inventário do usuário ou cria novo"""
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
        return True
    
    def remove_item(self, user_id: str, item_id: str, quantidade: int = 1) -> bool:
        """Remove item do inventário se existir em quantidade suficiente"""
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
    
    def equip_item(self, user_id: str, item_id: str) -> bool:
        """Equipa um item passivo"""
        inventario = self.load_json(self.inventario_file)
        user_id_str = str(user_id)
        user_inv = self.get_user_inventory(user_id)
        
        if item_id in user_inv["itens"] and user_inv["itens"][item_id] > 0:
            user_inv["equipados"][item_id] = True
            inventario["usuarios"][user_id_str] = user_inv
            self.save_json(self.inventario_file, inventario)
            return True
        return False
    
    def unequip_item(self, user_id: str, item_id: str) -> bool:
        """Desequipa um item"""
        inventario = self.load_json(self.inventario_file)
        user_id_str = str(user_id)
        user_inv = self.get_user_inventory(user_id)
        
        if item_id in user_inv["equipados"]:
            del user_inv["equipados"][item_id]
            inventario["usuarios"][user_id_str] = user_inv
            self.save_json(self.inventario_file, inventario)
            return True
        return False
    
    def get_almas(self, user_id: str) -> int:
        """Obtém quantidade de almas do usuário"""
        user_inv = self.get_user_inventory(user_id)
        return user_inv.get("almas", 0)
    
    def add_almas(self, user_id: str, quantidade: int):
        """Adiciona almas ao usuário"""
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
    
    def get_cor_embed(self, raridade: str) -> int:
        """Retorna cor do embed baseado na raridade"""
        cores = {
            "comum": 0x4A4A4A,
            "raro": 0x0099FF,
            "epico": 0x9933FF,
            "lendario": 0xFFD700,
            "ancestral": 0xFF4500
        }
        return cores.get(raridade, 0x808080)
    
    # ==================== COMANDOS ====================
    
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
            embed.add_field(name="💜 Almas", value=f"**{almas:,}**", inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Organizar itens por raridade
        itens_por_raridade = {}
        
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
                raridade_display = {
                    "ancestral": "🔴 ANCESTRAL",
                    "lendario": "🟡 LENDÁRIO",
                    "epico": "🟣 ÉPICO",
                    "raro": "🔵 RARO",
                    "comum": "⚪ COMUM"
                }
                embed.add_field(
                    name=raridade_display.get(raridade, raridade.upper()),
                    value=items_list,
                    inline=False
                )
        
        embed.add_field(name="💜 Almas", value=f"**{almas:,}**", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="equipar", description="Equipe um item passivo")
    @app_commands.describe(item="ID do item para equipar")
    async def equipar(self, interaction: discord.Interaction, item: str):
        """Equipa um item passivo"""
        economia = self.load_json(self.economia_file)
        
        # Procurar item em passivos
        passivos = economia.get("itens_passivos", {})
        if item not in passivos:
            await interaction.response.send_message(
                "❌ Item não é um equipável válido!",
                ephemeral=True
            )
            return
        
        if self.equip_item(interaction.user.id, item):
            item_data = passivos[item]
            emoji = item_data.get("emoji", "⭐")
            nome = item_data.get("nome", item)
            
            embed = discord.Embed(
                title="✅ Item Equipado!",
                description=f"Você equipou: {emoji} **{nome}**",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(
                "❌ Você não tem esse item!",
                ephemeral=True
            )
    
    @app_commands.command(name="desequipar", description="Remove um item equipado")
    @app_commands.describe(item="ID do item para remover")
    async def desequipar(self, interaction: discord.Interaction, item: str):
        """Desequipa um item"""
        economia = self.load_json(self.economia_file)
        passivos = economia.get("itens_passivos", {})
        
        if self.unequip_item(interaction.user.id, item):
            item_data = passivos.get(item, {})
            emoji = item_data.get("emoji", "⭐")
            nome = item_data.get("nome", item)
            
            embed = discord.Embed(
                title="✅ Item Desequipado!",
                description=f"Você desequipou: {emoji} **{nome}**",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(
                "❌ Você não tem esse item equipado!",
                ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(Inventario(bot))
