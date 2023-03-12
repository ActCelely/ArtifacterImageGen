import discord
from discord.ext import commands
from Generater import test
from io import BytesIO

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
    with BytesIO() as buffer:
        img.save(buffer, "png")
        buffer.seek(0)
        file = discord.File(buffer, "image.png")
        await ctx.send(file = file)


bot.run(token = TOKEN)