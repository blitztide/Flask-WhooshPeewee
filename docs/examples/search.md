# Simple Search Example

This is a simple search that performs query on a single model and returns a `SearchResult` as JSON

```python
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
        ("Alice", "alice@cooper.com")]

    for name, email in users:
        User.create(
            username=name,
            email=email).save()

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

```
