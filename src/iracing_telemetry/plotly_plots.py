"""Interactive Plotly figures for telemetry visualization."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from iracing_telemetry.balance import balance_trace, compute_balance
from iracing_telemetry.sectors import compute_sector_times, theoretical_best
from iracing_telemetry.utils import (
    Units,
    convert_speed,
    format_lap_time,
    speed_factor,
    speed_label,
)

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


def plot_speed_traces(df: pd.DataFrame, valid_laps: list, units: Units = "mph") -> go.Figure:
    """Speed versus lap distance for each valid lap."""
    df = convert_speed(df, units)
    slabel = speed_label(units)
    
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
            hovertemplate='<b>%{fullData.name}</b><br>Distance: %{x:.1f}%<br>Speed: %{y:.1f} ' + slabel + '<extra></extra>'
        ))
    
    fig.update_layout(
        **LAYOUT_TEMPLATE,
        title=dict(text='<b>Speed Trace Comparison</b>', font=dict(size=20)),
        xaxis=dict(title='<b>Lap Distance (%)</b>', showgrid=True, gridcolor='#E5E5E5'),
        yaxis=dict(title=f'<b>Speed ({slabel})</b>', showgrid=True, gridcolor='#E5E5E5'),
        height=600,
        margin=dict(l=80, r=80, t=100, b=80)
    )

    return fig


def plot_throttle_brake(df: pd.DataFrame, valid_laps: list, units: Units = "mph") -> go.Figure:
    """Throttle, brake and speed stacked in one subplot per lap."""
    df = convert_speed(df, units)
    slabel = speed_label(units)
    
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
                hovertemplate='Speed: %{y:.1f} ' + slabel + '<extra></extra>',
                legendgroup='speed',
                showlegend=(idx == 0)
            ),
            row=row, col=1, secondary_y=True
        )
        
        # Update y-axes for this subplot
        fig.update_yaxes(title_text="<b>Input (%)</b>", range=[0, 105], row=row, col=1, secondary_y=False)
        fig.update_yaxes(title_text=f"<b>Speed ({slabel})</b>", row=row, col=1, secondary_y=True)
        
        # Add lap time to subplot title
        fig.layout.annotations[idx].update(text=f"<b>Lap {int(lap)} ({lap_time_str})</b>")
    
    fig.update_xaxes(title_text="<b>Lap Distance (%)</b>", row=n_laps, col=1)
    
    fig.update_layout(
        **LAYOUT_TEMPLATE,
        title=dict(text='<b>Throttle/Brake Inputs & Speed</b>', font=dict(size=20)),
        height=400 * n_laps,
        margin=dict(l=80, r=80, t=100, b=80)
    )

    return fig


def plot_braking_points(df: pd.DataFrame, valid_laps: list, units: Units = "mph") -> list[go.Figure]:
    """Shade braking zones and mark the apex speed, one figure per lap."""
    df = convert_speed(df, units)
    slabel = speed_label(units)
    
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
            hovertemplate='Speed: %{y:.1f} ' + slabel + '<extra></extra>'
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
                    'text': f'{min_speed:.1f} ' + slabel
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
                hovertemplate='Apex Speed: %{y:.1f} ' + slabel + '<extra></extra>'
            ))
        
        fig.update_layout(
            **LAYOUT_TEMPLATE,
            title=dict(text=f'<b>Braking Points & Corner Speeds - Lap {int(lap)} ({lap_time_str})</b>', font=dict(size=20)),
            xaxis=dict(title='<b>Lap Distance (%)</b>', showgrid=True, gridcolor='#E5E5E5'),
            yaxis=dict(title=f'<b>Speed ({slabel})</b>', showgrid=True, gridcolor='#E5E5E5'),
            height=600,
            margin=dict(l=80, r=80, t=100, b=80)
        )
        
        figures.append(fig)

    return figures


def plot_racing_line(df: pd.DataFrame, valid_laps: list) -> go.Figure | None:
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

    return fig


def plot_brake_consistency(df: pd.DataFrame, valid_laps: list, units: Units = "mph") -> go.Figure | None:
    """Overlay every lap's brake and speed trace to show consistency."""
    if len(valid_laps) < 2:
        return None

    slabel = speed_label(units)
    
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
        lap_data_speed['Speed'] = lap_data_speed['Speed'] * speed_factor(units)
        fig.add_trace(
            go.Scatter(
                x=lap_data_speed['LapDistPct'] * 100,
                y=lap_data_speed['Speed'],
                mode='lines',
                name=f'Lap {int(lap)}',
                line=dict(color=colors[idx], width=2.5),
                hovertemplate='Speed: %{y:.1f} ' + slabel + '<extra></extra>',
                legendgroup=f'lap{lap}',
                showlegend=False
            ),
            row=2, col=1
        )
    
    fig.update_xaxes(title_text="<b>Lap Distance (%)</b>", row=2, col=1)
    fig.update_yaxes(title_text="<b>Brake (%)</b>", range=[0, 105], row=1, col=1)
    fig.update_yaxes(title_text=f"<b>Speed ({slabel})</b>", row=2, col=1)
    
    fig.update_layout(
        **LAYOUT_TEMPLATE,
        height=800,
        margin=dict(l=80, r=80, t=100, b=80)
    )

    return fig


