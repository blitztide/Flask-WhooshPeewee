from flask import Flask, request
from WhooshPeewee import WhooshPeewee
from models import db, User, Article, Course


search = WhooshPeewee()

def seed_db():
    tables = [
        User,
        Article,
        Course]

    for model in tables:
        model.create_table()

    users = [
        ("Steve", "steve@steve.com"),
        ("Alan", "alan@alan.in"),
        ("Bob", "bob@burgers.co"),
        ("Alice", "alice@cooper.com"),
        ("Sewage Steve", "steve@sewage.works")]

    for name, email in users:
        User.create(
            username=name,
            email=email).save()

    articles = [
        ("A New article about flowers", "flowers are really cool and smell nice."),
        ("Too much sewage", "Sewage is everywhere and I don't like the smell."),
        ("New sewage outlet", "A New sewage outlet has been built in your town"),
        ("Bees in local area", "Bees are pollinating flowers in the local area")
    ]

    for title, content in articles:
        Article.create(
            title=title,
            body=content).save()

    courses = [
        ("Sewage Treatment Manager","Manage the lifecycle of sewage with this course, no more smelling like flowers"),
        ("Burger Manager Course", "Learn how to open your own burger restaurant")]

    for name, description in courses:
        Course.create(
            name=name,
            description=description).save()

def create_app():
    app = Flask(__name__)

    app.config["WHOOSH_INDEX_ROOT"] = "./data/whoosh"

    db.connect(reuse_if_open=True)
    seed_db()
    assert User.get(1)

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
    @app.get("/")
    def index():
        return """
<html>
 <body>
    <h1>Search</h1>
    <form action="/search" method="GET">
        <input type="text" name="q"></input>
        <input type="submit"/>
    </form>
 </body>
</html>
"""

    @app.get("/search")
    def search_view():
        query = request.args.get("q", "").strip()

        if not query:
            return {"results": []}

        results = search.search(
            query,
            models=[
                User,
                Article,
                Course],
            limit=50,
        )

        return {
            "results": [
                {
                    "type": result.model_name,
                    "id": result.pk,
                    "score": result.score,
                    "object": result.get_object().__data__,
                }
                for result in results
            ]
        }

    search.rebuild()

    return app
