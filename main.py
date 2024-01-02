import asyncio

import discord
import peewee
from discord.ext import commands

bot = commands.Bot(command_prefix='cof?', intents=discord.Intents(messages=True, message_content=True))


@bot.event
async def on_ready():
    print('Bot is ready.')


@bot.command()
async def ping(ctx):
    await ctx.send('Quack!')


async def load_extensions():
    try:
        await bot.load_extension('triggers')
    except peewee.PeeweeException as e:
        print(f"An error has occurred while initializing the database: {e}")
        exit(1)


async def main():
    with open('cofbot_token', 'r') as f:
        await load_extensions()
        await bot.start(f.read().strip())

asyncio.run(main())
