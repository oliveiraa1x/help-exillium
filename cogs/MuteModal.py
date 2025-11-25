import discord
from discord.ui import Modal, TextInput
import datetime
import json
import os

PUNICOES_ARQUIVO = "punicoes.json"


def load_punicoes():
    """Carrega punições do JSON."""
    if not os.path.exists(PUNICOES_ARQUIVO):
        return []
    try:
        with open(PUNICOES_ARQUIVO, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def save_punicoes(data):
    """Salva punições no JSON."""
    with open(PUNICOES_ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


class MuteModal(Modal):
    def __init__(self, bot):
        super().__init__(title="Aplicar Mute")
        self.bot = bot

        # CAMPOS
        self.member_field = TextInput(
            label="ID ou @ do membro",
            placeholder="123456789012345678",
            required=True,
            max_length=32
        )

        self.duration_field = TextInput(
            label="Duração (minutos)",
            placeholder="10",
            required=True,
            max_length=6
        )

        self.reason_field = TextInput(
            label="Motivo",
            style=discord.TextStyle.long,
            placeholder="Explique o motivo",
            required=True,
            max_length=250
        )

        self.add_item(self.member_field)
        self.add_item(self.duration_field)
        self.add_item(self.reason_field)

    async def on_submit(self, interaction: discord.Interaction):

        membro_str = self.member_field.value
        minutos = self.duration_field.value
        motivo = self.reason_field.value

        # PROCESSAR ID/MENÇÃO
        try:
            membro_id = (
                membro_str.replace("<@", "")
                .replace(">", "")
                .replace("!", "")
                .strip()
            )
            membro_id = int(membro_id)
        except:
            return await interaction.response.send_message(
                "❌ **ID ou menção inválida!**",
                ephemeral=True
            )

        membro = interaction.guild.get_member(membro_id)

        if membro is None:
            return await interaction.response.send_message(
                "❌ **Esse membro não está no servidor!**",
                ephemeral=True
            )

        # PROTEÇÕES
        if membro == interaction.user:
            return await interaction.response.send_message(
                "❌ Você não pode se mutar!", ephemeral=True
            )

        if membro == interaction.guild.owner:
            return await interaction.response.send_message(
                "❌ Não posso mutar o dono do servidor!", ephemeral=True
            )

        if membro.top_role >= interaction.user.top_role:
            return await interaction.response.send_message(
                "❌ Esse membro tem um cargo igual ou maior que o seu!",
                ephemeral=True
            )

        if membro.bot:
            return await interaction.response.send_message(
                "❌ Não é possível mutar bots!",
                ephemeral=True
            )

        # TEMPO
        try:
            minutos = int(minutos)
            if minutos <= 0:
                raise ValueError
        except:
            return await interaction.response.send_message(
                "❌ **Duração inválida! Use um número maior que 0.**",
                ephemeral=True
            )

        # ⏳ TEMPO FINAL – CORREÇÃO AQUI
        until_time = discord.utils.utcnow() + timedelta(minutes=minutos)

        # APLICAR TIMEOUT
        try:
            await membro.timeout(
                until=until_time,
                reason=motivo
            )
        except Exception as e:
            return await interaction.response.send_message(
                f"❌ Erro ao aplicar mute!\n```{e}```",
                ephemeral=True
            )

        # REGISTRO
        try:
            puni = load_punicoes()
            puni.append({
                "tipo": "mute",
                "membro": membro.id,
                "moderador": interaction.user.id,
                "motivo": motivo,
                "duracao_min": minutos,
                "data": datetime.datetime.now().isoformat()
            })
            save_punicoes(puni)
        except Exception as e:
            return await interaction.response.send_message(
                f"⚠️ Mute aplicado, mas não consegui registrar!\n```{e}```",
                ephemeral=True
            )

        # EMBED FINAL
        embed = discord.Embed(
            title="🔇 Mute Aplicado com Sucesso!",
            color=discord.Color.orange()
        )
        embed.add_field(name="👤 Membro", value=membro.mention, inline=False)
        embed.add_field(name="⏳ Tempo", value=f"{minutos} minutos", inline=False)
        embed.add_field(name="📝 Motivo", value=motivo, inline=False)
        embed.set_footer(text=f"Moderador: {interaction.user}")

        await interaction.response.send_message(embed=embed, ephemeral=True)
