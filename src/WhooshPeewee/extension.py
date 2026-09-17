from __future__ import annotations

from pathlib import Path
from typing import Sequence, Type

import click
from flask import Flask
from peewee import Model

from .index import SearchIndex
from .multimodel import MultiModelSearch
from .results import SearchResult


class WhooshPeewee:
    """
    Flask extension providing Whoosh indexes for Peewee models.

    The extension does not modify or replace any Peewee query methods.

    Example:

        search = WhooshPeewee()

        def create_app():
            app = Flask(__name__)

            search.init_app(app)

            search.register(
                Article,
                fields=["title", "body"],
            )

            return app

    CLI:

        flask whoosh rebuild

        flask whoosh rebuild --model Article
    """

    def __init__(
        self,
        app: Flask | None = None,
        *,
        index_root: str | Path = "./whoosh_indexes",
    ):
        self.app: Flask | None = None
        self.index_root = Path(index_root)

        self.indexes: dict[
            Type[Model],
            SearchIndex,
        ] = {}

        if app is not None:
            self.init_app(app)

    def init_app(
        self,
        app: Flask,
    ) -> None:
        """
        Initialise the extension with a Flask application.
        """

        self.app = app

        configured_root = app.config.get(
            "WHOOSH_INDEX_ROOT",
            self.index_root,
        )

        self.index_root = Path(
            configured_root
        )

        self.index_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        app.extensions[
            "whoosh_peewee"
        ] = self

        app.cli.add_command(
            self._create_cli()
        )

    # ------------------------------------------------------------------
    # CLI
    # ------------------------------------------------------------------

    def _create_cli(self) -> click.Group:
        """
        Create the `flask whoosh` CLI command group.
        """

        @click.group("whoosh")
        def whoosh_cli():
            """Manage Whoosh search indexes."""

        @whoosh_cli.command("rebuild")
        @click.option(
            "--model",
            "model_name",
            default=None,
            help=(
                "Only rebuild the index for "
                "the specified model."
            ),
        )
        def rebuild(
            model_name: str | None,
        ):
            """
            Rebuild Whoosh search indexes.

            Without --model, every registered index is rebuilt.
            """

            if not self.indexes:
                click.echo(
                    "No Whoosh indexes are registered."
                )
                return

            if model_name is not None:
                search_index = (
                    self._find_index_by_model_name(
                        model_name
                    )
                )

                if search_index is None:
                    click.echo(
                        "Error: no index registered "
                        f"for model '{model_name}'.",
                        err=True,
                    )

                    raise click.exceptions.Exit(
                        1
                    )

                self._rebuild_index(
                    search_index
                )

                return

            self.rebuild()

        return whoosh_cli

    def _find_index_by_model_name(
        self,
        model_name: str,
    ) -> SearchIndex | None:
        """
        Find a registered index by Peewee model class name.

        Matching is case-insensitive.
        """

        model_name = model_name.lower()

        for search_index in self.indexes.values():
            if (
                search_index.model.__name__.lower()
                == model_name
            ):
                return search_index

        return None

    def _rebuild_index(
        self,
        search_index: SearchIndex,
    ) -> int:
        """
        Rebuild a single index and display progress.
        """

        model = search_index.model

        click.echo(
            f"Rebuilding {model.__name__}..."
        )

        count = search_index.rebuild()

        click.echo(
            f"  Indexed {count:,} "
            f"{model.__name__} record(s)."
        )

        return count

    # ------------------------------------------------------------------
    # Index registration
    # ------------------------------------------------------------------

    def register(
        self,
        model: Type[Model],
        *,
        fields: Sequence[str],
        index_name: str | None = None,
        stored_fields: Sequence[str] | None = None,
    ) -> SearchIndex:
        """
        Register a Peewee model with Whoosh.
        """

        name = (
            index_name
            or model.__name__.lower()
        )

        index_dir = (
            self.index_root / name
        )

        search_index = SearchIndex(
            model,
            index_dir,
            fields,
            index_name=name,
            stored_fields=stored_fields,
        )

        self.indexes[model] = search_index

        return search_index

    def get_index(
        self,
        model: Type[Model],
    ) -> SearchIndex:
        """
        Return the Whoosh index registered for a model.
        """

        return self.indexes[model]

    # ------------------------------------------------------------------
    # Rebuilding
    # ------------------------------------------------------------------

    def rebuild(
        self,
        *,
        models: Sequence[Type[Model]] | None = None,
    ) -> dict[str, int]:
        """
        Rebuild all registered Whoosh indexes.

        If `models` is supplied, only those indexes are rebuilt.

        Returns:

            {
                "Article": 150,
                "Course": 24,
                "User": 1200,
            }
        """

        if models is None:
            indexes = list(
                self.indexes.values()
            )
        else:
            indexes = [
                self.indexes[model]
                for model in models
            ]

        counts: dict[str, int] = {}

        if not indexes:
            click.echo(
                "No Whoosh indexes to rebuild."
            )

            return counts

        click.echo(
            "Rebuilding "
            f"{len(indexes)} "
            "Whoosh index(es)..."
        )

        for search_index in indexes:
            count = self._rebuild_index(
                search_index
            )

            counts[
                search_index.model.__name__
            ] = count

        click.echo(
            "Whoosh index rebuild complete."
        )

        return counts

    # ------------------------------------------------------------------
    # Searching
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        *,
        models: Sequence[Type[Model]] | None = None,
        limit: int = 20,
    ) -> list[SearchResult]:
        """
        Search registered models.
        """

        if models is None:
            indexes = list(
                self.indexes.values()
            )
        else:
            indexes = [
                self.indexes[model]
                for model in models
            ]

        multi = MultiModelSearch(
            *indexes
        )

        return multi.search(
            query,
            limit=limit,
        )

    @property
    def multi(self) -> MultiModelSearch:
        """
        Return a MultiModelSearch containing all registered models.
        """

        return MultiModelSearch(
            *self.indexes.values()
        )
