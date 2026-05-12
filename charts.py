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


def plotly_axis_extra(title: str | None = None, **kwargs):
    """Like :func:`plotly_axis_lines` but safe to combine with an axis ``title`` string.

    ``plotly_axis_lines`` embeds ``title=dict(font=…)``. Writing
    ``dict(title="Period", **plotly_axis_lines())`` raises *multiple values for keyword 'title'*.
    This helper pops that dict, sets ``text``, and merges any extra axis keys (e.g. ``tickformat``).
    """
    ax = plotly_axis_lines()
    title_cfg = dict(ax.pop("title", None) or {})
    merged = {**ax, **kwargs}
    if title is not None:
        title_cfg["text"] = title
        merged["title"] = title_cfg
    elif title_cfg:
        merged["title"] = title_cfg
    return merged


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


# ── Repeated Plotly layout / tokens (keeps app.py lean) ─────────────────────────
_CHART_TITLE = "#0f172a"
_CHART_TITLE_D = "#e8ecf4"


def chart_text_primary() -> str:
    """Primary text color for chart titles and outside labels."""
    return _CHART_TITLE if is_light_theme() else _CHART_TITLE_D


def chart_muted() -> str:
    """Muted line/series color (e.g. overall trend helper)."""
    return "#475569" if is_light_theme() else "#8b95aa"


def chart_hline_reference() -> str:
    """Horizontal reference line (e.g. zero baseline)."""
    return "#64748b" if is_light_theme() else "#4d5669"


def chart_hist_stroke_and_title() -> tuple[str, str]:
    """Histogram bar outline and title text color."""
    if is_light_theme():
        return "#cbd5e1", _CHART_TITLE
    return "#252b3a", _CHART_TITLE_D


def layout_chart_title(text: str, size: int = 16) -> dict:
    """Standard left-aligned chart title dict for :func:`apply_chart_theme`."""
    return dict(text=text, x=0.02, xanchor="left", font=dict(size=size, color=chart_text_primary()))


def colorway_cycled(n: int) -> list[str]:
    """Repeat ``PLOT_COLORWAY`` to cover ``n`` series or bars."""
    m = max(n, 1)
    k = len(PLOT_COLORWAY)
    return [PLOT_COLORWAY[i % k] for i in range(m)]


def volume_comparison_bars_layout(n_categories: int) -> dict:
    """Shared height, margin, and legend for Volume custom-period bar pairs."""
    h = max(620, 128 + 32 * max(n_categories, 1))
    return {
        "height": h,
        "margin": dict(l=52, r=20, t=60, b=240),
        "legend": dict(
            orientation="h",
            yanchor="top",
            y=-0.25,
            x=0.02,
            xanchor="left",
        ),
    }


def funnel_metric_bar_hover_and_ticks(m_fmt: str) -> tuple[str, str, str, str, str]:
    """Hover templates and y-axis tick settings for raw funnel-metric comparison bars."""
    if m_fmt == "pct":
        return (
            "%{x}<br>Period 1<br>%{y:.1%}<extra></extra>",
            "%{x}<br>Period 2<br>%{y:.1%}<extra></extra>",
            ".1%",
            "",
            "",
        )
    if m_fmt == "count":
        return (
            "%{x}<br>Period 1<br>%{y:,.0f}<extra></extra>",
            "%{x}<br>Period 2<br>%{y:,.0f}<extra></extra>",
            ",.0f",
            "",
            "",
        )
    if m_fmt == "dollar":
        return (
            "%{x}<br>Period 1<br>$%{y:,.2f}<extra></extra>",
            "%{x}<br>Period 2<br>$%{y:,.2f}<extra></extra>",
            ",.2f",
            "$",
            "",
        )
    return (
        "%{x}<br>Period 1<br>%{y:.2f}<extra></extra>",
        "%{x}<br>Period 2<br>%{y:.2f}<extra></extra>",
        ".2f",
        "",
        "",
    )
