def test_extension_registers_indexes(search, models):
    User = models["User"]
    Article = models["Article"]
    Course = models["Course"]

    assert search.get_index(User).model is User
    assert search.get_index(Article).model is Article
    assert search.get_index(Course).model is Course


def test_extension_is_registered_with_flask(
    app,
    search,
):
    assert (
        app.extensions["whoosh_peewee"]
        is search
    )


def test_search_through_extension(
    search,
    models,
    populated_database,
):
    User = models["User"]

    search.rebuild()

    results = search.search(
        "Steve",
        limit=10,
    )

    assert len(results) == 1
    assert results[0].model is User
    assert results[0].pk == 1


def test_extension_search_objects(
    search,
    models,
    populated_database,
):
    search.rebuild()

    results = search.multi.search_objects(
        "Steve",
        limit=10,
    )

    assert len(results) == 1
    assert results[0].username == "Steve"


def test_rebuild_all_indexes(
    search,
    models,
    populated_database,
):
    counts = search.rebuild()

    assert counts["User"] == 4
    assert counts["Article"] == 3
    assert counts["Course"] == 2


def test_rebuild_specific_model(
    search,
    models,
    populated_database,
):
    User = models["User"]

    counts = search.rebuild(
        models=[User],
    )

    assert counts == {
        "User": 4,
    }


def test_cli_rebuild(
    app,
    search,
    populated_database,
):
    runner = app.test_cli_runner()

    result = runner.invoke(
        args=[
            "whoosh",
            "rebuild",
        ]
    )

    assert result.exit_code == 0

    assert (
        "Whoosh index rebuild complete."
        in result.output
    )


def test_cli_rebuild_specific_model(
    app,
    models,
    populated_database,
):
    runner = app.test_cli_runner()

    result = runner.invoke(
        args=[
            "whoosh",
            "rebuild",
            "--model",
            "User",
        ]
    )

    assert result.exit_code == 0
    assert "Rebuilding User..." in result.output
    assert "Indexed 4 User record(s)." in result.output


def test_cli_rebuild_unknown_model(
    app,
    populated_database,
):
    runner = app.test_cli_runner()

    result = runner.invoke(
        args=[
            "whoosh",
            "rebuild",
            "--model",
            "DoesNotExist",
        ]
    )

    assert result.exit_code != 0
    assert (
        "no index registered"
        in result.output.lower()
    )

def test_search_endpoint(
    app,
    search,
    models,
    populated_database,
):
    User = models["User"]

    @app.get("/search")
    def search_view():
        from flask import request

        query = request.args.get(
            "q",
            "",
        ).strip()

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
                }
                for result in results
            ]
        }

    search.rebuild()

    client = app.test_client()

    response = client.get(
        "/search?q=Steve"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert len(data["results"]) == 1
    assert data["results"][0]["type"] == "User"
    assert data["results"][0]["id"] == 1


def test_search_endpoint_empty_query(
    app,
    search,
):
    @app.get("/search")
    def search_view():
        from flask import request

        query = request.args.get(
            "q",
            "",
        ).strip()

        if not query:
            return {"results": []}

        return {"results": []}

    client = app.test_client()

    response = client.get("/search")

    assert response.status_code == 200
    assert response.get_json() == {
        "results": []
    }
