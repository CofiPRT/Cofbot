import re

import discord
from . import help_pages
from discord.ext import commands
from cofdb import db, BaseModel
from peewee import *
from utils import Pages


class TriggerEntity(BaseModel):
    mode = CharField()
    user_pattern = CharField()
    response = CharField()
    cooldown = IntegerField()
    ignore_case = BooleanField()
    uses_wildcards = BooleanField()

    # all triggers actually use regex in the background, computed upon being created or modified
    # this field is not exposed to the user
    regex_pattern = CharField()
    position = IntegerField()


class TriggerCog(commands.Cog):
    group = discord.app_commands.Group(name="triggers", description="Manage this server's triggers")

    def __init__(self, bot):
        self.bot = bot
        if not db.is_connection_usable():
            db.connect()
            db.create_tables([TriggerEntity])

        self.triggers = None
        self.update_triggers()
        self.create_test_trigger()

    def update_triggers(self):
        raw_triggers = TriggerEntity.select().order_by(TriggerEntity.position)
        self.triggers = [(trigger, re.compile(trigger.regex_pattern)) for trigger in raw_triggers]

    def create_test_trigger(self):
        new_trigger = TriggerEntity(
            mode="word",
            user_pattern="d?ck",
            response="Pattern matched!",
            cooldown=0,
            ignore_case=True,
            uses_wildcards=True,
            regex_pattern=r"(?i)d.ck",
            position=0
        )

        new_trigger.save()
        self.update_triggers()

    @group.command(description="Display documentation")
    async def help(self, interaction: discord.Interaction):
        await TriggerCog.get_help(interaction)

    @commands.Cog.listener()
    async def on_message(self, message):
        for trigger, pattern in self.triggers:
            if pattern.search(message.content):
                await message.channel.send(trigger.response)
                break

    @staticmethod
    async def get_help(interaction: discord.Interaction):
        pages = Pages(help_pages.get())
        await pages.show(interaction)


async def setup(bot):
    await bot.add_cog(TriggerCog(bot))
