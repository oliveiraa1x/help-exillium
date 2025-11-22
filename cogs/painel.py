import discord
from discord.ext import commands
from datetime import timedelta   # <=== IMPORT CORRETO

LOG_CHANNEL_ID = 1421609844934443029  # <=== CANAL DE LOGS


class Painel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="painel")
    async def painel(self, ctx):
        embed = discord.Embed(
            title="🔧 Painel de Moderação",
            description="Escolha uma das ações abaixo:",
            color=discord.Color.red()
        )

        embed.add_field(name="⚠️ Advertência", value="Aplicar advertência em um membro.", inline=False)
        embed.add_field(name="🔇 Mute", value="Mutar um membro temporariamente.", inline=False)
        embed.add_field(name="👢 Kick", value="Expulsar um membro.", inline=False)
        embed.add_field(name="🔨 Ban", value="Banir um membro.", inline=False)

        embed.set_footer(text="Aeternum Exilium • Moderação")

        await ctx.send(embed=embed, view=PainelButtons(ctx.guild))


class PainelButtons(discord.ui.View):
    def __init__(self, guild):
        super().__init__(timeout=None)
        self.guild = guild

    @discord.ui.button(label="Advertência", style=discord.ButtonStyle.red)
    async def advert(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AdvertModal())

    @discord.ui.button(label="Aplicar Mute", style=discord.ButtonStyle.danger)
    async def mute(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(MuteModal())

    @discord.ui.button(label="Kick", style=discord.ButtonStyle.secondary)
    async def kick(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(KickModal())

    @discord.ui.button(label="Ban", style=discord.ButtonStyle.secondary)
    async def ban(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BanModal())


# =============================================================
#                       MODAIS (POP-UP)
# =============================================================

class AdvertModal(discord.ui.Modal, title="Aplicar Advertência"):
    user_id = discord.ui.TextInput(label="ID do usuário", placeholder="123456789012345678")
    reason = discord.ui.TextInput(label="Motivo", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):

        user = interaction.guild.get_member(int(self.user_id.value))

        if not user:
            return await interaction.response.send_message("❌ Usuário não encontrado.", ephemeral=True)

        await interaction.response.send_message(
            f"⚠️ **{user.mention} foi advertido.**\n📄 Motivo: `{self.reason.value}`",
            ephemeral=False
        )

        canal_logs = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if canal_logs:
            embed = discord.Embed(
                title="⚠️ Advertência Aplicada",
                color=discord.Color.orange()
            )
            embed.add_field(name="👤 Usuário", value=user.mention)
            embed.add_field(name="📝 Motivo", value=self.reason.value, inline=False)
            embed.add_field(name="🔧 Moderador", value=interaction.user.mention)
            await canal_logs.send(embed=embed)


# ------------------------ MUTE ------------------------
class MuteModal(discord.ui.Modal, title="Aplicar Mute"):
    user_id = discord.ui.TextInput(label="ID do usuário")
    duration = discord.ui.TextInput(label="Duração (ex: 10m, 2h, 1d)")
    reason = discord.ui.TextInput(label="Motivo", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):

        user = interaction.guild.get_member(int(self.user_id.value))
        if not user:
            return await interaction.response.send_message("❌ Usuário não encontrado.", ephemeral=True)

        tempo = self.duration.value.lower()
        mult = {"m": 60, "h": 3600, "d": 86400}

        try:
            segundos = int(tempo[:-1]) * mult.get(tempo[-1])
        except:
            return await interaction.response.send_message("❌ Formato inválido. Use ex: `10m`, `2h`, `1d`.", ephemeral=True)

        # Agora usando datetime CORRETO
        import datetime
        until_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=segundos)

        # Forma correta do timeout:
        await user.timeout(
            until_time,        # até quando
            self.reason.value  # motivo
        )

        await interaction.response.send_message(
            f"🔇 **{user.mention} foi mutado por `{self.duration.value}`**\n📄 Motivo: `{self.reason.value}`",
            ephemeral=False
        )

        # LOGS
        canal_logs = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if canal_logs:
            embed = discord.Embed(
                title="🔇 Membro Mutado",
                color=discord.Color.blue()
            )
            embed.add_field(name="👤 Usuário", value=user.mention)
            embed.add_field(name="⏳ Duração", value=self.duration.value)
            embed.add_field(name="📝 Motivo", value=self.reason.value, inline=False)
            embed.add_field(name="🔧 Moderador", value=interaction.user.mention)
            await canal_logs.send(embed=embed)



# ------------------------ KICK ------------------------
class KickModal(discord.ui.Modal, title="Expulsar Membro"):
    user_id = discord.ui.TextInput(label="ID do usuário")
    reason = discord.ui.TextInput(label="Motivo", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):

        user = interaction.guild.get_member(int(self.user_id.value))

        if not user:
            return await interaction.response.send_message("❌ Usuário não encontrado.", ephemeral=True)

        await user.kick(reason=self.reason.value)

        await interaction.response.send_message(
            f"👢 **{user.mention} foi expulso.**\n📄 Motivo: `{self.reason.value}`",
            ephemeral=False
        )

        canal_logs = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if canal_logs:
            embed = discord.Embed(
                title="👢 Membro Expulso",
                color=discord.Color.gold()
            )
            embed.add_field(name="👤 Usuário", value=user.mention)
            embed.add_field(name="📝 Motivo", value=self.reason.value)
            embed.add_field(name="🔧 Moderador", value=interaction.user.mention)
            await canal_logs.send(embed=embed)


# ------------------------ BAN ------------------------
class BanModal(discord.ui.Modal, title="Banir Membro"):
    user_id = discord.ui.TextInput(label="ID do usuário")
    reason = discord.ui.TextInput(label="Motivo", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):

        user = interaction.guild.get_member(int(self.user_id.value))

        if not user:
            return await interaction.response.send_message("❌ Usuário não encontrado.", ephemeral=True)

        await user.ban(reason=self.reason.value)

        await interaction.response.send_message(
            f"🔨 **{user.mention} foi banido.**\n📄 Motivo: `{self.reason.value}`",
            ephemeral=False
        )

        canal_logs = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if canal_logs:
            embed = discord.Embed(
                title="🔨 Membro Banido",
                color=discord.Color.red()
            )
            embed.add_field(name="👤 Usuário", value=user.mention)
            embed.add_field(name="📝 Motivo", value=self.reason.value)
            embed.add_field(name="🔧 Moderador", value=interaction.user.mention)
            await canal_logs.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Painel(bot))
