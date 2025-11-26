# casamento.py

import discord
import discord
from discord.ext import commands
from discord import app_commands
from discord import app_commands
from discord.ext import commands
import datetime
class CasamentoButtons(discord.ui.View):
    def __init__(self, proposer: discord.Member, target: discord.Member, bot):
        super().__init__(timeout=300)  # 5 minutos para responder
        self.proposer = proposer
        self.target = target
        self.bot = bot

    @discord.ui.button(label="💍 Aceitar", style=discord.ButtonStyle.success)
    async def aceitar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target.id:
            await interaction.response.send_message(
                "❌ Apenas a pessoa que recebeu o pedido pode aceitar!",
                ephemeral=True
            )
            return

        db = self.bot.db()
        proposer_id = str(self.proposer.id)
        target_id = str(self.target.id)

        # Garantir que os usuários existem no DB
        if proposer_id not in db:
            db[proposer_id] = {
                "sobre": None,
                "tempo_total": 0,
                "soul": 0,
                "xp": 0,
                "level": 1
            }
        if target_id not in db:
            db[target_id] = {
                "sobre": None,
                "tempo_total": 0,
                "soul": 0,
                "xp": 0,
                "level": 1
            }

        # Verificar se algum dos dois já está casado
        if db[proposer_id].get("casado_com"):
            casado_com_id = db[proposer_id].get("casado_com")
            try:
                casado_com_user = await self.bot.fetch_user(int(casado_com_id))
                await interaction.response.send_message(
                    f"❌ {self.proposer.mention} já está casado(a) com {casado_com_user.mention}!",
                    ephemeral=True
                )
            except:
                await interaction.response.send_message(
                    f"❌ {self.proposer.mention} já está casado(a)!",
                    ephemeral=True
                )
            return

        if db[target_id].get("casado_com"):
            casado_com_id = db[target_id].get("casado_com")
            try:
                casado_com_user = await self.bot.fetch_user(int(casado_com_id))
                await interaction.response.send_message(
                    f"❌ Você já está casado(a) com {casado_com_user.mention}!",
                    ephemeral=True
                )
            except:
                await interaction.response.send_message(
                    f"❌ Você já está casado(a)!",
                    ephemeral=True
                )
            return

        # Salvar o casamento
        db[proposer_id]["casado_com"] = target_id
        db[target_id]["casado_com"] = proposer_id
        self.bot.save_db(db)

        # Embed de sucesso
        embed = discord.Embed(
            title="💍 Casamento Realizado!",
            description=f"**{self.proposer.mention}** e **{self.target.mention}** estão agora casados! 💕",
            color=discord.Color.pink()
        )
        embed.set_image(url="https://i.imgur.com/4M7IWwP.gif")  # GIF de corações (pode trocar)
        embed.set_footer(text="Aeternum Exilium • Sistema de Casamento")
        embed.timestamp = datetime.datetime.now()

        # Desabilitar os botões
        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(embed=embed, view=self)
        
        # Enviar mensagem no canal
        await interaction.channel.send(embed=embed)

    @discord.ui.button(label="❌ Recusar", style=discord.ButtonStyle.danger)
    async def recusar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target.id:
            await interaction.response.send_message(
                "❌ Apenas a pessoa que recebeu o pedido pode recusar!",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="💔 Pedido Recusado",
            description=f"{self.target.mention} recusou o pedido de casamento de {self.proposer.mention}.",
            color=discord.Color.red()
        )
        embed.set_footer(text="Aeternum Exilium • Sistema de Casamento")

        # Desabilitar os botões
        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        # Desabilitar botões quando o tempo acabar
        for item in self.children:
            item.disabled = True
        # Tentar editar a mensagem se ainda existir
        try:
            embed = discord.Embed(
                title="⏰ Tempo Esgotado",
                description=f"O pedido de casamento expirou.",
                color=discord.Color.orange()
            )
            await self.message.edit(embed=embed, view=self)
        except:
            pass


