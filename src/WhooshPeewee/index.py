from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Iterable, Sequence, Type

from peewee import Model
from whoosh import index
from whoosh.fields import ID, TEXT, Schema
from whoosh.qparser import MultifieldParser
from whoosh.query import Query, Every

from .results import SearchResult


class SearchIndex:
    """
    A Whoosh index associated with a single Peewee model.

    Example:

        articles = SearchIndex(
            Article,
            "./indexes/articles",
            fields=["title", "body"],
        )

    The index is completely independent from Peewee's query system.
    """

    def __init__(
        self,
        model: Type[Model],
        index_dir: str | Path,
        fields: Sequence[str],
        *,
        index_name: str | None = None,
        stored_fields: Sequence[str] | None = None,
    ):
        if not issubclass(model, Model):
            raise TypeError(
                "model must be a Peewee Model"
            )

        if not fields:
            raise ValueError(
                "At least one searchable field is required"
            )

        self.model = model
        self.index_dir = Path(index_dir)
        self.fields = tuple(fields)
        self.index_name = index_name or model.__name__.lower()
        self.stored_fields = tuple(
            stored_fields or ()
        )

        self.index_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._validate_fields()
        self._ensure_index()

    # ------------------------------------------------------------------
    # Index setup
    # ------------------------------------------------------------------

    def _validate_fields(self) -> None:
        """
        Validate that all configured fields exist on the Peewee model.
        """

        for field_name in self.fields:
            if not hasattr(self.model, field_name):
                raise ValueError(
                    f"{self.model.__name__} has no field "
                    f"'{field_name}'"
                )

    def _schema(self) -> Schema:
        """
        Build the Whoosh schema.
        """

        schema_fields = {
            "pk": ID(
                stored=True,
                unique=True,
            ),
            "content": TEXT(
                stored=False,
            ),
        }

        for field_name in self.fields:
            schema_fields[field_name] = TEXT(
                stored=field_name in self.stored_fields,
            )

        return Schema(**schema_fields)

    def _ensure_index(self) -> None:
        """
        Create the Whoosh index if it does not already exist.
        """

        if not index.exists_in(
            str(self.index_dir)
        ):
            index.create_in(
                str(self.index_dir),
                self._schema(),
            )

    def _open(self):
        """
        Open the Whoosh index.
        """

        return index.open_dir(
            str(self.index_dir)
        )

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def _value_for_field(
        self,
        obj: Model,
        field_name: str,
    ) -> str:
        """
        Convert a model field to a searchable string.
        """

        value = getattr(
            obj,
            field_name,
            "",
        )

        if value is None:
            return ""

        return str(value)

    def _document_for_object(
        self,
        obj: Model,
    ) -> dict[str, Any]:
        """
        Convert a Peewee model instance into a Whoosh document.
        """

        primary_key = self.model._meta.primary_key

        if primary_key is None:
            raise ValueError(
                f"{self.model.__name__} does not have "
                "a primary key"
            )

        pk = getattr(
            obj,
            primary_key.name,
        )

        if pk is None:
            raise ValueError(
                "Cannot index a model instance without "
                "a primary key"
            )

        document = {
            "pk": str(pk),
        }

        content = []

        for field_name in self.fields:
            value = self._value_for_field(
                obj,
                field_name,
            )

            document[field_name] = value

            if value:
                content.append(value)

        document["content"] = " ".join(content)

        return document

    # ------------------------------------------------------------------
    # Primary key conversion
    # ------------------------------------------------------------------

    def _convert_primary_key(
        self,
        value: str,
    ) -> Any:
        """
        Convert a Whoosh string primary key back into the Peewee
        primary key's Python representation.
        """

        primary_key = self.model._meta.primary_key

        try:
            return primary_key.python_value(value)
        except (
            AttributeError,
            TypeError,
            ValueError,
        ):
            return value

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def add(
        self,
        obj: Model,
    ) -> None:
        """
        Add or replace a model instance in the index.
        """

        if not isinstance(
            obj,
            self.model,
        ):
            raise TypeError(
                f"Expected {self.model.__name__}, "
                f"got {type(obj).__name__}"
            )

        document = self._document_for_object(
            obj
        )

        ix = self._open()

        with ix.writer() as writer:
            writer.update_document(
                **document
            )

    def add_many(
        self,
        objects: Iterable[Model],
    ) -> int:
        """
        Add or replace multiple model instances.

        Returns the number of indexed objects.
        """

        ix = self._open()
        count = 0

        with ix.writer() as writer:
            for obj in objects:
                if not isinstance(
                    obj,
                    self.model,
                ):
                    raise TypeError(
                        f"Expected {self.model.__name__}, "
                        f"got {type(obj).__name__}"
                    )

                writer.update_document(
                    **self._document_for_object(obj)
                )

                count += 1

        return count

    def delete(
        self,
        obj_or_pk: Any,
    ) -> None:
        """
        Delete an object from the index.

        Accepts either a Peewee model instance or a primary key.
        """

        if isinstance(
            obj_or_pk,
            self.model,
        ):
            primary_key = self.model._meta.primary_key

            pk = getattr(
                obj_or_pk,
                primary_key.name,
            )
        else:
            pk = obj_or_pk

        ix = self._open()

        with ix.writer() as writer:
            writer.delete_by_term(
                "pk",
                str(pk),
            )

    def clear(self) -> None:
        ix = self._open()

        with ix.writer() as writer:
            writer.delete_by_query(
                Every(),
            )

    def rebuild(
        self,
        query=None,
    ) -> int:
        """
        Rebuild the complete index from the Peewee model.

        An optional Peewee query can be supplied to restrict which
        objects are indexed.

        Example:

            articles.rebuild(
                Article
                .select()
                .where(
                    Article.published == True
                )
            )
        """

        self.clear()

        if query is None:
            query = self.model.select()

        return self.add_many(query)

    # ------------------------------------------------------------------
    # Searching
    # ------------------------------------------------------------------

    def _build_query(
        self,
        searcher,
        query: str | Query,
        fields: Sequence[str] | None = None,
    ):
        """
        Convert a string query into a Whoosh query object.
        """

        if isinstance(
            query,
            Query,
        ):
            return query

        fields = tuple(
            fields or ("content",)
        )

        parser = MultifieldParser(
            fields,
            schema=searcher.schema,
        )

        return parser.parse(query)

    def search(
        self,
        query: str | Query,
        *,
        limit: int = 20,
        fields: Sequence[str] | None = None,
        offset: int = 0,
    ) -> list[SearchResult]:
        """
        Search this model's Whoosh index.
        """

        ix = self._open()

        with ix.searcher() as searcher:
            parsed_query = self._build_query(
                searcher,
                query,
                fields,
            )

            hits = searcher.search(
                parsed_query,
                limit=limit + offset,
            )

            results = []

            for hit in hits[offset:]:
                pk = self._convert_primary_key(
                    hit["pk"]
                )

                results.append(
                    SearchResult(
                        model=self.model,
                        pk=pk,
                        score=hit.score,
                        stored_fields=dict(hit),
                        index_name=self.index_name,
                    )
                )

            return results

    def search_objects(
        self,
        query: str | Query,
        *,
        limit: int = 20,
        fields: Sequence[str] | None = None,
    ) -> list[Model]:
        """
        Search and return the corresponding Peewee objects.
        """

        results = self.search(
            query,
            limit=limit,
            fields=fields,
        )

        objects = []

        for result in results:
            obj = result.get_object()

            if obj is not None:
                objects.append(obj)

        return objects
