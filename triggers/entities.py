from peewee import *
from cofdb import BaseModel


class TriggerEntity(BaseModel):
    # mandatory fields
    mode = TextField()
    user_pattern = TextField()
    response = TextField()

    # optional fields (with global defaults)
    cooldown = IntegerField(null=True)
    case_sensitive = BooleanField(null=True)
    avoid_links = BooleanField(null=True)
    avoid_emotes = BooleanField(null=True)

    # optional fields (without global defaults)
    start = BooleanField()
    end = BooleanField()

    # all triggers actually use regex in the background, computed upon being created or modified
    # this field is not exposed to the user
    regex_pattern = TextField()

    # self-managed fields
    position = IntegerField()
    last_triggered = DateTimeField(null=True)


class TriggerSettingsEntity(BaseModel):
    cooldown = IntegerField(default=0)
    case_sensitive = BooleanField(default=False)
    avoid_links = BooleanField(default=False)
    avoid_emotes = BooleanField(default=False)
