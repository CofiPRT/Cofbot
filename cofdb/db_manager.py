import peewee


db = peewee.SqliteDatabase('cofbot.db')


class BaseModel(peewee.Model):
    class Meta:
        database = db
