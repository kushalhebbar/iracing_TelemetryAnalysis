"""Smoke tests for the Plotly figure builders and the figure assembler."""

from __future__ import annotations

import plotly.graph_objects as go

from iracing_telemetry import plotly_plots
from iracing_telemetry.plotly_plots import build_figures


def _valid_laps():
    return [1, 2]


def test_speed_traces_returns_figure(telemetry_df):
    fig = plotly_plots.plot_speed_traces(telemetry_df, _valid_laps())
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2  # one trace per lap


def test_speed_traces_units_label(telemetry_df):
    mph = plotly_plots.plot_speed_traces(telemetry_df, _valid_laps(), units="mph")
    kph = plotly_plots.plot_speed_traces(telemetry_df, _valid_laps(), units="kph")
    assert "mph" in mph.layout.yaxis.title.text
    assert "kph" in kph.layout.yaxis.title.text
    assert kph.data[0].y.max() > mph.data[0].y.max()


def test_throttle_brake_returns_figure(telemetry_df):
    fig = plotly_plots.plot_throttle_brake(telemetry_df, _valid_laps())
    assert isinstance(fig, go.Figure)


def test_brake_consistency_requires_two_laps(telemetry_df):
    assert plotly_plots.plot_brake_consistency(telemetry_df, [1]) is None
    fig = plotly_plots.plot_brake_consistency(telemetry_df, _valid_laps())
    assert isinstance(fig, go.Figure)


def test_delta_time_returns_figure(telemetry_df):
    fig = plotly_plots.plot_delta_time(telemetry_df, _valid_laps(), fastest_lap=1)
    assert isinstance(fig, go.Figure)


def test_track_map_returns_figure(telemetry_df):
    fig = plotly_plots.plot_track_map(telemetry_df, _valid_laps())
    assert isinstance(fig, go.Figure)


def test_track_map_none_without_gps(telemetry_df):
    df = telemetry_df.drop(columns=["Lat", "Lon"])
    assert plotly_plots.plot_track_map(df, _valid_laps()) is None


def test_sector_times_returns_figure(telemetry_df):
    fig = plotly_plots.plot_sector_times(telemetry_df, _valid_laps())
    assert isinstance(fig, go.Figure)


class TestBuildFigures:
    def test_returns_expected_sections(self, telemetry_df):
        figures = build_figures(telemetry_df, _valid_laps())
        assert "Speed Traces" in figures
        assert "Sector Times" in figures
        assert "Braking Points" in figures
        assert "Delta Time" in figures
        assert "Track Map" in figures

    def test_single_lap_skips_consistency_and_delta(self, telemetry_df):
        figures = build_figures(telemetry_df, [1])
        assert "Brake Consistency" not in figures
        assert "Delta Time" not in figures
        assert "Speed Traces" in figures

    def test_track_map_omitted_without_gps(self, telemetry_df):
        df = telemetry_df.drop(columns=["Lat", "Lon"])
        assert "Track Map" not in build_figures(df, _valid_laps())

