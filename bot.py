import discord
from discord.ext import commands
from Generater import test

import os
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("token")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents = intents, help_command= None)

@bot.event
async def on_ready():
    print("Ready")

@bot.command()
async def c(ctx):
    img = test()
    file = discord.File(img)
    await ctx.send(file = file)


bot.run(token = TOKEN)