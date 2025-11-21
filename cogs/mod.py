import discord
from discord.ext import commands
import asyncio
import datetime
from typing import Optional


def parse_duration(text: str) -> Optional[int]:
    """Parse strings like '10s', '5m', '2h', '1d' into seconds."""
    if not text:
        return None
    unit = text[-1].lower()
    try:
        value = int(text[:-1])
    except ValueError:
        # maybe seconds given as number
        try:
            return int(text)
        except ValueError:
            return None

    if unit == 's':
        return value
    if unit == 'm':
        return value * 60
    if unit == 'h':
        return value * 3600
    if unit == 'd':
        return value * 86400
    return None


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ---------- Helpers ----------
    def check_admin(self, ctx: commands.Context) -> bool:
        return ctx.author.guild_permissions.manage_guild or ctx.author.guild_permissions.manage_roles

    async def _timed_unmute(self, guild: discord.Guild, member: discord.Member, delay: int):
        await asyncio.sleep(delay)
        mute_role = discord.utils.get(guild.roles, name="Muted")
        try:
            if mute_role and mute_role in member.roles:
                await member.remove_roles(mute_role, reason="Mute temporário expirado")
        except Exception:
            pass

    async def _timed_remove_role(self, guild: discord.Guild, member_id: int, role: discord.Role, delay: int):
        """Remove um role de um membro após `delay` segundos se ainda existir."""
        await asyncio.sleep(delay)
        try:
            member = guild.get_member(member_id)
            if not member:
                return
            if role in member.roles:
                await member.remove_roles(role, reason="Tempo de role expirado")
        except Exception:
            pass

    # ---------- Comandos gerais ----------
    @commands.command(name="tempo")
    async def cmd_tempo(self, ctx, member: Optional[discord.Member] = None):
        """sprt!tempo - mostra tempo em call do membro (ou autor)"""
        member = member or ctx.author
        if member.id in self.bot.active_users:
            start = self.bot.call_times.get(member.id, datetime.datetime.now())
            elapsed = int((datetime.datetime.now() - start).total_seconds())
            hours, remainder = divmod(elapsed, 3600)
            minutes, seconds = divmod(remainder, 60)
            await ctx.send(f"⏱️ {member.display_name} está em call há {hours}h {minutes}m {seconds}s")
        else:
            await ctx.send(f"❌ {member.display_name} não está em call")

    @commands.command(name="help")
    @commands.has_permissions(manage_guild=True)
    async def cmd_help(self, ctx: commands.Context):
        """sprt!help - Lista de comandos de moderação com uso e permissões necessárias."""
        embed = discord.Embed(
            title="🛡️ Painel de Moderação — Comandos (prefixo `sprt!`)",
            color=discord.Color.blurple()
        )
        embed.add_field(name="`sprt!tempo [@membro]`", value="Mostra tempo em call do membro (ou autor).", inline=False)
        embed.add_field(name="`sprt!addcargo @membro @cargo [tempo]`", value="Adiciona um cargo existente; opcionalmente remove após duração (s/m/h/d).", inline=False)
        embed.add_field(name="`sprt!removercargo @membro @cargo`", value="Remove um cargo existente do membro.", inline=False)
        embed.add_field(name="`sprt!criarcargo @membro NomeDoCargo`", value="Cria um cargo (se não existir) e adiciona ao membro.", inline=False)
        embed.add_field(name="`sprt!deletecargo @membro @cargo|Nome`", value="Remove cargo do membro; se ficar vazio, deleta o cargo.", inline=False)
        # Nota: comandos de mute em chat foram removidos — use moderação manualmente
        embed.add_field(name="`sprt!mutecall @membro [tempo] [motivo]`", value="Mute em voice (requer permissão de Mute Members).", inline=False)
        embed.add_field(name="`sprt!unmutecall @membro`", value="Desmuta em voice.", inline=False)
        embed.add_field(name="`sprt!prender @membro [tempo] [motivo]`", value="Move para canal 'Prisão' e muta/deafen (requer Move Members).", inline=False)
        embed.add_field(name="`sprt!soltar @membro`", value="Desmuta/deaf do membro e libera.", inline=False)
        embed.add_field(name="`sprt!ban @membro [motivo]`", value="Bane permanentemente o membro (requer Ban Members).", inline=False)
        embed.add_field(name="`sprt!unban <user_id> [motivo]`", value="Remove ban pelo ID do usuário.", inline=False)
        embed.set_footer(text="Use com responsabilidade — requer permissões administrativas.")
        await ctx.send(embed=embed)

    @commands.command(name="addcargo")
    @commands.has_permissions(manage_roles=True)
    async def cmd_addcargo(self, ctx, member: discord.Member, role: discord.Role, duration: Optional[str] = None):
        """sprt!addcargo @membro @cargo [10m] - adiciona um cargo existente ao membro; opcionalmente remove após tempo"""
        if role not in ctx.guild.roles:
            return await ctx.send("❌ Cargo não pertence a este servidor.")
        try:
            await member.add_roles(role, reason=f"Adicionado por {ctx.author}")
            await ctx.send(f"✅ Cargo `{role.name}` adicionado a {member.mention}")
        except discord.Forbidden:
            return await ctx.send("❌ Não tenho permissão para gerenciar cargos neste membro.")

        # Se foi passada uma duração, agendar remoção do cargo
        if duration:
            secs = parse_duration(duration)
            if not secs:
                return await ctx.send("❌ Duração inválida. Use s/m/h/d (ex: 10m).")
            # agendar a remoção em background
            try:
                asyncio.create_task(self._timed_remove_role(ctx.guild, member.id, role, secs))
                await ctx.send(f"⏳ O cargo `{role.name}` será removido de {member.mention} em {duration}.")
            except Exception:
                await ctx.send("⚠️ Falha ao agendar remoção do cargo.")

    @commands.command(name="removercargo")
    @commands.has_permissions(manage_roles=True)
    async def cmd_removercargo(self, ctx, member: discord.Member, role: discord.Role):
        """sprt!removercargo @membro @cargo - remove um cargo existente do membro"""
        if role not in ctx.guild.roles:
            return await ctx.send("❌ Cargo não pertence a este servidor.")
        try:
            await member.remove_roles(role, reason=f"Removido por {ctx.author}")
            await ctx.send(f"✅ Cargo `{role.name}` removido de {member.mention}")
        except discord.Forbidden:
            await ctx.send("❌ Não tenho permissão para gerenciar cargos neste membro.")

    # Helper to resolve role from mention or name
    def _resolve_role(self, guild: discord.Guild, role_arg: str) -> Optional[discord.Role]:
        """Tenta resolver um role a partir de uma menção (<@&id>) ou por nome exato."""
        if not role_arg:
            return None
        role = None
        # menção do role: <@&ID>
        if role_arg.startswith("<@&") and role_arg.endswith(">"):
            try:
                rid = int(role_arg[3:-1])
            except ValueError:
                rid = None
            if rid:
                role = discord.utils.get(guild.roles, id=rid)
                if role:
                    return role

        # tentar por nome exato
        role = discord.utils.get(guild.roles, name=role_arg)
        if role:
            return role

        # tentar remover acentos/trim e procurar
        cleaned = role_arg.strip()
        role = discord.utils.get(guild.roles, name=cleaned)
        return role

    @commands.command(name="criarcargo")
    @commands.has_permissions(manage_roles=True)
    async def cmd_criarcargo(self, ctx, member: discord.Member, *, role_arg: str):
        """sprt!criarcargo @membro NomeDoCargo - cria um cargo (se não existir) e adiciona ao membro
        Aceita também menção de cargo se já existir."""
        guild = ctx.guild
        if not role_arg:
            return await ctx.send("❌ Especifique o nome do cargo ou mencione o cargo.")

        # tentar resolver role existente
        role = self._resolve_role(guild, role_arg)
        if not role:
            # criar novo role com o nome fornecido
            try:
                role = await guild.create_role(name=role_arg)
            except discord.Forbidden:
                return await ctx.send("❌ Não tenho permissão para criar cargos neste servidor.")

        try:
            await member.add_roles(role, reason=f"Criado/adicionado por {ctx.author}")
            await ctx.send(f"✅ Cargo `{role.name}` aplicado a {member.mention}")
        except discord.Forbidden:
            await ctx.send("❌ Não tenho permissão para gerenciar cargos neste membro.")

    @commands.command(name="deletecargo")
    @commands.has_permissions(manage_roles=True)
    async def cmd_deletecargo(self, ctx, member: discord.Member, *, role_arg: str):
        """sprt!deletecargo @membro @cargoouNome - remove um cargo do membro; se o cargo ficar vazio, deleta-o"""
        guild = ctx.guild
        role = self._resolve_role(guild, role_arg)
        if not role:
            return await ctx.send("❌ Cargo não encontrado neste servidor.")

        try:
            # remover do membro
            if role in member.roles:
                await member.remove_roles(role, reason=f"Removido por {ctx.author}")
                await ctx.send(f"✅ Cargo `{role.name}` removido de {member.mention}")
            else:
                await ctx.send(f"⚠️ {member.mention} não possuía o cargo `{role.name}`")

            # se cargo está vazio agora, deletar
            # precisa buscar cargo atualizado
            if len(role.members) == 0:
                try:
                    await role.delete(reason=f"Deletado por {ctx.author} via deletecargo")
                    await ctx.send(f"🗑️ Cargo `{role.name}` estava vazio e foi deletado.")
                except discord.Forbidden:
                    await ctx.send("⚠️ Removido do membro, mas não tenho permissão para deletar o cargo.")
        except discord.Forbidden:
            await ctx.send("❌ Não tenho permissão para gerenciar cargos neste membro.")

    # ---------- Punições em chat ----------
    # NOTE: comandos de mute/unmute em chat foram removidos por solicitação.

    # ---------- Punições em call ----------
    @commands.command(name="mutecall")
    @commands.has_permissions(mute_members=True)
    async def cmd_mutecall(self, ctx, member: discord.Member, duration: str = None, *, reason: str = "Sem motivo"):
        if not member.voice or not member.voice.channel:
            return await ctx.send("❌ Membro não está em um canal de voz.")
        try:
            await member.edit(mute=True, reason=reason)
            await ctx.send(f"🔇 {member.mention} foi mutado na call. Motivo: {reason}")
        except discord.Forbidden:
            return await ctx.send("❌ Não tenho permissão para mutar membros em voice.")

        if duration:
            secs = parse_duration(duration)
            if secs:
                async def _unmute_after():
                    await asyncio.sleep(secs)
                    try:
                        await member.edit(mute=False, reason="Tempo de mute expirado")
                    except Exception:
                        pass
                asyncio.create_task(_unmute_after())

    @commands.command(name="unmutecall")
    @commands.has_permissions(mute_members=True)
    async def cmd_unmutecall(self, ctx, member: discord.Member, *, reason: str = "Fim do mute"):
        if not member.voice or not member.voice.channel:
            return await ctx.send("❌ Membro não está em um canal de voz.")
        try:
            await member.edit(mute=False, reason=reason)
            await ctx.send(f"🔊 {member.mention} foi desmutado na call.")
        except discord.Forbidden:
            await ctx.send("❌ Não tenho permissão para desmutar membros em voice.")

    @commands.command(name="prender")
    @commands.has_permissions(move_members=True)
    async def cmd_prender(self, ctx, member: discord.Member, duration: str = None, *, reason: str = "Sem motivo"):
        """Move o membro para um canal 'Prisão' e impede falar (muda mute/deaf)."""
        guild = ctx.guild
        prison_name = "Prisão"
        prison = discord.utils.get(guild.voice_channels, name=prison_name)
        try:
            if not prison:
                prison = await guild.create_voice_channel(prison_name)
            if member.voice and member.voice.channel:
                await member.move_to(prison, reason=reason)
            await member.edit(mute=True, deafen=True, reason=reason)
            await ctx.send(f"🔒 {member.mention} foi preso. Motivo: {reason}")
        except discord.Forbidden:
            await ctx.send("❌ Não tenho permissão para mover/mutar membros.")

        if duration:
            secs = parse_duration(duration)
            if secs:
                async def _release_after():
                    await asyncio.sleep(secs)
                    try:
                        await member.edit(mute=False, deafen=False, reason="Tempo de prisão expirado")
                    except Exception:
                        pass
                asyncio.create_task(_release_after())

    @commands.command(name="soltar")
    @commands.has_permissions(move_members=True)
    async def cmd_soltar(self, ctx, member: discord.Member, *, reason: str = "Solto"):
        try:
            await member.edit(mute=False, deafen=False, reason=reason)
            await ctx.send(f"✅ {member.mention} foi solto.")
        except discord.Forbidden:
            await ctx.send("❌ Não tenho permissão para desmutar/desdeafen membros.")

    # ---------- Permanente ----------
    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def cmd_ban(self, ctx, member: discord.Member, *, reason: str = None):
        try:
            await ctx.guild.ban(member, reason=reason)
            await ctx.send(f"⛔ {member.mention} foi banido. Motivo: {reason}")
        except discord.Forbidden:
            await ctx.send("❌ Não tenho permissão para banir este membro.")

    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def cmd_unban(self, ctx, user_id: int, *, reason: str = None):
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=reason)
            await ctx.send(f"✅ {user} foi desbanido. Motivo: {reason}")
        except discord.NotFound:
            await ctx.send("❌ Usuário não encontrado nos bans.")
        except discord.Forbidden:
            await ctx.send("❌ Não tenho permissão para desbanir.")


async def setup(bot):
    await bot.add_cog(Moderation(bot))
