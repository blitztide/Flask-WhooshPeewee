import pytest
from WhooshPeewee import WhooshPeewee
from flask import Flask
from peewee import (
    SqliteDatabase,
    Model,
    CharField,
    TextField,
)


@pytest.fixture
def database():
    """
    Provide a fresh in-memory SQLite database for each test.

    The connection remains open for the lifetime of the fixture.
    This is important because an SQLite :memory: database exists
    only while its connection remains alive.
    """

    db = SqliteDatabase(":memory:")

    class BaseModel(Model):
        class Meta:
            database = db

    class User(BaseModel):
        username = CharField()
        email = CharField()

    class Article(BaseModel):
        title = CharField()
        body = TextField()

    class Course(BaseModel):
        name = CharField()
        description = TextField()

    db.connect()

    db.create_tables([
        User,
        Article,
        Course,
    ])

    yield {
        "db": db,
        "User": User,
        "Article": Article,
        "Course": Course,
    }

    db.drop_tables(
        [
            User,
            Article,
            Course,
        ],
        safe=True,
    )

    db.close()


@pytest.fixture
def models(database):
    """
    Convenience fixture exposing the test models.
    """

    return {
        "User": database["User"],
        "Article": database["Article"],
        "Course": database["Course"],
    }


@pytest.fixture
def populated_database(database):
    """
    Database containing representative test data.
    """

    User = database["User"]
    Article = database["Article"]
    Course = database["Course"]

    users = [
        ("Steve", "steve@steve.com"),
        ("Alan", "alan@alan.in"),
        ("Bob", "bob@burgers.co"),
        ("Alice", "alice@cooper.com"),
    ]

    for username, email in users:
        User.create(
            username=username,
            email=email,
        )

    Article.create(
        title="Introduction to Linux",
        body="Learn Linux command line fundamentals.",
    )

    Article.create(
        title="Incident Response",
        body="Learn how to investigate a security incident.",
    )

    Article.create(
        title="Network Forensics",
        body="Analyse network traffic using Wireshark.",
    )

    Course.create(
        name="Blue Team Fundamentals",
        description="Learn defensive cybersecurity fundamentals.",
    )

    Course.create(
        name="Digital Forensics",
        description="Investigate forensic evidence from compromised systems.",
    )

    return database


@pytest.fixture
def app(database, models, tmp_path):
    """
    Create a Flask application configured with WhooshPeewee.
    """

    User = models["User"]
    Article = models["Article"]
    Course = models["Course"]

    app = Flask(__name__)

    app.config["TESTING"] = True
    app.config["WHOOSH_INDEX_ROOT"] = str(
        tmp_path / "whoosh"
    )

    search = WhooshPeewee()
    search.init_app(app)

    search.register(
        User,
        fields=[
            "username",
            "email",
        ],
    )

    search.register(
        Article,
        fields=[
            "title",
            "body",
        ],
        stored_fields=[
            "title",
        ],
    )

    search.register(
        Course,
        fields=[
            "name",
            "description",
        ],
        stored_fields=[
            "name",
        ],
    )

    app.extensions["test_search"] = search

    return app


@pytest.fixture
def search(app):
    """
    Return the WhooshPeewee extension from the test application.
    """

    return app.extensions["test_search"]
