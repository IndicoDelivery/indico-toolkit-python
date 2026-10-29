from collections.abc import Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeAlias, TypeVar

if TYPE_CHECKING:
    from .submissions import Submission
    from .tables import Table

# ORM Type Aliases
GraphqlQuery: TypeAlias = str
GraphqlVariables: TypeAlias = dict[str, Any]
Graphql: TypeAlias = tuple[GraphqlQuery, GraphqlVariables]
GraphqlIterator: TypeAlias = Iterator[Graphql]

# ORM Type Variables
SubmissionType = TypeVar("SubmissionType", bound="Submission")
TableType = TypeVar("TableType", bound="Table")
OrmType = TypeVar("OrmType", bound="Submission | Table")


# Scalar Field Types
@dataclass(frozen=True)
class Price:
    amount: float
    currency: str


@dataclass(frozen=True)
class User:
    id: int
    name: str
    email: str
