"""Plotly chart helpers and titles (colors follow ``theme.is_light_theme()``)."""

from __future__ import annotations

import plotly.graph_objects as go

from theme import is_light_theme

PLOT_COLORWAY = ["#3d8ef8", "#22d3c8", "#f5a623", "#f43f5e", "#a78bfa", "#22c55e"]

# Solid paper/plot colors so PNG exports match on-screen dark vs light mode.
PLOT_LAYOUT_DARK = dict(
    paper_bgcolor="#0d0f14",
    plot_bgcolor="#13161d",
    font=dict(family="DM Sans, sans-serif", color="#e8ecf4", size=12),
    xaxis=dict(
        gridcolor="#252b3a",
        linecolor="#2e3649",
        tickcolor="#2e3649",
        zerolinecolor="#2e3649",
        tickfont=dict(color="#cbd5e1"),
        title=dict(font=dict(color="#e8ecf4")),
    ),
    yaxis=dict(
        gridcolor="#252b3a",
        linecolor="#2e3649",
        tickcolor="#2e3649",
        zerolinecolor="#2e3649",
        tickfont=dict(color="#cbd5e1"),
        title=dict(font=dict(color="#e8ecf4")),
    ),
    legend=dict(
        bgcolor="#13161d",
        bordercolor="#252b3a",
        borderwidth=1,
        font=dict(size=11, color="#e8ecf4"),
    ),
    colorway=PLOT_COLORWAY,
)

PLOT_LAYOUT_LIGHT = dict(
    paper_bgcolor="#ffffff",
    plot_bgcolor="#f8fafc",
    font=dict(family="DM Sans, sans-serif", color="#0f172a", size=12),
    xaxis=dict(
        gridcolor="#e2e8f0",
        linecolor="#94a3b8",
        tickcolor="#94a3b8",
        zerolinecolor="#cbd5e1",
        tickfont=dict(color="#334155"),
        title=dict(font=dict(color="#0f172a")),
    ),
    yaxis=dict(
        gridcolor="#e2e8f0",
        linecolor="#94a3b8",
        tickcolor="#94a3b8",
        zerolinecolor="#cbd5e1",
        tickfont=dict(color="#334155"),
        title=dict(font=dict(color="#0f172a")),
    ),
    legend=dict(
        bgcolor="#ffffff",
        bordercolor="#e2e8f0",
        borderwidth=1,
        font=dict(size=11, color="#0f172a"),
    ),
    colorway=PLOT_COLORWAY,
)


def chart_theme_is_light() -> bool:
    """Alias for app code: True when the sidebar App theme is Light."""
    return is_light_theme()


def plotly_axis_lines():
    """Axis line/tick styling merged into ``xaxis`` / ``yaxis`` updates."""
    if is_light_theme():
        return dict(
            gridcolor="#e2e8f0",
            linecolor="#94a3b8",
            tickcolor="#94a3b8",
            zerolinecolor="#cbd5e1",
            tickfont=dict(color="#334155"),
            title=dict(font=dict(color="#0f172a")),
        )
    return dict(
        gridcolor="#252b3a",
        linecolor="#2e3649",
        tickcolor="#2e3649",
        zerolinecolor="#2e3649",
        tickfont=dict(color="#cbd5e1"),
        title=dict(font=dict(color="#e8ecf4")),
    )


def apply_chart_theme(fig: go.Figure, **extra):
    """Merge base theme with ``extra``; partial ``legend`` / ``xaxis`` dicts are shallow-merged into base."""
    base = PLOT_LAYOUT_LIGHT if is_light_theme() else PLOT_LAYOUT_DARK
    merged = dict(base)
    for key, val in extra.items():
        if key == "legend" and isinstance(val, dict) and isinstance(merged.get("legend"), dict):
            merged["legend"] = {**merged["legend"], **val}
        elif key in ("xaxis", "yaxis") and isinstance(val, dict) and isinstance(merged.get(key), dict):
            merged[key] = {**merged[key], **val}
        else:
            merged[key] = val
    fig.update_layout(**merged)
    if is_light_theme():
        fig.update_layout(
            font=dict(family="DM Sans, sans-serif", color="#0f172a", size=12),
            legend_font_color="#0f172a",
        )
        fig.update_yaxes(title_font_color="#0f172a")
        fig.update_xaxes(title_font_color="#0f172a")
    return fig


def apply_dark_theme(fig: go.Figure, **extra):
    return apply_chart_theme(fig, **extra)


def overview_chart_title(metric: str, group_choice: str) -> str:
    if group_choice == "None (Overall)":
        return metric
    return f"{metric} × {group_choice}"


def lift_chart_title(metric: str, group_choice: str, view: str) -> str:
    if group_choice == "None (Overall)":
        return f"{metric} — {view}"
    return f"{metric} × {group_choice} — {view}"
