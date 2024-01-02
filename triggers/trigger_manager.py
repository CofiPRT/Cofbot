import datetime
import re

from discord.ext import commands
from cofdb import db, BaseModel
from peewee import *


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
    created_at = DateTimeField(default=datetime.datetime.now)


class TriggerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not db.is_connection_usable():
            db.connect()
            db.create_tables([TriggerEntity])

        self.triggers = None
        self._update_triggers()
        self.create_test_trigger()

    def _update_triggers(self):
        raw_triggers = TriggerEntity.select().order_by(TriggerEntity.created_at)
        self.triggers = [(trigger, re.compile(trigger.regex_pattern)) for trigger in raw_triggers]

    def create_test_trigger(self):
        new_trigger = TriggerEntity(
            mode='word',
            user_pattern='d?ck',
            response='Pattern matched!',
            cooldown=0,
            ignore_case=True,
            uses_wildcards=True,
            regex_pattern=r'(?i)d.ck'
        )

        new_trigger.save()
        self._update_triggers()

    @commands.Cog.listener()
    async def on_message(self, message):
        for trigger, pattern in self.triggers:
            if pattern.search(message.content):
                await message.channel.send(trigger.response)
                break


async def setup(bot):
    await bot.add_cog(TriggerCog(bot))
