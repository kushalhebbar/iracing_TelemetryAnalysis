"""Enhanced plotting using Plotly for interactive telemetry visualization."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from iracing_telemetry.utils import convert_speed_to_mph, format_lap_time, ms_to_mph

# Professional color scheme
COLOR_PALETTE = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E', '#8E44AD', '#3498DB', '#E67E22']
SPEED_COLOR = '#2E86AB'
THROTTLE_COLOR = '#6A994E'
BRAKE_COLOR = '#C73E1D'
FASTEST_LAP_COLOR = '#2ECC71'

# Plotly layout template
LAYOUT_TEMPLATE = {
    'template': 'plotly_white',
    'font': {'family': 'Arial, sans-serif', 'size': 12},
    'hovermode': 'x unified',
    'legend': {
        'orientation': 'v',
        'yanchor': 'top',
        'y': 0.99,
        'xanchor': 'right',
        'x': 0.99,
        'bgcolor': 'rgba(255, 255, 255, 0.8)',
        'bordercolor': '#CCCCCC',
        'borderwidth': 1
    }
}


def plot_speed_traces(df: pd.DataFrame, valid_laps: list, plots_dir: Path, base_name: str, save_png: bool = True) -> go.Figure:
    """Speed versus lap distance for each valid lap."""
    df = convert_speed_to_mph(df)
    
    fig = go.Figure()
    
    colors = [COLOR_PALETTE[i % len(COLOR_PALETTE)] for i in range(len(valid_laps))]
    
    for idx, lap in enumerate(valid_laps):
        lap_data = df[df['Lap'] == lap].sort_values('LapDistPct')
        lap_time = lap_data['SessionTime'].max() - lap_data['SessionTime'].min()
        lap_time_str = format_lap_time(lap_time)
        
        fig.add_trace(go.Scatter(
            x=lap_data['LapDistPct'] * 100,
            y=lap_data['Speed'],
            mode='lines',
            name=f'Lap {int(lap)} ({lap_time_str})',
            line=dict(color=colors[idx], width=3),
            hovertemplate='<b>%{fullData.name}</b><br>Distance: %{x:.1f}%<br>Speed: %{y:.1f} mph<extra></extra>'
        ))
    
    fig.update_layout(
        **LAYOUT_TEMPLATE,
        title=dict(text='<b>Speed Trace Comparison</b>', font=dict(size=20)),
        xaxis=dict(title='<b>Lap Distance (%)</b>', showgrid=True, gridcolor='#E5E5E5'),
        yaxis=dict(title='<b>Speed (mph)</b>', showgrid=True, gridcolor='#E5E5E5'),
        height=600,
        margin=dict(l=80, r=80, t=100, b=80)
    )
    
    # Save PNG with descriptive name
    if save_png:
        png_path = plots_dir / f"{base_name}_speed_traces.png"
        fig.write_image(str(png_path), width=1600, height=600, scale=2)

    return fig


def plot_throttle_brake(df: pd.DataFrame, valid_laps: list, plots_dir: Path, base_name: str, save_png: bool = True) -> go.Figure:
    """Throttle, brake and speed stacked in one subplot per lap."""
    df = convert_speed_to_mph(df)
    
    n_laps = len(valid_laps)
    
    # Create subplots with secondary y-axes
    fig = make_subplots(
        rows=n_laps, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=[f"Lap {int(lap)}" for lap in valid_laps],
        specs=[[{"secondary_y": True}] for _ in range(n_laps)]
    )
    
    for idx, lap in enumerate(valid_laps):
        lap_data = df[df['Lap'] == lap].sort_values('LapDistPct')
        lap_time = lap_data['SessionTime'].max() - lap_data['SessionTime'].min()
        lap_time_str = format_lap_time(lap_time)
        
        row = idx + 1
        
        # Throttle
        fig.add_trace(
            go.Scatter(
                x=lap_data['LapDistPct'] * 100,
                y=lap_data['Throttle'] * 100,
                mode='lines',
                name='Throttle',
                fill='tozeroy',
                line=dict(color=THROTTLE_COLOR, width=2),
                fillcolor='rgba(106, 153, 78, 0.3)',
                hovertemplate='Throttle: %{y:.1f}%<extra></extra>',
                legendgroup='inputs',
                showlegend=(idx == 0)
            ),
            row=row, col=1, secondary_y=False
        )
        
        # Brake
        fig.add_trace(
            go.Scatter(
                x=lap_data['LapDistPct'] * 100,
                y=lap_data['Brake'] * 100,
                mode='lines',
                name='Brake',
                fill='tozeroy',
                line=dict(color=BRAKE_COLOR, width=2),
                fillcolor='rgba(199, 62, 29, 0.3)',
                hovertemplate='Brake: %{y:.1f}%<extra></extra>',
                legendgroup='inputs',
                showlegend=(idx == 0)
            ),
            row=row, col=1, secondary_y=False
        )
        
        # Speed on secondary axis
        fig.add_trace(
            go.Scatter(
                x=lap_data['LapDistPct'] * 100,
                y=lap_data['Speed'],
                mode='lines',
                name='Speed',
                line=dict(color=SPEED_COLOR, width=2.5),
                hovertemplate='Speed: %{y:.1f} mph<extra></extra>',
                legendgroup='speed',
                showlegend=(idx == 0)
            ),
            row=row, col=1, secondary_y=True
        )
        
        # Update y-axes for this subplot
        fig.update_yaxes(title_text="<b>Input (%)</b>", range=[0, 105], row=row, col=1, secondary_y=False)
        fig.update_yaxes(title_text="<b>Speed (mph)</b>", row=row, col=1, secondary_y=True)
        
        # Add lap time to subplot title
        fig.layout.annotations[idx].update(text=f"<b>Lap {int(lap)} ({lap_time_str})</b>")
    
    fig.update_xaxes(title_text="<b>Lap Distance (%)</b>", row=n_laps, col=1)
    
    fig.update_layout(
        **LAYOUT_TEMPLATE,
        title=dict(text='<b>Throttle/Brake Inputs & Speed</b>', font=dict(size=20)),
        height=400 * n_laps,
        margin=dict(l=80, r=80, t=100, b=80)
    )
    
    # Save PNG only
    if save_png:
        png_path = plots_dir / f"{base_name}_throttle_brake.png"
        fig.write_image(str(png_path), width=1600, height=400 * n_laps, scale=2)

    return fig


def plot_braking_points(df: pd.DataFrame, valid_laps: list, plots_dir: Path, base_name: str, save_png: bool = True) -> list[go.Figure]:
    """Shade braking zones and mark the apex speed, one figure per lap."""
    df = convert_speed_to_mph(df)
    
    figures = []
    for lap in valid_laps:
        fig = go.Figure()
        
        lap_data = df[df['Lap'] == lap].sort_values('LapDistPct').reset_index(drop=True)
        lap_time = lap_data['SessionTime'].max() - lap_data['SessionTime'].min()
        lap_time_str = format_lap_time(lap_time)
        
        # Plot speed
        fig.add_trace(go.Scatter(
            x=lap_data['LapDistPct'] * 100,
            y=lap_data['Speed'],
            mode='lines',
            name='Speed',
            line=dict(color=SPEED_COLOR, width=3),
            hovertemplate='Speed: %{y:.1f} mph<extra></extra>'
        ))
        
        # Identify braking zones
        braking = lap_data['Brake'] > 0.1
        brake_start = braking & ~braking.shift(1, fill_value=False)
        brake_end = ~braking & braking.shift(1, fill_value=False)
        
        # Highlight braking zones
        brake_zones: list = []
        corner_apexes = []
        
        for idx in lap_data[brake_start].index:
            end_candidates = lap_data[brake_end & (lap_data.index > idx)]
            if len(end_candidates) > 0:
                end_idx = end_candidates.index[0]
                brake_zone_data = lap_data.loc[idx:end_idx]
                
                # Add shaded braking zone
                fig.add_vrect(
                    x0=brake_zone_data['LapDistPct'].iloc[0] * 100,
                    x1=brake_zone_data['LapDistPct'].iloc[-1] * 100,
                    fillcolor=BRAKE_COLOR,
                    opacity=0.15,
                    line_width=0,
                    annotation_text="Braking" if len(brake_zones) == 0 else "",
                    annotation_position="top left"
                )
                
                # Mark corner apex (minimum speed)
                min_speed_idx = brake_zone_data['Speed'].idxmin()
                min_speed = lap_data.loc[min_speed_idx, 'Speed']
                min_dist = lap_data.loc[min_speed_idx, 'LapDistPct'] * 100
                
                corner_apexes.append({
                    'x': min_dist,
                    'y': min_speed,
                    'text': f'{min_speed:.1f} mph'
                })
        
        # Add apex markers
        if corner_apexes:
            fig.add_trace(go.Scatter(
                x=[apex['x'] for apex in corner_apexes],
                y=[apex['y'] for apex in corner_apexes],
                mode='markers+text',
                name='Corner Apex',
                marker=dict(
                    color=BRAKE_COLOR,
                    size=12,
                    symbol='circle',
                    line=dict(color='white', width=2)
                ),
                text=[apex['text'] for apex in corner_apexes],
                textposition='top center',
                textfont=dict(size=10, color=BRAKE_COLOR),
                hovertemplate='Apex Speed: %{y:.1f} mph<extra></extra>'
            ))
        
        fig.update_layout(
            **LAYOUT_TEMPLATE,
            title=dict(text=f'<b>Braking Points & Corner Speeds - Lap {int(lap)} ({lap_time_str})</b>', font=dict(size=20)),
            xaxis=dict(title='<b>Lap Distance (%)</b>', showgrid=True, gridcolor='#E5E5E5'),
            yaxis=dict(title='<b>Speed (mph)</b>', showgrid=True, gridcolor='#E5E5E5'),
            height=600,
            margin=dict(l=80, r=80, t=100, b=80)
        )
        
        # Save PNG only
        if save_png:
            png_path = plots_dir / f"{base_name}_braking_points_lap{int(lap)}.png"
            fig.write_image(str(png_path), width=1600, height=600, scale=2)
        
        figures.append(fig)

    return figures


def plot_racing_line(df: pd.DataFrame, valid_laps: list, plots_dir: Path, base_name: str, save_png: bool = True) -> go.Figure | None:
    """Lateral acceleration trace, used here as a racing-line proxy."""
    fig = go.Figure()
    
    colors = [COLOR_PALETTE[i % len(COLOR_PALETTE)] for i in range(len(valid_laps))]
    
    for idx, lap in enumerate(valid_laps):
        lap_data = df[df['Lap'] == lap].sort_values('LapDistPct')
        
        fig.add_trace(go.Scatter(
            x=lap_data['LapDistPct'] * 100,
            y=lap_data['LatAccel'],
            mode='lines',
            name=f'Lap {int(lap)}',
            line=dict(color=colors[idx], width=3),
            hovertemplate='Lap %{fullData.name}<br>Lat G: %{y:.2f}<extra></extra>'
        ))
    
    # Add zero reference line
    fig.add_hline(y=0, line_dash="dash", line_color="#666666", opacity=0.5)
    
    fig.update_layout(
        **LAYOUT_TEMPLATE,
        title=dict(text='<b>Lateral Acceleration (Racing Line Indicator)</b>', font=dict(size=20)),
        xaxis=dict(title='<b>Lap Distance (%)</b>', showgrid=True, gridcolor='#E5E5E5'),
        yaxis=dict(title='<b>Lateral Acceleration (G)</b>', showgrid=True, gridcolor='#E5E5E5'),
        height=600,
        margin=dict(l=80, r=80, t=100, b=80)
    )
    
    # Save PNG only
    if save_png:
        png_path = plots_dir / f"{base_name}_racing_line_lateral_g.png"
        fig.write_image(str(png_path), width=1600, height=600, scale=2)

    return fig


def plot_brake_consistency(df: pd.DataFrame, valid_laps: list, plots_dir: Path, base_name: str, save_png: bool = True) -> go.Figure | None:
    """Overlay every lap's brake and speed trace to show consistency."""
    if len(valid_laps) < 2:
        return None
    
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=["<b>Brake Consistency - All Laps Overlaid</b>", "<b>Speed Consistency</b>"]
    )
    
    colors = [COLOR_PALETTE[i % len(COLOR_PALETTE)] for i in range(len(valid_laps))]
    
    for idx, lap in enumerate(valid_laps):
        lap_data = df[df['Lap'] == lap].sort_values('LapDistPct')
        lap_time = lap_data['SessionTime'].max() - lap_data['SessionTime'].min()
        lap_time_str = format_lap_time(lap_time)
        
        # Brake overlay
        fig.add_trace(
            go.Scatter(
                x=lap_data['LapDistPct'] * 100,
                y=lap_data['Brake'] * 100,
                mode='lines',
                name=f'Lap {int(lap)} ({lap_time_str})',
                line=dict(color=colors[idx], width=2.5),
                hovertemplate='Brake: %{y:.1f}%<extra></extra>',
                legendgroup=f'lap{lap}',
                showlegend=True
            ),
            row=1, col=1
        )
        
        # Speed overlay
        lap_data_speed = lap_data.copy()
        lap_data_speed['Speed'] = lap_data_speed['Speed'] * ms_to_mph()
        fig.add_trace(
            go.Scatter(
                x=lap_data_speed['LapDistPct'] * 100,
                y=lap_data_speed['Speed'],
                mode='lines',
                name=f'Lap {int(lap)}',
                line=dict(color=colors[idx], width=2.5),
                hovertemplate='Speed: %{y:.1f} mph<extra></extra>',
                legendgroup=f'lap{lap}',
                showlegend=False
            ),
            row=2, col=1
        )
    
    fig.update_xaxes(title_text="<b>Lap Distance (%)</b>", row=2, col=1)
    fig.update_yaxes(title_text="<b>Brake (%)</b>", range=[0, 105], row=1, col=1)
    fig.update_yaxes(title_text="<b>Speed (mph)</b>", row=2, col=1)
    
    fig.update_layout(
        **LAYOUT_TEMPLATE,
        height=800,
        margin=dict(l=80, r=80, t=100, b=80)
    )
    
    if save_png:
        png_path = plots_dir / f"{base_name}_brake_consistency_overlay.png"
        fig.write_image(str(png_path), width=1600, height=800, scale=2)

    return fig


