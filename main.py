import asyncio
import logging
import traceback

import discord
from discord.ext import commands
from typing import Literal, Optional

bot = commands.Bot(command_prefix='cof?', intents=discord.Intents(messages=True, message_content=True))
log_handler = logging.FileHandler(filename='cofbot.log', encoding='utf-8', mode='w')


@bot.event
async def on_ready():
    print('Bot is ready.')


@bot.command()
async def ping(ctx):
    await ctx.send('Quack!')


@bot.command()
@commands.guild_only()
@commands.is_owner()
async def sync(
        ctx: commands.Context,
        guilds: commands.Greedy[discord.Object],
        spec: Optional[Literal["~", "*", "^"]] = None
) -> None:
    if not guilds:
        if spec == "~":
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "*":
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "^":
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            synced = []
        else:
            synced = await ctx.bot.tree.sync()

        await ctx.send(
            f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
        )
        return

    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)
        except discord.HTTPException:
            pass
        else:
            ret += 1

    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")


async def load_extensions():
    try:
        await bot.load_extension('triggers')
    except Exception as e:
        print(f"An error has occurred while loading extensions: {e}")
        traceback.print_exc()
        exit(1)


async def main():
    await load_extensions()

asyncio.run(main())
with open('cofbot_token', 'r') as f:
    bot.run(f.read().strip(), log_handler=log_handler)
