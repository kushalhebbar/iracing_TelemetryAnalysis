"""Read session metadata (track, car, driver, weather) from an .ibt file.

pyirsdk does not expose the session-info block for on-disk telemetry files, but
the YAML is still present in the file header. We read it directly and parse the
handful of fields worth surfacing in reports and the dashboard.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import irsdk
import yaml

logger = logging.getLogger("iracing_telemetry")


@dataclass(frozen=True)
class SessionMetadata:
    track_name: str | None = None
    track_display_name: str | None = None
    track_config: str | None = None
    track_city: str | None = None
    track_country: str | None = None
    track_length: str | None = None
    num_turns: int | None = None
    car: str | None = None
    driver: str | None = None

    @property
    def track_label(self) -> str:
        """Human-readable track name, including config where present."""
        name = self.track_display_name or self.track_name
        if not name:
            return "Unknown track"
        if self.track_config:
            return f"{name} ({self.track_config})"
        return name

    @property
    def location(self) -> str | None:
        parts = [p for p in (self.track_city, self.track_country) if p]
        return ", ".join(parts) if parts else None


def _read_session_info_yaml(ibt: irsdk.IBT) -> str | None:
    """Pull the raw session-info YAML string out of an open IBT's header."""
    header = ibt._header
    if header is None:
        return None
    offset = header.session_info_offset
    length = header.session_info_len
    if not length:
        return None
    raw = ibt._shared_mem[offset : offset + length]
    # The block is null-padded; keep only the text up to the first NUL.
    return raw.split(b"\x00", 1)[0].decode("latin-1", "ignore")


def parse_session_info(raw_yaml: str) -> dict:
    """Parse the session-info YAML text into a dict (empty on failure)."""
    try:
        data = yaml.safe_load(raw_yaml)
    except yaml.YAMLError as exc:
        logger.warning("Could not parse session-info YAML: %s", exc)
        return {}
    return data if isinstance(data, dict) else {}


def metadata_from_session_info(session_info: dict) -> SessionMetadata:
    """Build a SessionMetadata from a parsed session-info dict."""
    weekend = session_info.get("WeekendInfo") or {}

    driver_info = session_info.get("DriverInfo") or {}
    drivers = driver_info.get("Drivers") or []
    car_idx = driver_info.get("DriverCarIdx")
    me: dict = {}
    for driver in drivers:
        if driver.get("CarIdx") == car_idx:
            me = driver
            break
    if not me and drivers:
        me = drivers[0]

    turns = weekend.get("TrackNumTurns")
    return SessionMetadata(
        track_name=weekend.get("TrackName"),
        track_display_name=weekend.get("TrackDisplayName"),
        track_config=weekend.get("TrackConfigName") or None,
        track_city=weekend.get("TrackCity"),
        track_country=weekend.get("TrackCountry"),
        track_length=weekend.get("TrackLength"),
        num_turns=int(turns) if isinstance(turns, int) else None,
        car=me.get("CarScreenName"),
        driver=me.get("UserName"),
    )


def read_session_metadata(input_path: Path) -> SessionMetadata:
    """Open an .ibt file and return its session metadata (best-effort)."""
    ibt = irsdk.IBT()
    ibt.open(str(input_path))
    try:
        raw = _read_session_info_yaml(ibt)
    finally:
        ibt.close()

    if not raw:
        logger.info("No session-info block found in %s", input_path.name)
        return SessionMetadata()
    return metadata_from_session_info(parse_session_info(raw))
