from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, TypeAlias, TypeVar

if TYPE_CHECKING:
    from .submissions import Submission
    from .tables import Table


GraphqlQuery: TypeAlias = str
GraphqlVariables: TypeAlias = dict[str, Any]
Graphql: TypeAlias = tuple[GraphqlQuery, GraphqlVariables]
GraphqlIterator: TypeAlias = Iterator[Graphql]

SubmissionType = TypeVar("SubmissionType", bound="Submission")
TableType = TypeVar("TableType", bound="Table")
OrmType = TypeVar("OrmType", bound="Submission | Table")
