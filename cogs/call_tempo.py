import discord
from discord.ext import commands
import json
import os
import time

DATA_FILE = "call_tempo.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def format_time(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    sec = seconds % 60
    return f"{hours}:{minutes:02d}:{sec:02d}"


class CallTempo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Detecta entrada/saída da call
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        data = load_data()

        # Entrou na call
        if before.channel is None and after.channel is not None:
            data[str(member.id)] = int(time.time())   # salva timestamp
            save_data(data)

        # Saiu da call
        elif before.channel is not None and after.channel is None:
            if str(member.id) in data:
                del data[str(member.id)]
                save_data(data)


    # Comando para ver o tempo em call
    @commands.command()
    async def tempo(self, ctx):
        data = load_data()

        user_id = str(ctx.author.id)

        if user_id not in data:
            return await ctx.send("❌ Você não está em uma call no momento.")

        seconds = int(time.time()) - data[user_id]
        formatted = format_time(seconds)

        await ctx.send(f"⏱️ Você está na call há **{formatted}**!")


async def setup(bot):
    await bot.add_cog(CallTempo(bot))