def plot_throttle_consistency(df: pd.DataFrame, valid_laps: list, units: Units = "mph") -> go.Figure | None:
    """Overlay every lap's throttle and speed trace to show consistency."""
    if len(valid_laps) < 2:
        return None

    slabel = speed_label(units)
    
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
        lap_data_speed['Speed'] = lap_data_speed['Speed'] * speed_factor(units)
        fig.add_trace(
            go.Scatter(
                x=lap_data_speed['LapDistPct'] * 100,
                y=lap_data_speed['Speed'],
                mode='lines',
                name=f'Lap {int(lap)}',
                line=dict(color=colors[idx], width=2.5),
                hovertemplate='Speed: %{y:.1f} ' + slabel + '<extra></extra>',
                legendgroup=f'lap{lap}',
                showlegend=False
            ),
            row=2, col=1
        )
    
    fig.update_xaxes(title_text="<b>Lap Distance (%)</b>", row=2, col=1)
    fig.update_yaxes(title_text="<b>Throttle (%)</b>", range=[0, 105], row=1, col=1)
    fig.update_yaxes(title_text=f"<b>Speed ({slabel})</b>", row=2, col=1)
    
    fig.update_layout(
        **LAYOUT_TEMPLATE,
        height=800,
        margin=dict(l=80, r=80, t=100, b=80)
    )

    return fig


def plot_brake_trace(df: pd.DataFrame, valid_laps: list, units: Units = "mph") -> list[go.Figure]:
    """Brake pressure and speed for each lap."""
    df = convert_speed(df, units)
    slabel = speed_label(units)
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
                hovertemplate='Speed: %{y:.1f} ' + slabel + '<extra></extra>'
            ),
            row=2, col=1
        )
        
        fig.update_xaxes(title_text="<b>Lap Distance (%)</b>", row=2, col=1)
        fig.update_yaxes(title_text="<b>Brake (%)</b>", range=[0, 105], row=1, col=1)
        fig.update_yaxes(title_text=f"<b>Speed ({slabel})</b>", row=2, col=1)
        
        fig.update_layout(
            **LAYOUT_TEMPLATE,
            height=700,
            margin=dict(l=80, r=80, t=100, b=80)
        )
        
        figures.append(fig)

    return figures


def plot_delta_time(df: pd.DataFrame, valid_laps: list, fastest_lap: int, units: Units = "mph") -> go.Figure | None:
    """Time delta to the fastest lap at each point, with a speed comparison."""
    from scipy import interpolate

    if len(valid_laps) < 2:
        return None

    df = convert_speed(df, units)
    slabel = speed_label(units)
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
            hovertemplate='<b>Lap %{fullData.name}</b><br>Speed: %{y:.1f} ' + slabel + '<extra></extra>'
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
        hovertemplate='<b>Fastest Lap</b><br>Speed: %{y:.1f} ' + slabel + '<extra></extra>'
    ), row=2, col=1)
    
    fig.update_xaxes(title_text="<b>Lap Distance (%)</b>", row=2, col=1)
    fig.update_yaxes(title_text="<b>Delta Time (seconds)</b>", row=1, col=1)
    fig.update_yaxes(title_text=f"<b>Speed ({slabel})</b>", row=2, col=1)
    
    fig.update_layout(
        **LAYOUT_TEMPLATE,
        height=800,
        margin=dict(l=80, r=80, t=120, b=80)
    )

    return fig


def plot_track_map(df: pd.DataFrame, valid_laps: list, units: Units = "mph") -> go.Figure | None:
    """GPS racing line coloured by speed alongside a line-consistency view."""
    if 'Lat' not in df.columns or 'Lon' not in df.columns:
        return None

    df = convert_speed(df, units)
    slabel = speed_label(units)
    
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
                colorbar=dict(title=f"Speed ({slabel})", x=0.45) if idx == 0 else None
            ),
            line=dict(color=colors[idx], width=1),
            name=f'Lap {int(lap)}',
            showlegend=False,
            hovertemplate='<b>Lap %{fullData.name}</b><br>Speed: %{marker.color:.1f} ' + slabel + '<extra></extra>'
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

    return fig


