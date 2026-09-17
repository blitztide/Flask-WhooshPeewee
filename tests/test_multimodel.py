from WhooshPeewee import (
    SearchIndex,
    MultiModelSearch,
)


def test_search_multiple_models(
    models,
    populated_database,
    tmp_path,
):
    User = models["User"]
    Article = models["Article"]
    Course = models["Course"]

    user_index = SearchIndex(
        User,
        tmp_path / "users",
        fields=[
            "username",
            "email",
        ],
    )

    article_index = SearchIndex(
        Article,
        tmp_path / "articles",
        fields=[
            "title",
            "body",
        ],
    )

    course_index = SearchIndex(
        Course,
        tmp_path / "courses",
        fields=[
            "name",
            "description",
        ],
    )

    user_index.rebuild()
    article_index.rebuild()
    course_index.rebuild()

    search = MultiModelSearch(
        user_index,
        article_index,
        course_index,
    )

    results = search.search(
        "Learn",
        limit=20,
    )

    assert len(results) >= 2

    models_found = {
        result.model
        for result in results
    }

    assert Article in models_found
    assert Course in models_found


def test_search_specific_model(
    models,
    populated_database,
    tmp_path,
):
    User = models["User"]
    Article = models["Article"]

    user_index = SearchIndex(
        User,
        tmp_path / "users",
        fields=[
            "username",
            "email",
        ],
    )

    article_index = SearchIndex(
        Article,
        tmp_path / "articles",
        fields=[
            "title",
            "body",
        ],
    )

    user_index.rebuild()
    article_index.rebuild()

    search = MultiModelSearch(
        user_index,
        article_index,
    )

    results = search.search(
        "Steve",
        models=[User],
    )

    assert len(results) == 1
    assert results[0].model is User


def test_model_filter_excludes_other_models(
    models,
    populated_database,
    tmp_path,
):
    User = models["User"]
    Article = models["Article"]

    user_index = SearchIndex(
        User,
        tmp_path / "users",
        fields=[
            "username",
            "email",
        ],
    )

    article_index = SearchIndex(
        Article,
        tmp_path / "articles",
        fields=[
            "title",
            "body",
        ],
    )

    user_index.rebuild()
    article_index.rebuild()

    search = MultiModelSearch(
        user_index,
        article_index,
    )

    results = search.search(
        "security",
        models=[User],
    )

    assert all(
        result.model is User
        for result in results
    )


def test_remove_index(
    models,
    tmp_path,
):
    User = models["User"]
    Article = models["Article"]

    user_index = SearchIndex(
        User,
        tmp_path / "users",
        fields=["username"],
    )

    article_index = SearchIndex(
        Article,
        tmp_path / "articles",
        fields=["title"],
    )

    search = MultiModelSearch(
        user_index,
        article_index,
    )

    assert search.get_index("user") is user_index
    assert search.get_index("article") is article_index

    search.remove_index("article")

    assert "article" not in search.indexes
