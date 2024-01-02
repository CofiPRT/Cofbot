import discord
from discord.ext import commands

client = commands.Bot(command_prefix='cof?', intents=discord.Intents(messages=True, message_content=True))


@client.event
async def on_ready():
    print('Bot is ready.')


@client.command()
async def ping(ctx):
    await ctx.send('Quack!')

with open('cofbot_token', 'r') as f:
    client.run(f.read().strip())