def plot_sector_times(df: pd.DataFrame, valid_laps: list, n_sectors: int | None = None) -> go.Figure | None:
    """Grouped sector-time bars per lap, with the theoretical best overlaid."""
    sector_times = compute_sector_times(df, valid_laps, n_sectors)
    if sector_times.empty:
        return None

    fig = go.Figure()
    for idx, lap in enumerate(sector_times.columns):
        fig.add_trace(go.Bar(
            x=sector_times.index,
            y=sector_times[lap],
            name=f'Lap {int(lap)}',
            marker_color=COLOR_PALETTE[idx % len(COLOR_PALETTE)],
            hovertemplate='Sector %{x}<br>%{y:.3f}s<extra></extra>'
        ))

    best = theoretical_best(sector_times)
    if best is not None:
        fig.add_trace(go.Scatter(
            x=sector_times.index,
            y=best.best_sector_times,
            mode='lines+markers',
            name='Theoretical best',
            line=dict(color=FASTEST_LAP_COLOR, width=3, dash='dash'),
            marker=dict(size=8),
            hovertemplate='Sector %{x}<br>Best: %{y:.3f}s<extra></extra>'
        ))

    fig.update_layout(
        **LAYOUT_TEMPLATE,
        barmode='group',
        title=dict(text='<b>Sector Times</b>', font=dict(size=20)),
        xaxis=dict(title='<b>Sector</b>', dtick=1, showgrid=False),
        yaxis=dict(title='<b>Time (s)</b>', showgrid=True, gridcolor='#E5E5E5'),
        height=500,
        margin=dict(l=80, r=80, t=100, b=80)
    )

    return fig


def plot_balance(df: pd.DataFrame, valid_laps: list) -> go.Figure | None:
    """Understeer (+) / oversteer (-) balance around the lap, per lap."""
    if compute_balance(df, valid_laps) == []:
        return None

    fig = go.Figure()
    has_data = False
    for idx, lap in enumerate(valid_laps):
        trace = balance_trace(df, lap)
        if trace["Balance"].notna().sum() == 0:
            continue
        has_data = True
        fig.add_trace(go.Scatter(
            x=trace["LapDistPct"] * 100,
            y=trace["Balance"],
            mode='lines',
            name=f'Lap {int(lap)}',
            connectgaps=False,
            line=dict(color=COLOR_PALETTE[idx % len(COLOR_PALETTE)], width=2.5),
            hovertemplate='Distance: %{x:.1f}%<br>Balance: %{y:+.2f}<extra></extra>'
        ))

    if not has_data:
        return None

    fig.add_hline(y=0, line_dash="dash", line_color="#666666", opacity=0.6)
    fig.update_layout(
        **LAYOUT_TEMPLATE,
        title=dict(text='<b>Balance — Understeer (+) / Oversteer (−)</b>', font=dict(size=20)),
        xaxis=dict(title='<b>Lap Distance (%)</b>', showgrid=True, gridcolor='#E5E5E5'),
        yaxis=dict(title='<b>Balance index</b>', showgrid=True, gridcolor='#E5E5E5'),
        height=500,
        margin=dict(l=80, r=80, t=100, b=80)
    )
    return fig


def build_figures(df: pd.DataFrame, valid_laps: list, units: Units = "mph") -> dict:
    """Build every figure for a session, keyed by display section name.

    Values are either a single Figure or a list of Figures (per-lap plots).
    Sections with no data (e.g. consistency with a single lap) are omitted.
    """
    figures: dict = {}
    figures["Speed Traces"] = plot_speed_traces(df, valid_laps, units)
    figures["Throttle / Brake Inputs"] = plot_throttle_brake(df, valid_laps, units)
    figures["Brake Traces"] = plot_brake_trace(df, valid_laps, units)

    sector_times = plot_sector_times(df, valid_laps)
    if sector_times:
        figures["Sector Times"] = sector_times

    balance = plot_balance(df, valid_laps)
    if balance:
        figures["Balance"] = balance

    brake_consistency = plot_brake_consistency(df, valid_laps, units)
    if brake_consistency:
        figures["Brake Consistency"] = brake_consistency

    throttle_consistency = plot_throttle_consistency(df, valid_laps, units)
    if throttle_consistency:
        figures["Throttle Consistency"] = throttle_consistency

    racing_line = plot_racing_line(df, valid_laps)
    if racing_line:
        figures["Racing Line"] = racing_line

    figures["Braking Points"] = plot_braking_points(df, valid_laps, units)

    if len(valid_laps) >= 2:
        lap_times = {
            lap: (
                df[df["Lap"] == lap]["SessionTime"].max()
                - df[df["Lap"] == lap]["SessionTime"].min()
            )
            for lap in valid_laps
        }
        fastest_lap = min(lap_times, key=lambda lap: lap_times[lap])
        delta = plot_delta_time(df, valid_laps, fastest_lap, units)
        if delta:
            figures["Delta Time"] = delta

    track_map = plot_track_map(df, valid_laps, units)
    if track_map:
        figures["Track Map"] = track_map

    return figures
