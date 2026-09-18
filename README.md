# Flask-WhooshPeewee
[![Build](https://github.com/blitztide/Flask-WhooshPeewee/actions/workflows/pipeline.yml/badge.svg)](https://github.com/blitztide/Flask-WhooshPeewee/actions/workflows/pipeline.yml)

**Flask + Whoosh + peewee**

Flask-WhooshPeewee is a [Flask](https://flask.palletsprojects.com/en/stable/) extension that mixes the searching and indexing functionality of [Whoosh](https://whoosh.readthedocs.io/en/latest/index.html) with the Schema
of [peewee](https://peewee.readthedocs.io/en/latest/peewee/quickstart.html) for use in Flask applications.

## Installation

Install Flask-WhooshPeewee using pip:
```
pip install Flask-WhooshPeewee
```

## CLI Commands
Flask-WhooshPeewee comes with some commands to manage your Whoosh indexes outside of your main Flask application:

* **rebuild** - Rebuild your indexes fully

### Rebuild

```
flask whoosh rebuild
```

# Contributors

See AUTHORS.md

# License

Licensed under a BSD License.
