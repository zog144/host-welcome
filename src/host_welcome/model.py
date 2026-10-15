"""Strict v1 observation contract. No probing, side effects or authorization."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

SCHEMA_VERSION = "host-welcome.readiness/v1"
CATEGORIES = (
    "installation", "state_integrity", "host_identity", "enrollment",
    "network", "configuration", "station_access", "recovery",
)
LABELS = {
    "installation": "Installation",
    "state_integrity": "Protected STATE",
    "host_identity": "Host identity",
    "enrollment": "Enrollment",
    "network": "Network",
    "configuration": "Configuration",
    "station_access": "Station access",
    "recovery": "Recovery",
}
STATUSES = frozenset({"verified", "pending", "unknown", "degraded", "failed"})
SOURCE_KINDS = frozenset({"fixture", "host"})


class SnapshotError(ValueError):
    """An invalid or untrusted readiness snapshot."""


@dataclass(frozen=True)
class Observation:
    status: str
    summary: str
    producer: str
    evidence_ref: str | None


@dataclass(frozen=True)
class Snapshot:
    schema_version: str
    source_kind: str
    observed_at: datetime
    host_label: str
    observations: Mapping[str, Observation]


@dataclass(frozen=True)
class Assessment:
    aggregate: str
    fresh: bool
    reason: str


def _object(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SnapshotError(f"{context} must be an object")
    return value


def _string(value: Any, context: str, limit: int = 240) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise SnapshotError(f"{context} must be a nonempty string of at most {limit} characters")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise SnapshotError(f"{context} must not contain control characters")
    return value


def load_snapshot(data: Any, *, trusted: bool = False) -> Snapshot:
    """Validate a complete snapshot.

    CLI data is untrusted by default. Only an eventual protected local adapter
    may set trusted=True when it has *independently* verified the producer.
    """
    root = _object(data, "snapshot")
    required = {"schema_version", "source_kind", "observed_at", "host_label", "observations"}
    if set(root) != required:
        raise SnapshotError(f"snapshot keys must be exactly: {', '.join(sorted(required))}")
    if root["schema_version"] != SCHEMA_VERSION:
        raise SnapshotError("unsupported readiness schema version")
    source = root["source_kind"]
    if source not in SOURCE_KINDS:
        raise SnapshotError("unknown source_kind")
    if source == "host" and not trusted:
        raise SnapshotError("host observations require a protected trusted adapter (not implemented)")
    date_text = _string(root["observed_at"], "observed_at", 40)
    try:
        observed_at = datetime.fromisoformat(date_text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SnapshotError("observed_at must be an ISO-8601 timestamp") from exc
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise SnapshotError("observed_at must include a timezone")
    label = _string(root["host_label"], "host_label", 120)
    raw_obs = _object(root["observations"], "observations")
    if set(raw_obs) != set(CATEGORIES):
        raise SnapshotError("observations must contain exactly the eight v1 categories")
    observations = {}
    for category in CATEGORIES:
        item = _object(raw_obs[category], category)
        if set(item) != {"status", "summary", "producer", "evidence_ref"}:
            raise SnapshotError(f"{category} must have status, summary, producer, evidence_ref")
        status = item["status"]
        if status not in STATUSES:
            raise SnapshotError(f"{category} has invalid status")
        summary = _string(item["summary"], f"{category}.summary")
        producer = _string(item["producer"], f"{category}.producer", 100)
        evidence = item["evidence_ref"]
        if evidence is not None:
            evidence = _string(evidence, f"{category}.evidence_ref", 300)
        if status == "verified" and evidence is None:
            raise SnapshotError(f"{category}: verified requires an evidence_ref")
        observations[category] = Observation(status, summary, producer, evidence)
    return Snapshot(SCHEMA_VERSION, source, observed_at, label, observations)


def assess(snapshot: Snapshot, *, now: datetime | None = None,
           max_age_seconds: int = 300) -> Assessment:
    """Fail closed for stale/future-dated host evidence; fixtures are always demos."""
    if max_age_seconds <= 0:
        raise ValueError("max_age_seconds must be positive")
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    if snapshot.source_kind == "host":
        age = now - snapshot.observed_at
        if age < timedelta(seconds=-60) or age > timedelta(seconds=max_age_seconds):
            return Assessment("unknown", False, "Protected observation expired or is future-dated")
    states = {obs.status for obs in snapshot.observations.values()}
    if "failed" in states:
        return Assessment("attention", True, "A host readiness check failed")
    if "degraded" in states:
        return Assessment("degraded", True, "A host readiness check is degraded")
    if "unknown" in states:
        return Assessment("unknown", True, "Required readiness evidence is missing")
    if "pending" in states:
        return Assessment("setup_pending", True, "Configuration is not yet complete")
    return Assessment("ready", True, "Every required observation is verified")