def plot_throttle_consistency(df: pd.DataFrame, valid_laps: list, plots_dir: Path, base_name: str, save_png: bool = True) -> go.Figure | None:
    """Overlay every lap's throttle and speed trace to show consistency."""
    if len(valid_laps) < 2:
        return None
    
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=["<b>Throttle Consistency - All Laps Overlaid</b>", "<b>Speed Consistency</b>"]
    )
    
    colors = [COLOR_PALETTE[i % len(COLOR_PALETTE)] for i in range(len(valid_laps))]
    
    for idx, lap in enumerate(valid_laps):
        lap_data = df[df['Lap'] == lap].sort_values('LapDistPct')
        lap_time = lap_data['SessionTime'].max() - lap_data['SessionTime'].min()
        lap_time_str = format_lap_time(lap_time)
        
        # Throttle overlay
        fig.add_trace(
            go.Scatter(
                x=lap_data['LapDistPct'] * 100,
                y=lap_data['Throttle'] * 100,
                mode='lines',
                name=f'Lap {int(lap)} ({lap_time_str})',
                line=dict(color=colors[idx], width=2.5),
                hovertemplate='Throttle: %{y:.1f}%<extra></extra>',
                legendgroup=f'lap{lap}',
                showlegend=True
            ),
            row=1, col=1
        )
        
        # Speed overlay
        lap_data_speed = lap_data.copy()
        lap_data_speed['Speed'] = lap_data_speed['Speed'] * ms_to_mph()
        fig.add_trace(
            go.Scatter(
                x=lap_data_speed['LapDistPct'] * 100,
                y=lap_data_speed['Speed'],
                mode='lines',
                name=f'Lap {int(lap)}',
                line=dict(color=colors[idx], width=2.5),
                hovertemplate='Speed: %{y:.1f} mph<extra></extra>',
                legendgroup=f'lap{lap}',
                showlegend=False
            ),
            row=2, col=1
        )
    
    fig.update_xaxes(title_text="<b>Lap Distance (%)</b>", row=2, col=1)
    fig.update_yaxes(title_text="<b>Throttle (%)</b>", range=[0, 105], row=1, col=1)
    fig.update_yaxes(title_text="<b>Speed (mph)</b>", row=2, col=1)
    
    fig.update_layout(
        **LAYOUT_TEMPLATE,
        height=800,
        margin=dict(l=80, r=80, t=100, b=80)
    )
    
    if save_png:
        png_path = plots_dir / f"{base_name}_throttle_consistency_overlay.png"
        fig.write_image(str(png_path), width=1600, height=800, scale=2)

    return fig


