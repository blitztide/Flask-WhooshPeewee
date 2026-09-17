from peewee import (
    SqliteDatabase,
    AutoField,
    CharField,
    ForeignKeyField,
    Model,
    TextField,
)

db = SqliteDatabase(
    "file:whooshpeewee?mode=memory&cache=shared",
    uri=True,
)


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    id = AutoField()
    username = CharField()
    email = CharField()


class Article(BaseModel):
    id = AutoField()
    title = CharField()
    body = TextField()


class Course(BaseModel):
    id = AutoField()
    name = CharField()
    description = TextField()
