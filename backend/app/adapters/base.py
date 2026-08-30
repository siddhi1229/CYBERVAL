from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.orm import Session


class BaseSourceAdapter(ABC):
    """Abstract base adapter establishing the common ingestion contract for all security sources."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Unique identifier for the source adapter."""
        pass

    @abstractmethod
    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        """Retrieve or generate raw source records."""
        pass

    @abstractmethod
    def normalize(self, raw_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Normalize raw records into standard internal schemas."""
        pass

    @abstractmethod
    def validate(self, normalized_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate normalized records for contract completeness."""
        pass

    @abstractmethod
    def ingest(self, db: Session, records: list[dict[str, Any]] | None = None, **kwargs) -> int:
        """Persist records into PostgreSQL tables and return count of ingested entities."""
        pass
