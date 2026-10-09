"""Traceable event storage for deterministic evidence construction."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from types import MappingProxyType
from typing import Any, Protocol

from .schemas import EventSnapshot


class CanonicalLogEvent(Protocol):
    """Structural contract consumed from Member 1's canonical ``LogEvent``."""

    event_id: str
    timestamp_iso: str | None
    severity: str | None
    service: str | None
    message: str
    template: str | None
    source_file: str | None
    line_number: int | None


class EventStore:
    """Read-only ID index exposing immutable, validated event snapshots."""

    __slots__ = ("_events",)

    def __init__(self, events: Iterable[CanonicalLogEvent | Mapping[str, Any]]):
        snapshots: dict[str, EventSnapshot] = {}
        for event in events:
            snapshot = self._to_snapshot(event)
            if snapshot.event_id in snapshots:
                raise ValueError(f"Duplicate event_id: {snapshot.event_id}")
            snapshots[snapshot.event_id] = snapshot
        # MappingProxyType prevents accidental mutation of the underlying index.
        self._events = MappingProxyType(snapshots)

    @staticmethod
    def _read(event: CanonicalLogEvent | Mapping[str, Any], field: str) -> Any:
        if isinstance(event, Mapping):
            return event.get(field)
        return getattr(event, field, None)

    @classmethod
    def _to_snapshot(
        cls, event: CanonicalLogEvent | Mapping[str, Any]
    ) -> EventSnapshot:
        event_id = cls._read(event, "event_id")
        message = cls._read(event, "message")
        if not isinstance(event_id, str) or not event_id or not event_id.strip():
            raise ValueError("Every event must have a non-empty event_id")
        if event_id != event_id.strip():
            raise ValueError("event_id must not have leading or trailing whitespace")
        if not isinstance(message, str):
            raise ValueError(f"Event {event_id} must have a string message")

        line_number = cls._read(event, "line_number")
        # bool is a subclass of int in Python, but it is not a valid line number.
        if line_number is not None and (
            isinstance(line_number, bool) or not isinstance(line_number, int)
        ):
            raise ValueError(f"Event {event_id} has a non-integer line_number")

        return EventSnapshot(
            event_id=event_id,
            timestamp_iso=cls._read(event, "timestamp_iso"),
            severity=cls._read(event, "severity"),
            service=cls._read(event, "service"),
            message=message,
            template=cls._read(event, "template"),
            source_file=cls._read(event, "source_file"),
            line_number=line_number,
        )

    def __len__(self) -> int:
        return len(self._events)

    def __contains__(self, event_id: object) -> bool:
        return isinstance(event_id, str) and event_id in self._events

    def get(self, event_id: str) -> EventSnapshot | None:
        """Return a snapshot or ``None`` if the ID is unknown."""
        if not isinstance(event_id, str):
            return None
        return self._events.get(event_id)

    def require(self, event_id: str) -> EventSnapshot:
        """Return a snapshot or raise a traceable error for an unknown ID."""
        event = self.get(event_id)
        if event is None:
            raise KeyError(f"Unknown event_id: {event_id}")
        return event

    def ids(self) -> tuple[str, ...]:
        """Return event IDs in insertion/source order."""
        return tuple(self._events)