def plot_brake_trace(df: pd.DataFrame, valid_laps: list, plots_dir: Path, base_name: str, save_png: bool = True) -> list[go.Figure]:
    """Brake pressure and speed for each lap."""
    df = convert_speed_to_mph(df)
    figures = []
    
    for lap in valid_laps:
        lap_data = df[df['Lap'] == lap].sort_values('LapDistPct')
        lap_time = lap_data['SessionTime'].max() - lap_data['SessionTime'].min()
        lap_time_str = format_lap_time(lap_time)
        
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            subplot_titles=[f"<b>Brake Pressure - Lap {int(lap)} ({lap_time_str})</b>", "<b>Speed</b>"]
        )
        
        # Brake pressure
        fig.add_trace(
            go.Scatter(
                x=lap_data['LapDistPct'] * 100,
                y=lap_data['Brake'] * 100,
                mode='lines',
                name='Brake',
                fill='tozeroy',
                line=dict(color=BRAKE_COLOR, width=2.5),
                fillcolor='rgba(199, 62, 29, 0.3)',
                hovertemplate='Brake: %{y:.1f}%<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Speed
        fig.add_trace(
            go.Scatter(
                x=lap_data['LapDistPct'] * 100,
                y=lap_data['Speed'],
                mode='lines',
                name='Speed',
                line=dict(color=SPEED_COLOR, width=2.5),
                hovertemplate='Speed: %{y:.1f} mph<extra></extra>'
            ),
            row=2, col=1
        )
        
        fig.update_xaxes(title_text="<b>Lap Distance (%)</b>", row=2, col=1)
        fig.update_yaxes(title_text="<b>Brake (%)</b>", range=[0, 105], row=1, col=1)
        fig.update_yaxes(title_text="<b>Speed (mph)</b>", row=2, col=1)
        
        fig.update_layout(
            **LAYOUT_TEMPLATE,
            height=700,
            margin=dict(l=80, r=80, t=100, b=80)
        )
        
        if save_png:
            png_path = plots_dir / f"{base_name}_brake_trace_lap{int(lap)}.png"
            fig.write_image(str(png_path), width=1600, height=700, scale=2)
        
        figures.append(fig)
    

    return figures


def plot_delta_time(df: pd.DataFrame, valid_laps: list, fastest_lap: int, plots_dir: Path, base_name: str, save_png: bool = True) -> go.Figure | None:
    """Time delta to the fastest lap at each point, with a speed comparison."""
    from scipy import interpolate
    
    if len(valid_laps) < 2:
        return None
    
    df = convert_speed_to_mph(df)
    fastest_data = df[df['Lap'] == fastest_lap].sort_values('LapDistPct')
    
    # Create interpolation function for fastest lap
    fastest_interp = interpolate.interp1d(
        fastest_data['LapDistPct'],
        fastest_data['SessionTime'] - fastest_data['SessionTime'].min(),
        kind='linear',
        fill_value='extrapolate'
    )
    
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=[
            f"<b>Delta Time vs Fastest Lap ({int(fastest_lap)})</b>",
            "<b>Speed Comparison</b>"
        ]
    )
    
    colors = [COLOR_PALETTE[i % len(COLOR_PALETTE)] for i in range(len(valid_laps))]
    
    for idx, lap in enumerate(valid_laps):
        if lap == fastest_lap:
            continue
        
        lap_data = df[df['Lap'] == lap].sort_values('LapDistPct')
        lap_elapsed = lap_data['SessionTime'] - lap_data['SessionTime'].min()
        fastest_at_same_dist = fastest_interp(lap_data['LapDistPct'])
        delta = lap_elapsed.values - fastest_at_same_dist
        
        # Delta time plot
        fig.add_trace(go.Scatter(
            x=lap_data['LapDistPct'] * 100,
            y=delta,
            mode='lines',
            name=f'Lap {int(lap)}',
            line=dict(color=colors[idx], width=2),
            hovertemplate='<b>Lap %{fullData.name}</b><br>Distance: %{x:.1f}%<br>Delta: %{y:.2f}s<extra></extra>'
        ), row=1, col=1)
        
        # Speed comparison
        fig.add_trace(go.Scatter(
            x=lap_data['LapDistPct'] * 100,
            y=lap_data['Speed'],
            mode='lines',
            name=f'Lap {int(lap)}',
            line=dict(color=colors[idx], width=2),
            showlegend=False,
            hovertemplate='<b>Lap %{fullData.name}</b><br>Speed: %{y:.1f} mph<extra></extra>'
        ), row=2, col=1)
    
    # Add zero line for delta
    fig.add_hline(y=0, line=dict(color='green', width=2, dash='dash'), row=1, col=1)
    
    # Add fastest lap speed
    fig.add_trace(go.Scatter(
        x=fastest_data['LapDistPct'] * 100,
        y=fastest_data['Speed'],
        mode='lines',
        name=f'Fastest (Lap {int(fastest_lap)})',
        line=dict(color='green', width=2, dash='dash'),
        hovertemplate='<b>Fastest Lap</b><br>Speed: %{y:.1f} mph<extra></extra>'
    ), row=2, col=1)
    
    fig.update_xaxes(title_text="<b>Lap Distance (%)</b>", row=2, col=1)
    fig.update_yaxes(title_text="<b>Delta Time (seconds)</b>", row=1, col=1)
    fig.update_yaxes(title_text="<b>Speed (mph)</b>", row=2, col=1)
    
    fig.update_layout(
        **LAYOUT_TEMPLATE,
        height=800,
        margin=dict(l=80, r=80, t=120, b=80)
    )
    
    if save_png:
        png_path = plots_dir / f"{base_name}_delta_time_analysis.png"
        fig.write_image(str(png_path), width=1600, height=800, scale=2)

    return fig


def plot_track_map(df: pd.DataFrame, valid_laps: list, plots_dir: Path, base_name: str, save_png: bool = True) -> go.Figure | None:
    """GPS racing line coloured by speed alongside a line-consistency view."""
    if 'Lat' not in df.columns or 'Lon' not in df.columns:
        return None
    
    df = convert_speed_to_mph(df)
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=["<b>Racing Line (colored by speed)</b>", "<b>Racing Line Consistency</b>"],
        specs=[[{"type": "scatter"}, {"type": "scatter"}]]
    )
    
    colors = [COLOR_PALETTE[i % len(COLOR_PALETTE)] for i in range(len(valid_laps))]
    
    for idx, lap in enumerate(valid_laps):
        lap_data = df[df['Lap'] == lap].sort_values('LapDistPct')
        
        # Map 1: Colored by speed
        fig.add_trace(go.Scatter(
            x=lap_data['Lon'],
            y=lap_data['Lat'],
            mode='markers+lines',
            marker=dict(
                color=lap_data['Speed'],
                colorscale='RdYlGn',
                size=3,
                showscale=(idx == 0),
                colorbar=dict(title="Speed (mph)", x=0.45) if idx == 0 else None
            ),
            line=dict(color=colors[idx], width=1),
            name=f'Lap {int(lap)}',
            showlegend=False,
            hovertemplate='<b>Lap %{fullData.name}</b><br>Speed: %{marker.color:.1f} mph<extra></extra>'
        ), row=1, col=1)
        
        # Map 2: Line comparison
        fig.add_trace(go.Scatter(
            x=lap_data['Lon'],
            y=lap_data['Lat'],
            mode='lines',
            line=dict(color=colors[idx], width=3),
            name=f'Lap {int(lap)}',
            hovertemplate='<b>Lap %{fullData.name}</b><extra></extra>'
        ), row=1, col=2)
    
    fig.update_xaxes(title_text="<b>Longitude</b>", scaleanchor="y", scaleratio=1, row=1, col=1)
    fig.update_yaxes(title_text="<b>Latitude</b>", row=1, col=1)
    fig.update_xaxes(title_text="<b>Longitude</b>", scaleanchor="y2", scaleratio=1, row=1, col=2)
    fig.update_yaxes(title_text="<b>Latitude</b>", row=1, col=2)
    
    fig.update_layout(
        **LAYOUT_TEMPLATE,
        height=600,
        margin=dict(l=80, r=80, t=100, b=80)
    )
    
    if save_png:
        png_path = plots_dir / f"{base_name}_track_map_gps.png"
        fig.write_image(str(png_path), width=1600, height=600, scale=2)

    return fig


