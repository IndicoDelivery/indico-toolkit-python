from collections.abc import Iterator
from typing import TYPE_CHECKING, Annotated, Any, TypeAlias, TypeVar

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
Categorical = Annotated[str, "CATEGORICAL"]
