# Quick Start Guide

Import `Flask-WhooshPeewee` and initialise from your created `Flask` application.


```python
from flask import Flask
from Flask-WhooshPeewee import WhooshPeewee
from models import User, Article

app = Flask(__name__)
app.config["WHOOSH_INDEX_ROOT"] = "whoosh"  # Base folder for Whoosh Index

# Initialise WhooshPeewee
search = WhooshPeewee()
search.init_app(app)

# Register Indexes to models
search.register(
    User,
    fields=[
        "username",
        "email",
    ]
)

search.register(
        Article,
        fields=[  # Just store indexes
            "title",
            "body",
        ],
        stored_fields=[  # Store data in the index
            "title",
        ],
)

```
