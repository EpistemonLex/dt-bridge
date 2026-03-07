"""Architectural interfaces for dt-bridge."""

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    import pandas as pd

class ITranscriptVectorizer(Protocol):
    """Protocol for semantic transcript search."""

    def search(self, query: str, limit: int = 5) -> pd.DataFrame:
        """Search for transcript chunks."""
        ...
