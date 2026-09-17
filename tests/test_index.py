from WhooshPeewee import SearchIndex


def test_index_can_be_created(models, tmp_path):
    User = models["User"]

    search_index = SearchIndex(
        User,
        tmp_path / "users",
        fields=[
            "username",
            "email",
        ],
    )

    assert search_index.model is User
    assert search_index.index_name == "user"
    assert search_index.index_dir.exists()


def test_add_and_search(models, tmp_path):
    User = models["User"]

    user = User.create(
        username="Steve",
        email="steve@example.com",
    )

    search_index = SearchIndex(
        User,
        tmp_path / "users",
        fields=[
            "username",
            "email",
        ],
    )

    search_index.add(user)

    results = search_index.search("Steve")

    assert len(results) == 1
    assert results[0].model is User
    assert results[0].pk == user.id


def test_search_email(models, tmp_path):
    User = models["User"]

    user = User.create(
        username="Steve",
        email="steve@example.com",
    )

    search_index = SearchIndex(
        User,
        tmp_path / "users",
        fields=[
            "username",
            "email",
        ],
    )

    search_index.add(user)

    results = search_index.search("steve@example.com")

    assert len(results) == 1
    assert results[0].pk == user.id


def test_add_many(models, tmp_path):
    User = models["User"]

    users = [
        User.create(
            username="Steve",
            email="steve@example.com",
        ),
        User.create(
            username="Alan",
            email="alan@example.com",
        ),
        User.create(
            username="Alice",
            email="alice@example.com",
        ),
    ]

    search_index = SearchIndex(
        User,
        tmp_path / "users",
        fields=[
            "username",
            "email",
        ],
    )

    count = search_index.add_many(users)

    assert count == 3

    results = search_index.search("example.com")

    assert len(results) == 3


def test_update_existing_document(models, tmp_path):
    User = models["User"]

    user = User.create(
        username="Steve",
        email="old@example.com",
    )

    search_index = SearchIndex(
        User,
        tmp_path / "users",
        fields=[
            "username",
            "email",
        ],
    )

    search_index.add(user)

    user.email = "new@example.com"
    user.save()

    search_index.add(user)

    old_results = search_index.search("old@example.com")
    new_results = search_index.search("new@example.com")

    assert len(old_results) == 0
    assert len(new_results) == 1
    assert new_results[0].pk == user.id


def test_delete_document(models, tmp_path):
    User = models["User"]

    user = User.create(
        username="Steve",
        email="steve@example.com",
    )

    search_index = SearchIndex(
        User,
        tmp_path / "users",
        fields=[
            "username",
            "email",
        ],
    )

    search_index.add(user)

    assert len(search_index.search("Steve")) == 1

    search_index.delete(user)

    assert len(search_index.search("Steve")) == 0


def test_delete_by_primary_key(models, tmp_path):
    User = models["User"]

    user = User.create(
        username="Steve",
        email="steve@example.com",
    )

    search_index = SearchIndex(
        User,
        tmp_path / "users",
        fields=[
            "username",
            "email",
        ],
    )

    search_index.add(user)

    search_index.delete(user.id)

    assert search_index.search("Steve") == []


def test_rebuild_indexes_existing_records(
    models,
    tmp_path,
):
    User = models["User"]

    User.create(
        username="Steve",
        email="steve@example.com",
    )

    User.create(
        username="Alan",
        email="alan@example.com",
    )

    search_index = SearchIndex(
        User,
        tmp_path / "users",
        fields=[
            "username",
            "email",
        ],
    )

    count = search_index.rebuild()

    assert count == 2

    results = search_index.search("Steve")

    assert len(results) == 1
    assert results[0].pk == 1


def test_search_objects(models, tmp_path):
    User = models["User"]

    user = User.create(
        username="Steve",
        email="steve@example.com",
    )

    search_index = SearchIndex(
        User,
        tmp_path / "users",
        fields=[
            "username",
            "email",
        ],
    )

    search_index.add(user)

    results = search_index.search_objects("Steve")

    assert len(results) == 1
    assert results[0].id == user.id
    assert results[0].username == "Steve"


def test_stored_fields(models, tmp_path):
    Article = models["Article"]

    article = Article.create(
        title="Incident Response",
        body="Investigate compromised systems.",
    )

    search_index = SearchIndex(
        Article,
        tmp_path / "articles",
        fields=[
            "title",
            "body",
        ],
        stored_fields=[
            "title",
        ],
    )

    search_index.add(article)

    results = search_index.search("Incident")

    assert len(results) == 1
    assert results[0].stored_fields["title"] == "Incident Response"


def test_no_results(models, tmp_path):
    User = models["User"]

    search_index = SearchIndex(
        User,
        tmp_path / "users",
        fields=[
            "username",
            "email",
        ],
    )

    assert search_index.search("doesnotexist") == []


def test_invalid_model_field_is_rejected(
    models,
    tmp_path,
):
    User = models["User"]

    try:
        SearchIndex(
            User,
            tmp_path / "users",
            fields=["does_not_exist"],
        )
    except ValueError as exc:
        assert "does_not_exist" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError"
        )
