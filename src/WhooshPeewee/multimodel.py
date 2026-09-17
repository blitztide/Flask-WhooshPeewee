from __future__ import annotations

from typing import Sequence, Type

from peewee import Model

from .index import SearchIndex
from .results import SearchResult


class MultiModelSearch:
    """
    Search across multiple SearchIndex instances.

    Each Peewee model can have its own Whoosh index and schema.

    Example:

        search = MultiModelSearch(
            article_index,
            course_index,
            lab_index,
        )

        results = search.search(
            "incident response"
        )
    """

    def __init__(
        self,
        *indexes: SearchIndex,
    ):
        self.indexes: dict[
            str,
            SearchIndex,
        ] = {}

        for search_index in indexes:
            self.add_index(
                search_index
            )

    def add_index(
        self,
        search_index: SearchIndex,
    ) -> None:
        """
        Add an index to the multi-model search.
        """

        self.indexes[
            search_index.index_name
        ] = search_index

    def remove_index(
        self,
        name: str,
    ) -> None:
        """
        Remove an index by name.
        """

        self.indexes.pop(
            name,
            None,
        )

    def get_index(
        self,
        name: str,
    ) -> SearchIndex:
        """
        Retrieve an index by name.
        """

        return self.indexes[name]

    def search(
        self,
        query: str,
        *,
        models: Sequence[Type[Model]] | None = None,
        limit: int = 20,
        per_model_limit: int | None = None,
        fields: Sequence[str] | None = None,
    ) -> list[SearchResult]:
        """
        Search across multiple model indexes.

        Results are merged and sorted by Whoosh score.

        `models` can be used to restrict which Peewee models are
        searched.

        `per_model_limit` controls the number of results initially
        retrieved from each individual index.
        """

        if models is None:
            indexes = list(
                self.indexes.values()
            )
        else:
            model_set = set(models)

            indexes = [
                search_index
                for search_index
                in self.indexes.values()
                if search_index.model
                in model_set
            ]

        if per_model_limit is None:
            per_model_limit = limit

        results: list[SearchResult] = []

        for search_index in indexes:
            results.extend(
                search_index.search(
                    query,
                    limit=per_model_limit,
                    fields=fields,
                )
            )

        results.sort(
            key=lambda result: result.score,
            reverse=True,
        )

        return results[:limit]

    def search_objects(
        self,
        query: str,
        *,
        models: Sequence[Type[Model]] | None = None,
        limit: int = 20,
    ) -> list[Model]:
        """
        Search multiple models and return the corresponding Peewee
        objects.
        """

        results = self.search(
            query,
            models=models,
            limit=limit,
        )

        objects = []

        for result in results:
            obj = result.get_object()

            if obj is not None:
                objects.append(obj)

        return objects