def create_combined_html(figures_dict: dict, plots_dir: Path, base_name: str) -> None:
    """Create a single HTML file with all plots organized in sections."""
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Telemetry Analysis - {base_name}</title>
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js" charset="utf-8"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #2E86AB 0%, #1a5276 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0;
            font-size: 32px;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .section {{
            background: white;
            padding: 25px;
            margin-bottom: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            margin-top: 0;
            color: #2E86AB;
            border-bottom: 3px solid #2E86AB;
            padding-bottom: 10px;
        }}
        .plot-container {{
            margin: 20px 0;
        }}
        .info-box {{
            background: #e3f2fd;
            border-left: 4px solid #2E86AB;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>iRacing Telemetry Analysis</h1>
        <p>Session: {base_name}</p>
    </div>
    
    <div class="info-box">
        <strong>Interactive features:</strong> Hover for values, click-drag to zoom, double-click to reset, click legend items to toggle traces
    </div>
"""
    
    plot_id = 0
    
    # Add each section
    for section_name, figures in figures_dict.items():
        if not figures:
            continue
        
        html_content += f"""
    <div class="section">
        <h2>{section_name}</h2>
"""
        
        if isinstance(figures, list):
            for fig in figures:
                if fig:
                    plot_id += 1
                    div_id = f"plot_{plot_id}"
                    # Convert each trace to dict, then manually convert numpy arrays
                    data_list = []
                    for trace in fig.data:
                        trace_dict = trace.to_plotly_json()
                        # Convert any numpy arrays in the trace dict to lists
                        for key, val in trace_dict.items():
                            if isinstance(val, np.ndarray):
                                trace_dict[key] = val.tolist()
                        data_list.append(trace_dict)
                    
                    layout_dict = fig.layout.to_plotly_json()
                    fig_json = json.dumps({"data": data_list, "layout": layout_dict})
                    
                    html_content += f"""
        <div class="plot-container">
            <div id="{div_id}" style="width:100%;height:600px;"></div>
            <script>
                var plotData = {fig_json};
                Plotly.newPlot('{div_id}', plotData.data, plotData.layout, {{responsive: true}});
            </script>
        </div>
"""
        else:
            if figures:
                plot_id += 1
                div_id = f"plot_{plot_id}"
                # Convert each trace to dict, then manually convert numpy arrays
                data_list = []
                for trace in figures.data:
                    trace_dict = trace.to_plotly_json()
                    # Convert any numpy arrays in the trace dict to lists
                    for key, val in trace_dict.items():
                        if isinstance(val, np.ndarray):
                            trace_dict[key] = val.tolist()
                    data_list.append(trace_dict)
                
                layout_dict = figures.layout.to_plotly_json()
                fig_json = json.dumps({"data": data_list, "layout": layout_dict})
                
                html_content += f"""
        <div class="plot-container">
            <div id="{div_id}" style="width:100%;height:600px;"></div>
            <script>
                var plotData = {fig_json};
                Plotly.newPlot('{div_id}', plotData.data, plotData.layout, {{responsive: true}});
            </script>
        </div>
"""
        
        html_content += "    </div>\n"
    
    html_content += """
</body>
</html>
"""
    
    html_path = plots_dir / f"{base_name}_telemetry_report.html"
    html_path.write_text(html_content)
