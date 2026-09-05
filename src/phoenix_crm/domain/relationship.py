"""Customer relationship helpers for Phoenix CRM 360."""

from __future__ import annotations

from uuid import UUID


def add_unique_relationship(relationship_ids: list[UUID], entity_id: UUID) -> None:
    """Add an entity identifier once while preserving insertion order."""
    if entity_id not in relationship_ids:
        relationship_ids.append(entity_id)


def remove_relationship(relationship_ids: list[UUID], entity_id: UUID) -> None:
    """Remove an entity identifier when present."""
    try:
        relationship_ids.remove(entity_id)
    except ValueError:
        pass
