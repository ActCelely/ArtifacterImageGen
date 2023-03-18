import discord
from discord.ext import commands

import os
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("token")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

bot.load_extension("cogs.genshin")


@bot.event
async def on_ready():
    print("Ready")


@bot.command()
async def reload(ctx, cog):
    bot.reload_extension(cog)
    await ctx.send("reloaded")

bot.run(token=TOKEN)