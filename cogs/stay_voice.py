import discord
from discord.ext import commands
from discord import app_commands

class StayVoice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot_voice_clients = {}  # {guild_id: voice_client}

    @app_commands.command(name="stay-voice", description="Conecta o bot ao seu canal de voz e mantém a conexão indefinidamente.")
    async def stay_voice(self, interaction: discord.Interaction):
        """
        Conecta o bot ao canal de voz do usuário
        """
        # Verificar se o usuário está em um canal de voz
        if not interaction.user.voice or not interaction.user.voice.channel:
            embed = discord.Embed(
                title="❌ Erro",
                description="Você precisa estar em um canal de voz para usar este comando!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        channel = interaction.user.voice.channel
        guild = interaction.guild

        # Verificar se o bot já está em um canal de voz no servidor
        if guild.id in self.bot_voice_clients:
            vc = self.bot_voice_clients[guild.id]
            if vc.is_connected():
                embed = discord.Embed(
                    title="⚠️ Bot já conectado",
                    description=f"O bot já está conectado em {vc.channel.mention}",
                    color=discord.Color.orange()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        try:
            # Conectar ao canal de voz
            vc = await channel.connect()
            self.bot_voice_clients[guild.id] = vc

            embed = discord.Embed(
                title="✅ Conectado!",
                description=f"Bot conectado ao canal {channel.mention} e permanecerá lá até ser desligado.",
                color=discord.Color.green()
            )
            embed.set_footer(text="Use /leave-voice para desconectar")
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Erro ao conectar",
                description=f"Não foi possível conectar ao canal: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="leave-voice", description="Desconecta o bot do canal de voz.")
    async def leave_voice(self, interaction: discord.Interaction):
        """
        Desconecta o bot do canal de voz
        """
        guild = interaction.guild

        if guild.id not in self.bot_voice_clients:
            embed = discord.Embed(
                title="❌ Erro",
                description="O bot não está conectado a nenhum canal de voz.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        vc = self.bot_voice_clients[guild.id]
        if vc.is_connected():
            await vc.disconnect()
            del self.bot_voice_clients[guild.id]

            embed = discord.Embed(
                title="✅ Desconectado",
                description="Bot desconectado do canal de voz.",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Erro",
                description="O bot não está conectado a nenhum canal de voz.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """
        Se o bot for desconectado manualmente, removê-lo do dicionário
        """
        if member.id == self.bot.user.id:
            # Bot saiu de um canal
            if before.channel and not after.channel:
                guild = before.channel.guild
                if guild.id in self.bot_voice_clients:
                    del self.bot_voice_clients[guild.id]

async def setup(bot):
    await bot.add_cog(StayVoice(bot))
