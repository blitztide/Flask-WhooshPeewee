# Quick Start Guide

Import `Flask-WhooshPeewee` and initialise from your created `Flask` application.


```python
from flask import Flask
from Flask-WhooshPeewee import WhooshPeewee

app = Flask(__name__)
app.config["WHOOSH_INDEX_ROOT"] = "whoosh"  # Base folder for Whoosh Index
WhooshPeewee.init_app(app)
```
