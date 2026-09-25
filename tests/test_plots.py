"""Smoke tests for the Plotly figure and HTML builders.

These run the plotting code paths with ``save_png=False`` so they exercise
figure construction (and the combined-HTML writer) without requiring Kaleido or
a display.
"""

from __future__ import annotations

import plotly.graph_objects as go

from iracing_telemetry import plotly_plots


def _valid_laps():
    return [1, 2]


def test_speed_traces_returns_figure(telemetry_df, tmp_path):
    fig = plotly_plots.plot_speed_traces(
        telemetry_df, _valid_laps(), tmp_path, "sample", save_png=False
    )
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2  # one trace per lap


def test_throttle_brake_returns_figure(telemetry_df, tmp_path):
    fig = plotly_plots.plot_throttle_brake(
        telemetry_df, _valid_laps(), tmp_path, "sample", save_png=False
    )
    assert isinstance(fig, go.Figure)


def test_brake_consistency_requires_two_laps(telemetry_df, tmp_path):
    assert (
        plotly_plots.plot_brake_consistency(
            telemetry_df, [1], tmp_path, "sample", save_png=False
        )
        is None
    )
    fig = plotly_plots.plot_brake_consistency(
        telemetry_df, _valid_laps(), tmp_path, "sample", save_png=False
    )
    assert isinstance(fig, go.Figure)


def test_delta_time_returns_figure(telemetry_df, tmp_path):
    fig = plotly_plots.plot_delta_time(
        telemetry_df, _valid_laps(), fastest_lap=1, plots_dir=tmp_path,
        base_name="sample", save_png=False,
    )
    assert isinstance(fig, go.Figure)


def test_track_map_returns_figure(telemetry_df, tmp_path):
    fig = plotly_plots.plot_track_map(
        telemetry_df, _valid_laps(), tmp_path, "sample", save_png=False
    )
    assert isinstance(fig, go.Figure)


def test_track_map_none_without_gps(telemetry_df, tmp_path):
    df = telemetry_df.drop(columns=["Lat", "Lon"])
    assert (
        plotly_plots.plot_track_map(df, _valid_laps(), tmp_path, "sample", save_png=False)
        is None
    )


def test_create_combined_html_writes_report(telemetry_df, tmp_path):
    speed = plotly_plots.plot_speed_traces(
        telemetry_df, _valid_laps(), tmp_path, "sample", save_png=False
    )
    braking = plotly_plots.plot_braking_points(
        telemetry_df, _valid_laps(), tmp_path, "sample", save_png=False
    )
    plotly_plots.create_combined_html(
        {"Speed Traces": speed, "Braking Points": braking}, tmp_path, "sample"
    )
    report = tmp_path / "sample_telemetry_report.html"
    assert report.exists()
    content = report.read_text()
    assert "Plotly.newPlot" in content
    assert "iRacing Telemetry Analysis" in content
