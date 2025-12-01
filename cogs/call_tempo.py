import discord
from discord.ext import commands, tasks
import time
import asyncio

class VoiceChannelTimer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_channels = {}  # {channel_id: start_time}
        self.update_channel_names.start()

    def format_time(self, seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        sec = seconds % 60
        return f"{hours}:{minutes:02d}:{sec:02d}"

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):

        # Entrou em um canal
        if before.channel is None and after.channel is not None:
            channel = after.channel

            # Se o canal ainda não está sendo contado, inicia
            if channel.id not in self.active_channels:
                self.active_channels[channel.id] = int(time.time())

        # Saiu de um canal
        if before.channel is not None and after.channel is None:
            channel = before.channel

            # Se ficou vazio, remove o contador
            if len(channel.members) == 0:
                if channel.id in self.active_channels:
                    del self.active_channels[channel.id]
                # Volta nome ao original
                try:
                    await channel.edit(name=channel.name.split(" —")[0])
                except:
                    pass

    @tasks.loop(seconds=5)  # atualiza a cada 5 segundos
    async def update_channel_names(self):
        for channel_id, start_time in list(self.active_channels.items()):
            channel = self.bot.get_channel(channel_id)

            if channel and isinstance(channel, discord.VoiceChannel):
                elapsed = int(time.time()) - start_time
                formatted = self.format_time(elapsed)

                base_name = channel.name.split(" —")[0]  # nome original sem timer

                try:
                    await channel.edit(name=f"{base_name} — {formatted}")
                except discord.Forbidden:
                    pass
                except Exception as e:
                    print("Erro ao editar canal:", e)

    @update_channel_names.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(VoiceChannelTimer(bot))