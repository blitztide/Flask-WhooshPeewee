from WhooshPeewee import SearchResult


def test_search_result_get_object(models):
    User = models["User"]

    user = User.create(
        username="Steve",
        email="steve@example.com",
    )

    result = SearchResult(
        model=User,
        pk=user.id,
        score=1.0,
        stored_fields={
            "username": "Steve",
        },
        index_name="user",
    )

    obj = result.get_object()

    assert obj is not None
    assert obj.id == user.id
    assert obj.username == "Steve"


def test_search_result_missing_object(models):
    User = models["User"]

    result = SearchResult(
        model=User,
        pk=999,
        score=1.0,
        stored_fields={},
        index_name="user",
    )

    assert result.get_object() is None


def test_model_name(models):
    User = models["User"]

    result = SearchResult(
        model=User,
        pk=1,
        score=1.0,
        stored_fields={},
        index_name="user",
    )

    assert result.model_name == "User"
