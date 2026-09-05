from typing import Literal

type ExpenseSortField = Literal[
    "spent_at",
    "created_at",
    "updated_at",
    "amount",
    "title",
]
type SortDirection = Literal["asc", "desc"]
