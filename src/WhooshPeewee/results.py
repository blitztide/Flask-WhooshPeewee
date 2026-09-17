from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Type

from peewee import Model


@dataclass(frozen=True)
class SearchResult:
    """
    Represents a result returned from a Whoosh search.

    The result stores the Peewee model class and primary key rather
    than the Peewee object itself. This keeps the search layer
    independent from Peewee's query system.

    The underlying object can be retrieved using get_object().
    """

    model: Type[Model]
    pk: Any
    score: float
    stored_fields: Mapping[str, Any]
    index_name: str

    def get_object(self) -> Model | None:
        """
        Retrieve the corresponding Peewee model instance.

        This uses Peewee's normal query interface and does not modify
        or replace any Peewee query methods.
        """

        primary_key = self.model._meta.primary_key

        return self.model.get_or_none(
            primary_key == self.pk
        )

    @property
    def model_name(self) -> str:
        """
        Return the name of the Peewee model.
        """

        return self.model.__name__
