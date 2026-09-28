"""Tests for session metadata parsing."""

from __future__ import annotations

from iracing_telemetry.metadata import (
    SessionMetadata,
    metadata_from_session_info,
    parse_session_info,
)

SAMPLE_SESSION_INFO = {
    "WeekendInfo": {
        "TrackName": "monza full",
        "TrackDisplayName": "Autodromo Nazionale Monza",
        "TrackConfigName": "",
        "TrackCity": "Monza",
        "TrackCountry": "Italy",
        "TrackLength": "5.7508 km",
        "TrackNumTurns": 11,
    },
    "DriverInfo": {
        "DriverCarIdx": 0,
        "Drivers": [
            {"CarIdx": 0, "UserName": "Kushal Hebbar", "CarScreenName": "Porsche 911 GT3 R (992)"},
            {"CarIdx": 1, "UserName": "Someone Else", "CarScreenName": "BMW M4 GT3"},
        ],
    },
}


class TestMetadataFromSessionInfo:
    def test_extracts_track_and_driver(self):
        md = metadata_from_session_info(SAMPLE_SESSION_INFO)
        assert md.track_display_name == "Autodromo Nazionale Monza"
        assert md.track_city == "Monza"
        assert md.num_turns == 11
        assert md.car == "Porsche 911 GT3 R (992)"
        assert md.driver == "Kushal Hebbar"

    def test_picks_the_driver_car_index(self):
        info = {**SAMPLE_SESSION_INFO, "DriverInfo": {**SAMPLE_SESSION_INFO["DriverInfo"], "DriverCarIdx": 1}}
        md = metadata_from_session_info(info)
        assert md.driver == "Someone Else"
        assert md.car == "BMW M4 GT3"

    def test_empty_info_yields_blank_metadata(self):
        md = metadata_from_session_info({})
        assert md == SessionMetadata()
        assert md.car is None


class TestSessionMetadataProperties:
    def test_track_label_without_config(self):
        md = metadata_from_session_info(SAMPLE_SESSION_INFO)
        assert md.track_label == "Autodromo Nazionale Monza"

    def test_track_label_with_config(self):
        info = {"WeekendInfo": {"TrackDisplayName": "Spa", "TrackConfigName": "Grand Prix"}}
        md = metadata_from_session_info(info)
        assert md.track_label == "Spa (Grand Prix)"

    def test_track_label_fallback(self):
        assert SessionMetadata().track_label == "Unknown track"

    def test_location(self):
        md = metadata_from_session_info(SAMPLE_SESSION_INFO)
        assert md.location == "Monza, Italy"

    def test_location_none_when_missing(self):
        assert SessionMetadata().location is None


class TestParseSessionInfo:
    def test_parses_yaml(self):
        raw = "---\nWeekendInfo:\n TrackDisplayName: Silverstone\n TrackNumTurns: 18\n"
        info = parse_session_info(raw)
        assert info["WeekendInfo"]["TrackDisplayName"] == "Silverstone"

    def test_bad_yaml_returns_empty_dict(self):
        assert parse_session_info(":\n  bad: : :") == {}

    def test_non_mapping_returns_empty_dict(self):
        assert parse_session_info("just a string") == {}