class Casamento(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_unload(self):
        try:
            self.bot.tree.remove_command(self.casar.name, type=self.casar.type)
        except:
            pass
        try:
            self.bot.tree.remove_command(self.divorciar.name, type=self.divorciar.type)
        except:
            pass

    @app_commands.command(name="casar", description="Peça alguém em casamento!")
    @app_commands.describe(pessoa="A pessoa que você quer casar")
    async def casar(self, interaction: discord.Interaction, pessoa: discord.Member):
        # Verificar se está tentando casar consigo mesmo
        if pessoa.id == interaction.user.id:
            await interaction.response.send_message(
                "❌ Você não pode casar consigo mesmo!",
                ephemeral=True
            )
            return

        # Verificar se está tentando casar com um bot
        if pessoa.bot:
            await interaction.response.send_message(
                "❌ Você não pode casar com um bot!",
                ephemeral=True
            )
            return

        db = self.bot.db()
        proposer_id = str(interaction.user.id)
        target_id = str(pessoa.id)

        # Garantir que os usuários existem no DB
        if proposer_id not in db:
            db[proposer_id] = {
                "sobre": None,
                "tempo_total": 0,
                "soul": 0,
                "xp": 0,
                "level": 1
            }
        if target_id not in db:
            db[target_id] = {
                "sobre": None,
                "tempo_total": 0,
                "soul": 0,
                "xp": 0,
                "level": 1
            }
        self.bot.save_db(db)

        # Verificar se o proposer já está casado
        if db[proposer_id].get("casado_com"):
            casado_com_id = db[proposer_id].get("casado_com")
            try:
                casado_com_user = await self.bot.fetch_user(int(casado_com_id))
                await interaction.response.send_message(
                    f"❌ Você já está casado(a) com {casado_com_user.mention}!",
                    ephemeral=True
                )
            except:
                await interaction.response.send_message(
                    f"❌ Você já está casado(a)!",
                    ephemeral=True
                )
            return

        # Verificar se o alvo já está casado
        if db[target_id].get("casado_com"):
            casado_com_id = db[target_id].get("casado_com")
            try:
                casado_com_user = await self.bot.fetch_user(int(casado_com_id))
                await interaction.response.send_message(
                    f"❌ {pessoa.mention} já está casado(a) com {casado_com_user.mention}!",
                    ephemeral=True
                )
            except:
                await interaction.response.send_message(
                    f"❌ {pessoa.mention} já está casado(a)!",
                    ephemeral=True
                )
            return

        # Criar embed bonito do pedido
        embed = discord.Embed(
            title="💍 Pedido de Casamento",
            description=f"{interaction.user.mention} está pedindo {pessoa.mention} em casamento! 💕\n\n"
                        f"**{pessoa.display_name}**, você aceita este pedido?",
            color=discord.Color.pink()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_image(url="https://i.imgur.com/4M7IWwP.gif")  # GIF de corações (pode trocar)
        embed.set_footer(text="Aeternum Exilium • Sistema de Casamento • Expira em 5 minutos")
        embed.timestamp = datetime.datetime.now()

        view = CasamentoButtons(interaction.user, pessoa, self.bot)
        
        # Deferir para ocultar o uso do comando
        await interaction.response.defer(thinking=False, ephemeral=True)
        
        # Enviar a mensagem no canal
        msg = await interaction.channel.send(embed=embed, view=view)
        view.message = msg

    @app_commands.command(name="divorciar", description="Divorcie-se de seu parceiro(a)")
    async def divorciar(self, interaction: discord.Interaction):
        db = self.bot.db()
        user_id = str(interaction.user.id)

        if user_id not in db or not db[user_id].get("casado_com"):
            await interaction.response.send_message(
                "❌ Você não está casado(a)!",
                ephemeral=True
            )
            return

        casado_com_id = db[user_id].get("casado_com")
        
        # Remover casamento de ambos
        db[user_id]["casado_com"] = None
        if casado_com_id in db:
            db[casado_com_id]["casado_com"] = None
        self.bot.save_db(db)

        try:
            ex_parceiro = await self.bot.fetch_user(int(casado_com_id))
            await interaction.response.send_message(
                f"💔 Você se divorciou de {ex_parceiro.mention}.",
                ephemeral=True
            )
        except:
            await interaction.response.send_message(
                f"💔 Você se divorciou.",
                ephemeral=True
            )


async def setup(bot):
    # Verificar se o cog já foi carregado
    if bot.get_cog("Casamento"):
        print("Cog Casamento já está carregado, pulando...")
        return
    
    # Remover comandos se já existirem
    for cmd_name in ["casar", "divorciar"]:
        existing = bot.tree.get_command(cmd_name)
        if existing:
            try:
                bot.tree.remove_command(cmd_name)
            except:
                pass
    
    cog = Casamento(bot)
    await bot.add_cog(cog)
    
    # Adicionar comandos
    try:
        bot.tree.add_command(cog.casar)
    except Exception as e:
        # Se já estiver registrado, apenas avisar mas continuar
        if "already registered" in str(e).lower():
            print(f"Comando 'casar' já está registrado, continuando...")
        else:
            raise e
    
    try:
        bot.tree.add_command(cog.divorciar)
    except Exception as e:
        # Se já estiver registrado, apenas avisar mas continuar
        if "already registered" in str(e).lower():
            print(f"Comando 'divorciar' já está registrado, continuando...")
        else:
            raise e

