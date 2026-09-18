# Updating Indexes

Flask-WhooshPeewee doesn't monkeypatch into PeeWee so indexes need to be updated manually.

## Full Rebuild

To trigger a full rebuild you can either call `WhooshPeewee.rebuild()` or run the CLI command `flask whoosh rebuild`

This rebuilds all indexes you have defined in your Flask application.

## Update a single index

In the event that you make a change to indexable content using Peewee, you can trigger an update for just one Index using the following code:

```python
app = Flask(__name__)
search = WhooshPeewee()
search.init_app(app)
...

post = Post.get_or_none(1)  # Get a post
post.content = "new content"  # New content for a post
post.save() # Update the database record using peewee

# We now want to update the index on Whoosh's side for Posts
search.rebuild(
    models=[
            Post,
        ]
    )

# This has now built a new index for Posts
```

You can also use the CLI to manually trigger a rebuild of a specific index `flask whoosh rebuild --model Post`
