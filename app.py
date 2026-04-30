import streamlit as st
import streamlit.components.v1 as st_components
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import json
import os
import hashlib
from datetime import timedelta, date

st.set_page_config(
    page_title="Arcadia Performance Dash",
    page_icon="⚡",
    layout="wide",
)

# ── Custom CSS (dark-first; follows Streamlit light/dark via --st-* fallbacks) ─
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Mono:wght@300;400;500&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;1,300&display=swap');

:root {
    --bg-base:       #0d0f14;
    --bg-card:       #13161d;
    --bg-card-alt:   #181c25;
    --bg-hover:      #1e2330;
    --border:        #252b3a;
    --border-bright: #2e3649;
    --accent:        #3d8ef8;
    --accent-dim:    #2563c4;
    --accent-glow:   rgba(61, 142, 248, 0.12);
    --teal:          #22d3c8;
    --amber:         #f5a623;
    --rose:          #f43f5e;
    --green:         #22c55e;
    --text-primary:  #e8ecf4;
    --text-secondary:#8b95aa;
    --text-muted:    #4d5669;
    --radius:        8px;
    --radius-lg:     12px;
}

html, body, [class*="css"], .stApp, .stMarkdown, p, span, div, label {
    font-family: 'DM Sans', sans-serif !important;
    color: var(--st-text-color, var(--text-primary)) !important;
}

.stApp {
    background-color: var(--st-background-color, var(--bg-base)) !important;
    color: var(--st-text-color, var(--text-primary)) !important;
    background-image:
        radial-gradient(ellipse 80% 40% at 50% -10%, rgba(61,142,248,0.06) 0%, transparent 58%),
        radial-gradient(ellipse 40% 30% at 90% 80%, rgba(34,211,200,0.03) 0%, transparent 50%);
}

.main .block-container {
    padding: 2rem 2.5rem 4rem !important;
    max-width: 1600px !important;
}

[data-testid="stSidebar"] {
    background-color: var(--st-secondary-background-color, var(--bg-card)) !important;
    border-right: 1px solid var(--st-border-color, var(--border)) !important;
}
[data-testid="stSidebar"] .stTitle > * {
    font-family: 'Syne', sans-serif !important;
    font-size: 1.1rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: var(--accent) !important;
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stMultiSelect label,
[data-testid="stSidebar"] .stDateInput label,
[data-testid="stSidebar"] .stToggle label {
    font-size: 0.7rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: var(--text-secondary) !important;
}

h1, h2, h3, h4 {
    font-family: 'Syne', sans-serif !important;
    color: var(--st-text-color, var(--text-primary)) !important;
}
h1 { font-size: 1.8rem !important; font-weight: 800 !important; letter-spacing: -0.01em !important; }
h2 { font-size: 1.25rem !important; font-weight: 700 !important; letter-spacing: 0.01em !important; }
h3 { font-size: 1rem !important; font-weight: 600 !important; }

[data-testid="stHeading"] h1 {
    color: var(--st-text-color, var(--text-primary)) !important;
    font-size: 2rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.02em !important;
    padding-bottom: 0.1em;
}

.stCaptionContainer, [data-testid="stCaptionContainer"], small, caption {
    color: var(--st-text-color-secondary, var(--text-secondary)) !important;
    font-size: 0.78rem !important;
    line-height: 1.5 !important;
}

[data-testid="stMetric"] {
    background: var(--st-secondary-background-color, var(--bg-card)) !important;
    border: 1px solid var(--st-border-color, var(--border)) !important;
    border-radius: var(--radius-lg) !important;
    padding: 1rem 1.25rem !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
    position: relative;
    overflow: hidden;
}
[data-testid="stMetric"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--accent), var(--teal));
    opacity: 0;
    transition: opacity 0.2s;
}
[data-testid="stMetric"]:hover { border-color: var(--border-bright) !important; box-shadow: 0 0 0 1px var(--border-bright), 0 4px 20px rgba(0,0,0,0.4) !important; }
[data-testid="stMetric"]:hover::before { opacity: 1; }
[data-testid="stMetricLabel"] { font-size: 0.68rem !important; font-weight: 500 !important; letter-spacing: 0.1em !important; text-transform: uppercase !important; color: var(--st-text-color-secondary, var(--text-secondary)) !important; font-family: 'DM Sans', sans-serif !important; }
[data-testid="stMetricValue"] { font-family: 'DM Mono', monospace !important; font-size: 1.5rem !important; font-weight: 500 !important; color: var(--st-text-color, var(--text-primary)) !important; line-height: 1.2 !important; }
[data-testid="stMetricDelta"] { font-family: 'DM Mono', monospace !important; font-size: 0.75rem !important; }
[data-testid="stMetricDelta"] svg { display: none !important; }

[data-testid="stTabs"] [role="tablist"] { border-bottom: 1px solid var(--st-border-color, var(--border)) !important; gap: 0 !important; background: transparent !important; }
[data-testid="stTabs"] [role="tab"] { font-family: 'Syne', sans-serif !important; font-size: 0.78rem !important; font-weight: 600 !important; letter-spacing: 0.07em !important; text-transform: uppercase !important; color: var(--st-text-color-secondary, var(--text-muted)) !important; padding: 0.6rem 1.25rem !important; border: none !important; border-bottom: 2px solid transparent !important; background: transparent !important; transition: color 0.15s, border-color 0.15s !important; }
[data-testid="stTabs"] [role="tab"]:hover { color: var(--st-text-color, var(--text-secondary)) !important; border-bottom-color: var(--st-border-color, var(--border-bright)) !important; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] { color: var(--st-primary-color, var(--accent)) !important; border-bottom-color: var(--st-primary-color, var(--accent)) !important; background: transparent !important; }

hr { border: none !important; border-top: 1px solid var(--st-border-color, var(--border)) !important; margin: 2rem 0 !important; }

.stSelectbox > div > div,
.stMultiSelect > div > div,
.stTextInput > div > div > input,
.stDateInput > div > div > input {
    background-color: var(--st-secondary-background-color, var(--bg-card-alt)) !important;
    border: 1px solid var(--st-border-color, var(--border-bright)) !important;
    border-radius: var(--radius) !important;
    color: var(--st-text-color, var(--text-primary)) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
    transition: border-color 0.15s !important;
}
.stSelectbox > div > div:focus-within,
.stMultiSelect > div > div:focus-within { border-color: var(--accent) !important; box-shadow: 0 0 0 2px var(--accent-glow) !important; outline: none !important; }

[data-baseweb="menu"] { background-color: var(--st-secondary-background-color, var(--bg-card-alt)) !important; border: 1px solid var(--st-border-color, var(--border-bright)) !important; border-radius: var(--radius) !important; }
[data-baseweb="menu"] li { font-family: 'DM Sans', sans-serif !important; font-size: 0.85rem !important; color: var(--st-text-color, var(--text-primary)) !important; }
[data-baseweb="menu"] li:hover { background-color: var(--st-secondary-background-color, var(--bg-hover)) !important; }
[data-baseweb="tag"] { background-color: var(--accent-dim) !important; border: none !important; border-radius: 4px !important; font-size: 0.75rem !important; }

.stRadio > div { gap: 0.5rem !important; background: transparent !important; border: none !important; padding: 0 !important; display: inline-flex !important; }
.stRadio label { font-size: 0.75rem !important; font-weight: 500 !important; letter-spacing: 0.05em !important; text-transform: uppercase !important; padding: 0.3rem 0.85rem !important; border-radius: 6px !important; cursor: pointer !important; color: var(--st-text-color-secondary, var(--text-secondary)) !important; background: transparent !important; transition: color 0.15s !important; }

[data-testid="stDataFrame"], .stDataFrame { border: 1px solid var(--st-border-color, var(--border)) !important; border-radius: var(--radius-lg) !important; overflow: hidden !important; }
[data-testid="stDataFrame"] thead th { background: var(--st-secondary-background-color, var(--bg-card-alt)) !important; font-family: 'DM Sans', sans-serif !important; font-size: 0.68rem !important; font-weight: 600 !important; letter-spacing: 0.1em !important; text-transform: uppercase !important; color: var(--st-text-color-secondary, var(--text-secondary)) !important; border-bottom: 1px solid var(--st-border-color, var(--border-bright)) !important; padding: 0.6rem 0.8rem !important; }
[data-testid="stDataFrame"] thead th:not(:first-child),
[data-testid="stDataFrame"] tbody td:not(:first-child) { text-align: right !important; }
[data-testid="stDataFrame"] thead th:first-child,
[data-testid="stDataFrame"] tbody td:first-child { text-align: left !important; }
[data-testid="stDataFrame"] tbody td { font-family: 'DM Mono', monospace !important; font-size: 0.82rem !important; color: var(--st-text-color, var(--text-primary)) !important; border-bottom: 1px solid var(--st-border-color, var(--border)) !important; padding: 0.5rem 0.8rem !important; background: var(--st-secondary-background-color, var(--bg-card)) !important; }
[data-testid="stDataFrame"] tbody tr:hover td { background: var(--st-secondary-background-color, var(--bg-hover)) !important; }

.stButton > button { background: var(--st-primary-color, var(--accent)) !important; color: white !important; border: none !important; border-radius: var(--radius) !important; font-family: 'DM Sans', sans-serif !important; font-size: 0.8rem !important; font-weight: 600 !important; letter-spacing: 0.05em !important; padding: 0.5rem 1.25rem !important; transition: all 0.15s !important; }
.stButton > button:hover { background: var(--accent-dim) !important; box-shadow: 0 4px 12px rgba(61,142,248,0.3) !important; transform: translateY(-1px) !important; }

[data-testid="stHeading"] h2, .stMarkdown h2 { color: var(--st-text-color, var(--text-primary)) !important; font-size: 1.1rem !important; font-weight: 700 !important; letter-spacing: 0.02em !important; padding-top: 0.25rem !important; padding-bottom: 0.5rem !important; border-bottom: 1px solid var(--st-border-color, var(--border)) !important; margin-bottom: 1rem !important; }

[data-testid="stInfo"] { background: rgba(61,142,248,0.08) !important; border: 1px solid rgba(61,142,248,0.25) !important; border-radius: var(--radius) !important; color: var(--accent) !important; font-size: 0.85rem !important; }
[data-testid="stWarning"] { background: rgba(245,166,35,0.08) !important; border: 1px solid rgba(245,166,35,0.25) !important; border-radius: var(--radius) !important; color: var(--amber) !important; }

[data-testid="stCaptionContainer"] p { color: var(--st-text-color-secondary, var(--text-muted)) !important; font-size: 0.78rem !important; font-family: 'DM Mono', monospace !important; letter-spacing: 0.05em !important; }
.stMarkdown strong { color: var(--st-text-color, var(--text-primary)) !important; font-weight: 600 !important; }

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--st-background-color, var(--bg-base)); }
::-webkit-scrollbar-thumb { background: var(--st-border-color, var(--border-bright)); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--st-text-color-secondary, var(--text-muted)); }
</style>
""", unsafe_allow_html=True)

# ── Plotly themes (match app dark / Streamlit light) ───────────────────────────
PLOT_COLORWAY = ["#3d8ef8", "#22d3c8", "#f5a623", "#f43f5e", "#a78bfa", "#22c55e"]

PLOT_LAYOUT_DARK = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, sans-serif", color="#8b95aa", size=12),
    xaxis=dict(gridcolor="#1e2330", linecolor="#252b3a", tickcolor="#252b3a", zerolinecolor="#252b3a"),
    yaxis=dict(gridcolor="#1e2330", linecolor="#252b3a", tickcolor="#252b3a", zerolinecolor="#252b3a"),
    legend=dict(bgcolor="rgba(19,22,29,0.8)", bordercolor="#252b3a", borderwidth=1, font=dict(size=11, color="#8b95aa")),
    colorway=PLOT_COLORWAY,
)

PLOT_LAYOUT_LIGHT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, sans-serif", color="#64748b", size=12),
    xaxis=dict(gridcolor="#e2e8f0", linecolor="#cbd5e1", tickcolor="#cbd5e1", zerolinecolor="#cbd5e1"),
    yaxis=dict(gridcolor="#e2e8f0", linecolor="#cbd5e1", tickcolor="#cbd5e1", zerolinecolor="#cbd5e1"),
    legend=dict(bgcolor="rgba(255,255,255,0.94)", bordercolor="#cbd5e1", borderwidth=1, font=dict(size=11, color="#64748b")),
    colorway=PLOT_COLORWAY,
)


def chart_theme_is_light() -> bool:
    try:
        return str(st.context.theme.get("type", "") or "").lower() == "light"
    except Exception:
        return False


def plotly_axis_lines():
    if chart_theme_is_light():
        return dict(gridcolor="#e2e8f0", linecolor="#cbd5e1", tickcolor="#cbd5e1", zerolinecolor="#cbd5e1")
    return dict(gridcolor="#1e2330", linecolor="#252b3a", tickcolor="#252b3a", zerolinecolor="#252b3a")


def apply_chart_theme(fig, **extra):
    base = PLOT_LAYOUT_LIGHT if chart_theme_is_light() else PLOT_LAYOUT_DARK
    fig.update_layout(**{**base, **extra})
    return fig


def apply_dark_theme(fig, **extra):
    return apply_chart_theme(fig, **extra)


def dataframe_display_height(n_rows: int, min_rows: int = 4, row_px: int = 36, header_px: int = 52, cap: int = 2200) -> int:
    try:
        n = max(min_rows, int(n_rows))
    except (TypeError, ValueError):
        n = min_rows
    return int(min(cap, header_px + row_px * n))


def table_export_row(display_df: pd.DataFrame, download_filename: str, copy_label: str = "Copy"):
    """Renders download + copy actions (place below ``st.dataframe``). Copy button sized to match Streamlit download."""
    tsv = display_df.to_csv(index=False, sep="\t")
    csv_bytes = display_df.to_csv(index=False).encode("utf-8")
    uid = hashlib.md5(download_filename.encode(), usedforsecurity=False).hexdigest()[:12]
    b1, b2 = st.columns([1, 1])
    with b1:
        st.download_button(
            "Download CSV",
            data=csv_bytes,
            file_name=download_filename,
            mime="text/csv",
            key=f"dl_{uid}",
        )
    with b2:
        tsv_literal = json.dumps(tsv)
        lbl_literal = json.dumps(copy_label)
        st_components.html(
            f"""<div style="font-family:DM Sans,sans-serif;padding:0;margin:0;">
<button type="button" id="cpbtn_{uid}"
  style="background:#3d8ef8;color:#fff;border:none;border-radius:0.5rem;box-sizing:border-box;
  width:100%;min-height:2.625rem;height:2.625rem;padding:0 1.25rem;font-size:0.875rem;font-weight:600;
  line-height:1.2;cursor:pointer;display:flex;align-items:center;justify-content:center;">{copy_label}</button>
</div>
<script>
(function() {{
  var text = {tsv_literal};
  var orig = {lbl_literal};
  var b = document.getElementById("cpbtn_{uid}");
  if (!b) return;
  b.addEventListener("click", function() {{
    function fallbackCopy() {{
      try {{
        var ta = document.createElement("textarea");
        ta.value = text;
        ta.setAttribute("readonly", "");
        ta.style.position = "fixed";
        ta.style.left = "-9999px";
        document.body.appendChild(ta);
        ta.focus();
        ta.select();
        ta.setSelectionRange(0, 999999);
        document.execCommand("copy");
        document.body.removeChild(ta);
      }} catch (e) {{}}
    }}
    if (navigator.clipboard && window.isSecureContext) {{
      navigator.clipboard.writeText(text).catch(fallbackCopy);
    }} else {{
      fallbackCopy();
    }}
    b.textContent = "Copied";
    setTimeout(function() {{ b.textContent = orig; }}, 1600);
  }});
}})();
</script>""",
            height=52,
        )


def overview_chart_title(metric: str, group_choice: str) -> str:
    if group_choice == "None (Overall)":
        return metric
    return f"{metric} × {group_choice}"


def lift_chart_title(metric: str, group_choice: str, view: str) -> str:
    if group_choice == "None (Overall)":
        return f"{metric} — {view}"
    return f"{metric} × {group_choice} — {view}"

# ── Load data ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl="24h")
def load_data():
    data_dir = "data/"
    files = [f for f in os.listdir(data_dir) if f.startswith("agent_calls_") and f.endswith(".csv")]
    
    if not files:
        raise FileNotFoundError("No monthly CSV files found in data/")
    
    dfs = []
    for f in sorted(files):
        dfs.append(pd.read_csv(os.path.join(data_dir, f)))
    
    df = pd.concat(dfs, ignore_index=True)
    df["call_date_est"] = pd.to_datetime(df["call_date_est"])
    return df

try:
    df_raw = load_data()
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()

# ── Sidebar Filters ────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("Filters")

    min_d = df_raw["call_date_est"].min().date()
    max_d = df_raw["call_date_est"].max().date()
    default_start = max(min_d, max_d - timedelta(days=6))

    date_range = st.date_input(
        "Date Range",
        value=(default_start, max_d),
        min_value=min_d,
        max_value=max_d,
        key="filter_date",
    )

    center_opts   = sorted(df_raw["center_location"].dropna().unique().tolist()) if "center_location" in df_raw.columns else []
    mkt_opts      = sorted(df_raw["marketing_bucket"].dropna().unique().tolist()) if "marketing_bucket" in df_raw.columns else []
    mov_opts      = sorted(df_raw["moverSwitcher"].dropna().unique().tolist()) if "moverSwitcher" in df_raw.columns else []
    tenure_opts   = sorted(df_raw["tenure_bucket"].dropna().unique().tolist()) if "tenure_bucket" in df_raw.columns else []
    calltype_opts = sorted(df_raw["call_type"].dropna().unique().tolist()) if "call_type" in df_raw.columns else []
    sel_center   = st.multiselect("Center",           options=center_opts,   default=[], key="f_center")
    sel_mkt      = st.multiselect("Marketing Bucket", options=mkt_opts,      default=[], key="f_mkt")
    sel_mov      = st.multiselect("Mover / Switcher", options=mov_opts,      default=[], key="f_mov")
    sel_tenure   = st.multiselect("Tenure Bucket",    options=tenure_opts,   default=[], key="f_tenure")
    sel_calltype = st.multiselect("Site/SERP",        options=calltype_opts, default=[], key="f_calltype")

# ── Apply filters ──────────────────────────────────────────────────────────────
def apply_filters(base, use_date_range=True):
    d = base.copy()
    # Always filter to Arcadia only outside of the Arcadia vs Atom tab
    if "membership" in d.columns:
        d = d[d["membership"] == "Arcadia"]
    if use_date_range and len(date_range) == 2:
        d = d[(d["call_date_est"].dt.date >= date_range[0]) & (d["call_date_est"].dt.date <= date_range[1])]
    if sel_center   and "center_location"  in d.columns: d = d[d["center_location"].isin(sel_center)]
    if sel_mkt      and "marketing_bucket" in d.columns: d = d[d["marketing_bucket"].isin(sel_mkt)]
    if sel_mov      and "moverSwitcher"    in d.columns: d = d[d["moverSwitcher"].isin(sel_mov)]
    if sel_tenure   and "tenure_bucket"    in d.columns: d = d[d["tenure_bucket"].isin(sel_tenure)]
    if sel_calltype and "call_type"        in d.columns: d = d[d["call_type"].isin(sel_calltype)]
    return d

df = apply_filters(df_raw)

# ── Shared helpers ─────────────────────────────────────────────────────────────
PERIOD_OPTIONS = ["Daily", "Weekly", "Monthly"]
PERIOD_CODE    = {"Daily": "D", "Weekly": "W", "Monthly": "M"}
PERIOD_FMT     = {"Daily": "%b %d", "Weekly": "%b %d", "Monthly": "%b %Y"}

def period_labels(date_series, period):
    code = PERIOD_CODE[period]
    return date_series.dt.to_period(code).apply(lambda p: p.start_time)

def period_display(label_series, period):
    return pd.to_datetime(label_series).dt.strftime(PERIOD_FMT[period])

def safe_rate(num, denom):
    return num / denom if denom > 0 else float("nan")


def top_funnel_mask(d: pd.DataFrame) -> pd.Series:
    """Inbound calls only for top-of-funnel denominators."""
    if "call_direction" in d.columns:
        return d["call_direction"].astype(str).str.upper().eq("INBOUND")
    if "ibcalls" in d.columns:
        return d["ibcalls"].eq(1)
    return pd.Series(True, index=d.index)


def order_revenue_mask(d: pd.DataFrame) -> pd.Series:
    """Orders/revenue include inbound + manual outbound calls."""
    if "call_direction" in d.columns:
        return d["call_direction"].astype(str).str.upper().isin(["INBOUND", "MANUAL_OUTBOUND"])
    return pd.Series(True, index=d.index)


def top_funnel_call_count(d: pd.DataFrame) -> int:
    return int(top_funnel_mask(d).sum())


# Funnel / overview metric names where a *decrease* (P2 vs P1, or vs prior week) is better
FUNNEL_METRIC_LOWER_IS_BETTER = frozenset({"Talk Time", "Sold Talk Time", "Unsold Talk Time"})
# Lift tab KPI keys (same semantics for Arcadia vs Atom deltas)
LIFT_KPI_LOWER_IS_BETTER = frozenset({"tt"})


def pct_change_cell_style(metric_id: str, pct_num: float, neutral_abs: float = 1.5) -> str:
    """CSS for a numeric % change. metric_id = funnel 'Metric' name or lift KPI key (e.g. 'tt')."""
    if pct_num is None or (isinstance(pct_num, float) and (pd.isna(pct_num) or np.isinf(pct_num))):
        return ""
    if abs(float(pct_num)) < neutral_abs:
        return "background-color: #2a2a1a; color: #c8a000"
    lower_better = metric_id in FUNNEL_METRIC_LOWER_IS_BETTER or metric_id in LIFT_KPI_LOWER_IS_BETTER
    good = (float(pct_num) < 0) if lower_better else (float(pct_num) > 0)
    if good:
        return "background-color: #0f2a1a; color: #22c55e"
    return "background-color: #2a1018; color: #f43f5e"


def parse_display_pct(val):
    """Parse '+12.3%' / '-4.0%' / '—' from styled tables into a float or None."""
    if val is None or val == "—" or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip().replace("%", "").replace("+", "")
    try:
        return float(s)
    except ValueError:
        return None

def delta_str_pct(cur, prev):
    if pd.isna(cur) or pd.isna(prev) or prev == 0:
        return None
    return f"{(cur - prev) * 100:+.1f}pp vs prior week"

def delta_str_dollar(cur, prev):
    if pd.isna(cur) or pd.isna(prev):
        return None
    return f"${cur - prev:+,.0f} vs prior week"

def week_kpi(source, metric_fn):
    """Returns (this_week_val, prev_week_val) using last 2 ISO weeks."""
    if "call_date_est" not in source.columns:
        return None, None
    tmp = source.dropna(subset=["call_date_est"]).copy()
    tmp["week"] = tmp["call_date_est"].dt.to_period("W")
    weeks = sorted(tmp["week"].unique())
    if not weeks:
        return None, None
    this_w = weeks[-1]
    prev_w = weeks[-2] if len(weeks) >= 2 else None
    this_v = metric_fn(tmp[tmp["week"] == this_w])
    prev_v = metric_fn(tmp[tmp["week"] == prev_w]) if prev_w else None
    return this_v, prev_v

# ── Core metric computations ───────────────────────────────────────────────────
def compute_kpis(d):
    inbound = d[top_funnel_mask(d)]
    orders_rev_rows = d[order_revenue_mask(d)]
    n_calls       = top_funnel_call_count(d)
    n_contact     = int(inbound["ib_contact_calls"].sum()) if "ib_contact_calls" in inbound.columns else 0
    n_credit      = int(inbound["credit_calls_flag"].sum()) if "credit_calls_flag" in inbound.columns else 0
    n_pass_credit = int(inbound["passed_credit_call_flag"].sum()) if "passed_credit_call_flag" in inbound.columns else 0
    n_fail_credit = int(inbound["failed_credit_call_flag"].sum()) if "failed_credit_call_flag" in inbound.columns else 0
    n_pass_sale   = int(inbound["passed_credit_sale_flag"].sum()) if "passed_credit_sale_flag" in inbound.columns else 0
    n_fail_sale   = int(inbound["failed_credit_sale_flag"].sum()) if "failed_credit_sale_flag" in inbound.columns else 0
    n_orders      = int(orders_rev_rows["orders"].sum()) if "orders" in orders_rev_rows.columns else 0
    n_tpsales     = int(orders_rev_rows["tpsales_flag"].sum()) if "tpsales_flag" in orders_rev_rows.columns else 0
    total_gcv     = orders_rev_rows["gcv_fo"].sum() if "gcv_fo" in orders_rev_rows.columns else 0.0
    total_rev     = orders_rev_rows["total_revenue"].sum() if "total_revenue" in orders_rev_rows.columns else total_gcv
    tt_avg        = inbound["talk_time_minutes"].mean() if "talk_time_minutes" in inbound.columns else float("nan")
    tt_sold       = inbound[inbound["orders"] > 0]["talk_time_minutes"].mean() if ("talk_time_minutes" in inbound.columns and "orders" in inbound.columns) else float("nan")
    tt_unsold     = inbound[inbound["orders"] == 0]["talk_time_minutes"].mean() if ("talk_time_minutes" in inbound.columns and "orders" in inbound.columns) else float("nan")

    return {
        "n_calls":        n_calls,
        "contact_rate":   safe_rate(n_contact, n_calls),
        "credit_rate":    safe_rate(n_credit, n_calls),
        "pass_credit_rate":     safe_rate(n_pass_credit, n_credit),
        "fail_credit_rate":     safe_rate(n_fail_credit, n_credit),
        "pass_credit_conv":     safe_rate(n_pass_sale, n_pass_credit),
        "fail_credit_conv":     safe_rate(n_fail_sale, n_fail_credit),
        "net_conversion": safe_rate(n_orders, n_calls),
        "top_product_mix":safe_rate(n_tpsales, n_orders),
        "total_revenue":  total_rev,
        "rev_per_call":   safe_rate(total_rev, n_calls),
        "rev_per_order":  safe_rate(total_rev, n_orders),
        "talk_time":      tt_avg,
        "talk_time_sold": tt_sold,
        "talk_time_unsold": tt_unsold,
    }

# ── Header ─────────────────────────────────────────────────────────────────────
date_str = ""
if df["call_date_est"].notna().any():
    mn = df["call_date_est"].min().strftime("%b %d")
    mx = df["call_date_est"].max().strftime("%b %d, %Y")
    date_str = f"{mn} – {mx}"

st.title("⚡ Arcadia Performance Dash")
st.caption(f"{date_str}  ·  {top_funnel_call_count(df):,} inbound calls in view")

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_overview, tab_agent, tab_lift = st.tabs([
    "Overview",
    "Agent Level",
    "Arcadia vs Atom",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB — OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
with tab_overview:

    # ── Top KPI row — always last week vs prior week, ignores date filter ──────
    st.subheader("Last Week vs Prior Week")
    st.caption("Automatically compares the two most recent ISO weeks · ignores date filter")

    def _wk_raw(fn):
        """Uses df_raw with sidebar filters except date (week KPIs are always last 2 ISO weeks)."""
        return week_kpi(apply_filters(df_raw.copy(), use_date_range=False), fn)

    def wk_pct_delta(cur, prev):
        if cur is None or prev is None or pd.isna(cur) or pd.isna(prev) or prev == 0:
            return None
        return f"{(cur / prev - 1) * 100:+.1f}% vs prior wk"

    # Compute last-week values for display (not filtered by date)
    def last_week_val(fn):
        this_v, _ = _wk_raw(fn)
        return this_v

    lw_rev_call  = last_week_val(lambda d: safe_rate(d.loc[order_revenue_mask(d), "total_revenue"].sum() if "total_revenue" in d.columns else 0, top_funnel_call_count(d)))
    lw_net_conv  = last_week_val(lambda d: safe_rate(d.loc[order_revenue_mask(d), "orders"].sum() if "orders" in d.columns else 0, top_funnel_call_count(d)))
    lw_rev_order = last_week_val(lambda d: safe_rate(d.loc[order_revenue_mask(d), "total_revenue"].sum() if "total_revenue" in d.columns else 0, d.loc[order_revenue_mask(d), "orders"].sum() if "orders" in d.columns else 0))
    lw_cic       = last_week_val(lambda d: safe_rate(d.loc[top_funnel_mask(d), "credit_calls_flag"].sum() if "credit_calls_flag" in d.columns else 0, top_funnel_call_count(d)))
    lw_tt        = last_week_val(lambda d: d.loc[top_funnel_mask(d), "talk_time_minutes"].mean() if "talk_time_minutes" in d.columns else float("nan"))

    cv1, pv1 = _wk_raw(lambda d: safe_rate(d.loc[order_revenue_mask(d), "total_revenue"].sum() if "total_revenue" in d.columns else 0, top_funnel_call_count(d)))
    cv2, pv2 = _wk_raw(lambda d: safe_rate(d.loc[order_revenue_mask(d), "orders"].sum() if "orders" in d.columns else 0, top_funnel_call_count(d)))
    cv3, pv3 = _wk_raw(lambda d: safe_rate(d.loc[order_revenue_mask(d), "total_revenue"].sum() if "total_revenue" in d.columns else 0, d.loc[order_revenue_mask(d), "orders"].sum() if "orders" in d.columns else 0))
    cv4, pv4 = _wk_raw(lambda d: safe_rate(d.loc[top_funnel_mask(d), "credit_calls_flag"].sum() if "credit_calls_flag" in d.columns else 0, top_funnel_call_count(d)))
    cv5, pv5 = _wk_raw(lambda d: d.loc[top_funnel_mask(d), "talk_time_minutes"].mean() if "talk_time_minutes" in d.columns else float("nan"))

    km1, km2, km3, km4, km5 = st.columns(5)
    km1.metric("Rev / Call",         f"${lw_rev_call:,.2f}"  if lw_rev_call  and not pd.isna(lw_rev_call)  else "—", delta=wk_pct_delta(cv1, pv1))
    km2.metric("Net Conversion",     f"{lw_net_conv:.1%}"    if lw_net_conv  and not pd.isna(lw_net_conv)  else "—", delta=wk_pct_delta(cv2, pv2))
    km3.metric("Rev / Order",        f"${lw_rev_order:,.2f}" if lw_rev_order and not pd.isna(lw_rev_order) else "—", delta=wk_pct_delta(cv3, pv3))
    km4.metric("Calls Into Credit",  f"{lw_cic:.1%}"         if lw_cic       and not pd.isna(lw_cic)       else "—", delta=wk_pct_delta(cv4, pv4))
    km5.metric(
        "Talk Time",
        f"{lw_tt:.1f} min" if lw_tt and not pd.isna(lw_tt) else "—",
        delta=wk_pct_delta(cv5, pv5),
        delta_color="inverse",
    )

    st.divider()

    # ── Funnel table ───────────────────────────────────────────────────────────
    st.subheader("Funnel Over Time")

    ov_gran = st.radio(
        "Granularity", PERIOD_OPTIONS, index=0, horizontal=True, key="overview_gran"
    )

    FUNNEL_METRICS = [
        ("Calls",          "count"),
        ("CiContact",      "pct"),
        ("CiCredit",       "pct"),
        ("PCR",            "pct"),
        ("PCC",            "pct"),
        ("FCC",            "pct"),
        ("NC",             "pct"),
        ("TPM",            "pct"),
        ("Revenue",        "dollar"),
        ("RPNC",           "dollar"),
        ("RPO",            "dollar"),
        ("Talk Time",      "decimal"),
        ("Sold Talk Time", "decimal"),
        ("Unsold Talk Time","decimal"),
    ]

    def compute_funnel_row(grp, metric):
        inbound = grp[top_funnel_mask(grp)]
        orders_rev_rows = grp[order_revenue_mask(grp)]
        n          = top_funnel_call_count(grp)
        n_contact  = inbound["ib_contact_calls"].sum()  if "ib_contact_calls"       in inbound.columns else 0
        n_credit   = inbound["credit_calls_flag"].sum() if "credit_calls_flag"       in inbound.columns else 0
        n_pass_cr  = inbound["passed_credit_call_flag"].sum() if "passed_credit_call_flag" in inbound.columns else 0
        n_fail_cr  = inbound["failed_credit_call_flag"].sum() if "failed_credit_call_flag" in inbound.columns else 0
        n_pass_sale= inbound["passed_credit_sale_flag"].sum() if "passed_credit_sale_flag" in inbound.columns else 0
        n_fail_sale= inbound["failed_credit_sale_flag"].sum() if "failed_credit_sale_flag" in inbound.columns else 0
        n_orders   = orders_rev_rows["orders"].sum()            if "orders"                  in orders_rev_rows.columns else 0
        n_tpsales  = orders_rev_rows["tpsales_flag"].sum()      if "tpsales_flag"            in orders_rev_rows.columns else 0
        rev        = orders_rev_rows["total_revenue"].sum()     if "total_revenue"           in orders_rev_rows.columns else orders_rev_rows["gcv_fo"].sum() if "gcv_fo" in orders_rev_rows.columns else 0
        tt_all     = inbound["talk_time_minutes"].mean()    if "talk_time_minutes"   in inbound.columns else float("nan")
        tt_sold    = inbound[inbound["orders"] > 0]["talk_time_minutes"].mean() if ("talk_time_minutes" in inbound.columns and "orders" in inbound.columns) else float("nan")
        tt_unsold  = inbound[inbound["orders"] == 0]["talk_time_minutes"].mean() if ("talk_time_minutes" in inbound.columns and "orders" in inbound.columns) else float("nan")

        val_map = {
            "Calls":           n,
            "CiContact":       safe_rate(n_contact,   n),
            "CiCredit":        safe_rate(n_credit,    n),
            "PCR":             safe_rate(n_pass_cr,   n_credit),
            "PCC":             safe_rate(n_pass_sale, n_pass_cr),
            "FCC":             safe_rate(n_fail_sale, n_fail_cr),
            "NC":              safe_rate(n_orders,    n),
            "TPM":             safe_rate(n_tpsales,   n_orders),
            "Revenue":         rev,
            "RPNC":            safe_rate(rev,         n),
            "RPO":             safe_rate(rev,         n_orders),
            "Talk Time":       tt_all,
            "Sold Talk Time":  tt_sold,
            "Unsold Talk Time":tt_unsold,
        }
        return val_map.get(metric, float("nan"))

    def fmt_funnel(val, fmt):
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return "—"
        if fmt == "count":   return f"{int(val):,}"
        if fmt == "pct":     return f"{val:.1%}"
        if fmt == "dollar":  return f"${val:,.2f}"
        return f"{val:.2f}"

    if "call_date_est" in df.columns and len(df) > 0:
        ft_df = df.dropna(subset=["call_date_est"]).copy()
        ft_df["period"] = period_labels(ft_df["call_date_est"], ov_gran)
        periods_sorted = sorted(ft_df["period"].unique())

        # Build period display labels
        period_disp = {p: pd.to_datetime(p).strftime(PERIOD_FMT[ov_gran]) for p in periods_sorted}

        funnel_rows = []
        for metric, fmt in FUNNEL_METRICS:
            row = {"Metric": metric}
            for p in periods_sorted:
                grp = ft_df[ft_df["period"] == p]
                row[period_disp[p]] = fmt_funnel(compute_funnel_row(grp, metric), fmt)
            funnel_rows.append(row)

        funnel_table = pd.DataFrame(funnel_rows)
        st.dataframe(
            funnel_table,
            use_container_width=True,
            hide_index=True,
            height=dataframe_display_height(len(funnel_table)),
        )
        table_export_row(funnel_table, "funnel_over_time.csv")
    else:
        st.info("No data available.")

    # ── Custom period comparison (ignores sidebar date filter) ─────────────────
    st.subheader("Custom Period Comparison")
    st.caption(
        "Ignores the sidebar **Date Range**. Uses Center, Marketing, Mover/Switcher, Tenure, and Call Type filters. "
        "Each period is one aggregate over its date window (same metrics as the funnel table)."
    )
    df_cmp = apply_filters(df_raw.copy(), use_date_range=False)
    if "call_date_est" in df_cmp.columns and len(df_cmp) > 0:
        _cmp_min = df_cmp["call_date_est"].min().date()
        _cmp_max = df_cmp["call_date_est"].max().date()
        _w = timedelta(days=6)
        _d2_end = _cmp_max
        _d2_start = max(_cmp_min, _d2_end - _w)
        _d1_end = _d2_start - timedelta(days=1)
        _d1_start = max(_cmp_min, _d1_end - _w)
        if _d1_start > _d1_end:
            _d1_start = _cmp_min
            _d1_end = min(_cmp_max, _d1_start + _w)

        pc_a, pc_b = st.columns(2)
        with pc_a:
            cmp_range_1 = st.date_input(
                "Period 1",
                value=(_d1_start, _d1_end),
                min_value=_cmp_min,
                max_value=_cmp_max,
                key="ov_cmp_period1",
            )
        with pc_b:
            cmp_range_2 = st.date_input(
                "Period 2",
                value=(_d2_start, _d2_end),
                min_value=_cmp_min,
                max_value=_cmp_max,
                key="ov_cmp_period2",
            )

        def _slice_period(d_all, dr):
            if len(dr) != 2:
                return d_all.iloc[0:0]
            a, b = dr[0], dr[1]
            if a > b:
                a, b = b, a
            m = (d_all["call_date_est"].dt.date >= a) & (d_all["call_date_est"].dt.date <= b)
            return d_all.loc[m]

        def _pct_change_numeric(v1, v2):
            if v1 is None or v2 is None:
                return float("nan")
            if (isinstance(v1, float) and pd.isna(v1)) or (isinstance(v2, float) and pd.isna(v2)):
                return float("nan")
            try:
                v1 = float(v1)
                v2 = float(v2)
            except (TypeError, ValueError):
                return float("nan")
            if v1 == 0:
                return float("nan")
            return (v2 / v1 - 1.0) * 100.0

        def _fmt_pct_change(p):
            if p is None or (isinstance(p, float) and pd.isna(p)):
                return "—"
            return f"{p:+.1f}%"

        if len(cmp_range_1) == 2 and len(cmp_range_2) == 2:
            g1 = _slice_period(df_cmp, cmp_range_1)
            g2 = _slice_period(df_cmp, cmp_range_2)
            c1a, c1b = sorted([cmp_range_1[0], cmp_range_1[1]])
            c2a, c2b = sorted([cmp_range_2[0], cmp_range_2[1]])
            col1 = f"P1 ({c1a.strftime('%b %d, %Y')} – {c1b.strftime('%b %d, %Y')})"
            col2 = f"P2 ({c2a.strftime('%b %d, %Y')} – {c2b.strftime('%b %d, %Y')})"

            cmp_rows = []
            for metric, fmt in FUNNEL_METRICS:
                raw1 = compute_funnel_row(g1, metric)
                raw2 = compute_funnel_row(g2, metric)
                disp1 = fmt_funnel(raw1, fmt)
                disp2 = fmt_funnel(raw2, fmt)
                pch = _pct_change_numeric(raw1, raw2)
                cmp_rows.append(
                    {
                        "Metric": metric,
                        col1: disp1,
                        col2: disp2,
                        "% Change (P2 vs P1)": _fmt_pct_change(pch),
                    }
                )
            cmp_table = pd.DataFrame(cmp_rows)
            _pch_col = "% Change (P2 vs P1)"

            def _style_cmp_row(row):
                m = row["Metric"]
                p = parse_display_pct(row[_pch_col])
                out = pd.Series("", index=row.index)
                if p is not None:
                    out[_pch_col] = pct_change_cell_style(m, p)
                return out

            cmp_styler = cmp_table.style.apply(_style_cmp_row, axis=1)
            st.dataframe(
                cmp_styler,
                use_container_width=True,
                hide_index=True,
                height=dataframe_display_height(len(cmp_table)),
            )
            table_export_row(cmp_table, "period_comparison.csv")
        else:
            st.info("Select a full start and end date for each period.")
    else:
        st.info("No data available for period comparison with current filters.")

    st.divider()

    # ── Trend chart — shares granularity with funnel table ────────────────────
    st.subheader("Trend Over Time")

    tr_c1, tr_c2 = st.columns(2)
    with tr_c1:
        ov_metric_choice = st.selectbox(
            "Metric",
            ["Net Conversion", "Total Revenue", "Rev / Call", "Rev / Order",
             "Top Product Mix", "Contact Rate", "Credit Rate",
             "Passed Credit Rate", "Passed Credit Conv.", "Failed Credit Conv.",
             "Talk Time", "Calls"],
            key="ov_trend_metric",
        )
    with tr_c2:
        GROUP_COL_MAP = {
            "Center":           "center_location",
            "Marketing Bucket": "marketing_bucket",
            "Mover / Switcher": "moverSwitcher",
            "Tenure Bucket":    "tenure_bucket",
            "Call Type":        "call_type",
            "None (Overall)":   None,
        }
        ov_group_choice = st.selectbox(
            "Group By",
            options=list(GROUP_COL_MAP.keys()),
            index=0,
            key="ov_trend_group",
        )
        ov_group_col = GROUP_COL_MAP[ov_group_choice]

    METRIC_MAP_OV = {
        "Net Conversion":      ("orders",                    "n_calls",             "pct"),
        "Total Revenue":       ("total_revenue",              None,                  "dollar"),
        "Rev / Call":          ("total_revenue",              "n_calls",             "dollar"),
        "Rev / Order":         ("total_revenue",              "n_orders",            "dollar"),
        "Top Product Mix":     ("tpsales_flag",               "orders",              "pct"),
        "Contact Rate":        ("ib_contact_calls",           "n_calls",             "pct"),
        "Credit Rate":         ("credit_calls_flag",          "n_calls",             "pct"),
        "Passed Credit Rate":  ("passed_credit_call_flag",    "credit_calls_flag",   "pct"),
        "Passed Credit Conv.": ("passed_credit_sale_flag",    "passed_credit_call_flag", "pct"),
        "Failed Credit Conv.": ("failed_credit_sale_flag",    "failed_credit_call_flag", "pct"),
        "Talk Time":           ("talk_time_minutes",          None,                  "decimal"),
        "Calls":               (None,                         None,                  "count"),
    }

    if "call_date_est" in df.columns and len(df) > 0:
        ov_ts_df = df.dropna(subset=["call_date_est"]).copy()
        ov_ts_df["period"] = period_labels(ov_ts_df["call_date_est"], ov_gran)

        num_col_ov, denom_col_ov, fmt_ov = METRIC_MAP_OV[ov_metric_choice]

        def agg_metric_ov(grp):
            inbound = grp[top_funnel_mask(grp)]
            orders_rev_rows = grp[order_revenue_mask(grp)]
            if ov_metric_choice == "Calls":
                return top_funnel_call_count(grp)
            elif ov_metric_choice == "Talk Time":
                return inbound["talk_time_minutes"].mean() if "talk_time_minutes" in inbound.columns else float("nan")
            elif ov_metric_choice == "Total Revenue":
                return orders_rev_rows["total_revenue"].sum() if "total_revenue" in orders_rev_rows.columns else orders_rev_rows["gcv_fo"].sum() if "gcv_fo" in orders_rev_rows.columns else 0
            elif fmt_ov == "dollar" and denom_col_ov:
                num = orders_rev_rows["total_revenue"].sum() if "total_revenue" in orders_rev_rows.columns else 0
                denom = top_funnel_call_count(grp) if denom_col_ov == "n_calls" else (orders_rev_rows["orders"].sum() if "orders" in orders_rev_rows.columns else 0)
                return safe_rate(num, denom)
            elif fmt_ov == "pct":
                if num_col_ov not in inbound.columns:
                    return float("nan")
                num = inbound[num_col_ov].sum()
                if denom_col_ov == "n_calls":
                    denom = top_funnel_call_count(grp)
                elif denom_col_ov and denom_col_ov in inbound.columns:
                    denom = inbound[denom_col_ov].sum()
                else:
                    return float("nan")
                return safe_rate(num, denom)
            return float("nan")

        ov_ts_overall = (
            ov_ts_df.groupby("period")
            .apply(agg_metric_ov)
            .reset_index()
            .rename(columns={0: "value"})
        )
        ov_ts_overall["period"] = pd.to_datetime(ov_ts_overall["period"])
        ov_ts_overall = ov_ts_overall.sort_values("period")
        ov_ts_overall["period_display"] = ov_ts_overall["period"].dt.strftime(PERIOD_FMT[ov_gran])

        fig_ov_trend = go.Figure()
        _ax_ov = plotly_axis_lines()
        _muted = "#64748b" if chart_theme_is_light() else "#8b95aa"

        if ov_group_col and ov_group_col in ov_ts_df.columns:
            for group_val, grp_c in ov_ts_df.groupby(ov_group_col):
                ts_c = (
                    grp_c.groupby("period")
                    .apply(agg_metric_ov)
                    .reset_index()
                    .rename(columns={0: "value"})
                )
                ts_c["period"] = pd.to_datetime(ts_c["period"])
                ts_c = ts_c.sort_values("period")
                fig_ov_trend.add_trace(go.Scatter(
                    x=ts_c["period"], y=ts_c["value"],
                    name=str(group_val), mode="lines+markers",
                    line=dict(width=2), marker=dict(size=5),
                ))

        fig_ov_trend.add_trace(go.Scatter(
            x=ov_ts_overall["period"], y=ov_ts_overall["value"],
            name="Overall", mode="lines+markers",
            line=dict(width=2, dash="dot", color=_muted),
            marker=dict(size=5, color=_muted),
        ))

        tick_vals = ov_ts_overall["period"].tolist()
        tick_text = ov_ts_overall["period"].dt.strftime(PERIOD_FMT[ov_gran]).tolist()

        if fmt_ov == "pct":
            y_fmt, y_prefix, y_suffix, y_title = ".1%", "", "", ov_metric_choice
        elif fmt_ov == "dollar":
            y_fmt, y_prefix, y_suffix, y_title = ",.0f", "$", "", ov_metric_choice
        elif ov_metric_choice == "Talk Time":
            y_fmt, y_prefix, y_suffix, y_title = ".2f", "", "", "Talk Time (Minutes)"
        else:
            y_fmt, y_prefix, y_suffix, y_title = ",.0f", "", "", ov_metric_choice

        _tcol = "#0f172a" if chart_theme_is_light() else "#e8ecf4"
        _trend_title = overview_chart_title(ov_metric_choice, ov_group_choice)
        apply_chart_theme(
            fig_ov_trend,
            title=dict(text=_trend_title, x=0.02, xanchor="left", font=dict(size=16, color=_tcol)),
            yaxis_tickformat=y_fmt,
            yaxis_tickprefix=y_prefix,
            yaxis_ticksuffix=y_suffix,
            yaxis_title=y_title,
            xaxis=dict(tickvals=tick_vals, ticktext=tick_text, **_ax_ov),
            height=400,
            margin=dict(l=50, r=20, t=48, b=40),
            legend=dict(orientation="h", y=-0.2),
        )
        st.plotly_chart(fig_ov_trend, use_container_width=True)

        # ── Performance snapshot (bar) — same metric / group as trend ───────────
        st.divider()
        st.subheader("Performance Snapshot")
        st.caption(
            "Same metric and group by as above · one value per category for the full filtered date range."
        )
        _snap_title = overview_chart_title(ov_metric_choice, ov_group_choice)

        def _fmt_bar_val(v):
            if v is None or (isinstance(v, float) and pd.isna(v)):
                return "—"
            if fmt_ov == "pct":
                return f"{v:.1%}"
            if fmt_ov == "dollar":
                return f"${v:,.0f}"
            if ov_metric_choice == "Talk Time":
                return f"{v:.1f}"
            return f"{v:,.0f}"

        if ov_group_col and ov_group_col in ov_ts_df.columns:
            bar_parts = [{"Category": str(gv), "Value": agg_metric_ov(gx)} for gv, gx in ov_ts_df.groupby(ov_group_col)]
            bar_df = pd.DataFrame(bar_parts).sort_values("Value", ascending=False, na_position="last")
        else:
            bar_df = pd.DataFrame([{"Category": "Overall", "Value": agg_metric_ov(ov_ts_df)}])

        _bar_colors = (PLOT_COLORWAY * (1 + len(bar_df) // max(len(PLOT_COLORWAY), 1)))[: max(len(bar_df), 1)]
        _tcol2 = "#0f172a" if chart_theme_is_light() else "#e8ecf4"
        _mline = "#cbd5e1" if chart_theme_is_light() else "#252b3a"
        fig_ov_bar = go.Figure(
            go.Bar(
                x=bar_df["Category"],
                y=bar_df["Value"],
                marker_color=_bar_colors,
                opacity=0.92,
                marker_line_color=_mline,
                marker_line_width=1,
                text=[_fmt_bar_val(v) for v in bar_df["Value"]],
                textposition="outside",
                textfont=dict(size=11, color=_tcol2),
            )
        )
        apply_chart_theme(
            fig_ov_bar,
            title=dict(text=_snap_title, x=0.02, xanchor="left", font=dict(size=16, color=_tcol2)),
            yaxis_tickformat=y_fmt,
            yaxis_tickprefix=y_prefix,
            yaxis_ticksuffix=y_suffix,
            yaxis_title=y_title,
            xaxis=dict(title="", tickangle=-22, automargin=True, **_ax_ov),
            height=min(920, 320 + 48 * max(len(bar_df), 1)),
            margin=dict(l=50, r=28, t=56, b=120),
            showlegend=False,
        )
        st.plotly_chart(fig_ov_bar, use_container_width=True)
    else:
        st.info("No data available for trend chart.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB — AGENT LEVEL
# ══════════════════════════════════════════════════════════════════════════════
with tab_agent:

    st.subheader("Agent-Level Performance")
    st.caption(
        "One row per agent. All sidebar filters apply. "
        "GCV metrics are per-call averages. Rates are computed from calls in the filtered date range."
    )

    agent_needed = {"agent_name", "orders", "total_revenue", "talk_time_minutes"}

    if not agent_needed.issubset(df.columns):
        missing = agent_needed - set(df.columns)
        st.info(f"Columns missing: {', '.join(sorted(missing))}")
    else:
        al_c1, al_c2, al_c3 = st.columns([2, 2, 1])
        with al_c1:
            agent_search = st.text_input("Search Agent", key="agent_search", placeholder="Type to filter…")
        with al_c2:
            sort_col = st.selectbox(
                "Sort By",
                ["Calls", "Net Conv.", "Rev / Call", "Rev / Order", "Top Product Mix",
                 "Total Revenue", "Talk Time", "Sold Talk Time"],
                key="agent_sort",
            )
        with al_c3:
            sort_asc = st.radio("Order", ["Desc", "Asc"], horizontal=True, key="agent_order") == "Asc"

        ag = df.copy()
        if agent_search:
            ag = ag[ag["agent_name"].astype(str).str.contains(agent_search, case=False, na=False)]

        def agent_agg(g):
            inbound = g[top_funnel_mask(g)]
            orders_rev_rows = g[order_revenue_mask(g)]
            n = top_funnel_call_count(g)
            n_orders  = orders_rev_rows["orders"].sum() if "orders" in orders_rev_rows.columns else 0
            n_tpsales = orders_rev_rows["tpsales_flag"].sum() if "tpsales_flag" in orders_rev_rows.columns else 0
            rev       = orders_rev_rows["total_revenue"].sum() if "total_revenue" in orders_rev_rows.columns else orders_rev_rows["gcv_fo"].sum() if "gcv_fo" in orders_rev_rows.columns else 0
            tt_all    = inbound["talk_time_minutes"].mean() if "talk_time_minutes" in inbound.columns else float("nan")
            tt_sold   = inbound[inbound["orders"] > 0]["talk_time_minutes"].mean() if "talk_time_minutes" in inbound.columns else float("nan")
            cohort    = g["membership"].mode()[0] if "membership" in g.columns and len(g) > 0 else "—"
            center    = g["center_location"].mode()[0] if "center_location" in g.columns and len(g) > 0 else "—"
            tenure    = g["tenure_bucket"].mode()[0] if "tenure_bucket" in g.columns and len(g) > 0 else "—"
            return pd.Series({
                "Calls":           n,
                "Center":          center,
                "Membership":      cohort,
                "Tenure":          tenure,
                "Net Conv.":       safe_rate(n_orders, n),
                "Top Product Mix": safe_rate(n_tpsales, n_orders),
                "Total Revenue":   rev,
                "Rev / Call":      safe_rate(rev, n),
                "Rev / Order":     safe_rate(rev, n_orders),
                "Talk Time":       tt_all,
                "Sold Talk Time":  tt_sold,
            })

        agent_df = (
            ag.groupby("agent_name")
            .apply(agent_agg)
            .reset_index()
            .rename(columns={"agent_name": "Agent"})
        )

        if sort_col in agent_df.columns:
            agent_df = agent_df.sort_values(sort_col, ascending=sort_asc)

        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric("Agents",          f"{len(agent_df):,}")
        sc2.metric("Avg Net Conv.",    f"{agent_df['Net Conv.'].mean():.1%}")
        sc3.metric("Avg Rev / Call",   f"${agent_df['Rev / Call'].mean():,.2f}")
        sc4.metric("Avg Talk Time",    f"{agent_df['Talk Time'].mean():.1f} min")

        # Distribution charts
        dc1, dc2 = st.columns(2)

        _hist_line = "#cbd5e1" if chart_theme_is_light() else "#252b3a"
        _ht = "#0f172a" if chart_theme_is_light() else "#e8ecf4"
        with dc1:
            st.markdown("**Net Conversion × Agents (Distribution)**")
            fig_nc = go.Figure(go.Histogram(
                x=agent_df["Net Conv."].dropna(),
                nbinsx=20,
                marker_color="#3d8ef8", opacity=0.8,
                marker_line_color=_hist_line,
                marker_line_width=1,
            ))
            apply_chart_theme(
                fig_nc,
                title=dict(text="Net conversion × agents", x=0.02, xanchor="left", font=dict(size=14, color=_ht)),
                xaxis_tickformat=".1%",
                xaxis_title="Net conversion",
                yaxis_title="Agents",
                height=260,
                margin=dict(l=44, r=20, t=40, b=44),
            )
            st.plotly_chart(fig_nc, use_container_width=True)

        with dc2:
            st.markdown("**Revenue Per Call × Agents (Distribution)**")
            fig_rc = go.Figure(go.Histogram(
                x=agent_df["Rev / Call"].dropna(), nbinsx=20,
                marker_color="#22d3c8", opacity=0.8,
                marker_line_color=_hist_line,
                marker_line_width=1,
            ))
            apply_chart_theme(
                fig_rc,
                title=dict(text="Revenue per call × agents", x=0.02, xanchor="left", font=dict(size=14, color=_ht)),
                xaxis_tickformat="$,.0f",
                xaxis_title="Revenue per call",
                yaxis_title="Agents",
                height=260,
                margin=dict(l=44, r=20, t=40, b=44),
            )
            st.plotly_chart(fig_rc, use_container_width=True)

        # Format for display
        fmt_df = agent_df.copy()
        for col in ["Net Conv.", "Top Product Mix"]:
            fmt_df[col] = fmt_df[col].apply(lambda x: f"{x:.1%}" if pd.notna(x) else "—")
        for col in ["Total Revenue", "Rev / Call", "Rev / Order"]:
            fmt_df[col] = fmt_df[col].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "—")
        for col in ["Talk Time", "Sold Talk Time"]:
            fmt_df[col] = fmt_df[col].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "—")
        fmt_df["Calls"] = fmt_df["Calls"].apply(lambda x: f"{x:,}")

        st.dataframe(
            fmt_df,
            use_container_width=True,
            hide_index=True,
            height=dataframe_display_height(len(fmt_df)),
        )
        table_export_row(fmt_df, "agent_level.csv")

with tab_lift:

    CENTER_CONFIG = {
        "Jamaica": {
            "file":       "data/lift_jamaica",
            "pre_start":  "2026-01-05",
            "pre_end":    "2026-03-01",
            "post_start": "2026-03-09",
            "post_end":   "2026-04-19",
        },
        "Durban": {
            "file":       "data/lift_durban",
            "pre_start":  "2026-02-16",
            "pre_end":    "2026-04-08",
            "post_start": "2026-04-09",
            "post_end":   "2026-04-28",
        },
    }

    LIFT_KPI_SPECS = [
        ("contact_rate",      "Contact Rate",        "pct"),
        ("credit_rate",       "Calls Into Credit",   "pct"),
        ("pass_credit_rate",  "Passed Credit Rate",  "pct"),
        ("pass_credit_conv",  "Passed Credit Conv.", "pct"),
        ("fail_credit_conv",  "Failed Credit Conv.", "pct"),
        ("nc",                "Net Conversion",      "pct"),
        ("rpo",               "RPO",                 "dollar"),
        ("rpnc",              "RPNC",                "dollar"),
        ("tt",                "Talk Time",           "decimal"),
        ("cm_call",           "CM / Call",           "dollar"),
    ]
    LIFT_KPI_KEYS   = [k for k, _, _ in LIFT_KPI_SPECS]
    LIFT_KPI_LABELS = {k: lbl for k, lbl, _ in LIFT_KPI_SPECS}
    LIFT_KPI_FMTS   = {k: fmt for k, _, fmt in LIFT_KPI_SPECS}
    CM_COST_PER_MIN = 0.4

    # ── Center selector ────────────────────────────────────────────────────────
    lift_center = st.selectbox(
        "Center", options=list(CENTER_CONFIG.keys()), key="lift_center"
    )
    cfg = CENTER_CONFIG[lift_center]

    # ── Load CSV ───────────────────────────────────────────────────────────────
    @st.cache_data(ttl=None)
    def load_lift_data(file_base):
        import glob
        chunks = []

        # Fixed files
        for period_label in ["post", "pre"]:
            path = f"{file_base}_{period_label}.csv"
            try:
                chunks.append(pd.read_csv(path, low_memory=False))
            except Exception as e:
                st.error(f"Could not load {path}: {e}")
                st.stop()

        # pre_weekly — variable number of split files
        pre_weekly_files = sorted(glob.glob(f"{file_base}_pre_weekly_*.csv"))
        if not pre_weekly_files:
            st.error(f"No pre_weekly files found matching {file_base}_pre_weekly_*.csv")
            st.stop()
        for path in pre_weekly_files:
            try:
                chunks.append(pd.read_csv(path, low_memory=False))
            except Exception as e:
                st.error(f"Could not load {path}: {e}")
                st.stop()

        df = pd.concat(chunks, ignore_index=True)
        df["call_datetime_est"] = pd.to_datetime(df["call_datetime_est"])
        df["call_date_fo"]      = pd.to_datetime(df["call_date_fo"])
        for col in ["talk_time_minutes", "order_orders", "gcv_revenue", "ibcalls",
                    "credit_calls_ind", "passed_credit_call_ind", "ib_contact_calls",
                    "passed_credit_sale", "failed_credit_sale"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df

    try:
        lift_raw = load_lift_data(cfg["file"])
    except Exception as e:
        st.error(f"Could not load lift data for {lift_center}: {e}")
        st.stop()

    # ── Durban week exclusion ──────────────────────────────────────────────────
    DURBAN_EXCLUDE_WEEK = "02/23/2026"
    exclude_feb23 = False
    if lift_center == "Durban":
        exclude_feb23 = st.checkbox(
            "Exclude week of 2/23 (Kingston test not yet launched)",
            value=False,
            key="lift_exclude_feb23",
        )

    # ── Tab-level date filter ──────────────────────────────────────────────────
    # Independent of the sidebar date filter. Scopes both pre_weekly and post
    # rows to the selected post date range. Pre_weekly rows are scoped by
    # post_week (the post week they serve as baseline for), not by their own
    # call date, so narrowing the post window automatically narrows the
    # pre baselines too.
    st.subheader("Date Range")
    post_dates = pd.to_datetime(
        lift_raw[lift_raw["period"] == "post"]["call_datetime_est"]
    )
    min_post_date = post_dates.min().date()
    max_post_date = post_dates.max().date()

    lift_date_col1, lift_date_col2 = st.columns(2)
    with lift_date_col1:
        lift_start_date = st.date_input(
            "Post Period From",
            value=min_post_date,
            min_value=min_post_date,
            max_value=max_post_date,
            key="lift_start_date",
        )
    with lift_date_col2:
        lift_end_date = st.date_input(
            "Post Period To",
            value=max_post_date,
            min_value=min_post_date,
            max_value=max_post_date,
            key="lift_end_date",
        )

    # ── Apply sidebar filters to ALL periods equally ───────────────────────────
    # pre_weekly, post, and pre (canonical) are all filtered the same way.
    # This means the summary table shows lift for the filtered call population
    # in both the pre baseline and post period — enabling slices by customer
    # type, marketing bucket, etc.
    # Cohort assignment is NOT re-derived after filtering — it was fixed at
    # extract time from the full unfiltered post population, ensuring agents
    # are in the same cohorts regardless of what filter is active.
    def apply_sidebar_filters(df):
        if sel_mkt      and "marketing_bucket" in df.columns:
            df = df[df["marketing_bucket"].isin(sel_mkt)]
        if sel_mov      and "mover_switcher"   in df.columns:
            df = df[df["mover_switcher"].isin(sel_mov)]
        if sel_calltype and "call_type"        in df.columns:
            df = df[df["call_type"].isin(sel_calltype)]
        if sel_tenure   and "tenure_bucket"    in df.columns:
            df = df[df["tenure_bucket"].isin(sel_tenure)]
        return df

    # Date filter for post rows: restrict to selected post date window.
    # For pre_weekly rows: restrict by post_week falling within the selected
    # window, so the pre baselines stay aligned with the visible post weeks.
    active_post_weeks = (
        lift_raw[
            (lift_raw["period"] == "post") &
            (lift_raw["call_datetime_est"].dt.date >= lift_start_date) &
            (lift_raw["call_datetime_est"].dt.date <= lift_end_date)
        ]["week"]
        .dropna()
        .unique()
        .tolist()
    )

    pre_weekly_base = lift_raw[
        (lift_raw["period"] == "pre_weekly") &
        (lift_raw["post_week"].isin(active_post_weeks))
    ].copy()

    post_base = lift_raw[
        (lift_raw["period"] == "post") &
        (lift_raw["call_datetime_est"].dt.date >= lift_start_date) &
        (lift_raw["call_datetime_est"].dt.date <= lift_end_date)
    ].copy()

    other_base = lift_raw[
        (lift_raw["period"] == "pre") &
        (lift_raw["call_datetime_est"].dt.date >= pd.to_datetime(cfg["pre_start"]).date()) &
        (lift_raw["call_datetime_est"].dt.date <= pd.to_datetime(cfg["pre_end"]).date())
    ].copy()

    pre_weekly_raw = apply_sidebar_filters(pre_weekly_base)
    lf             = apply_sidebar_filters(
        pd.concat([post_base, other_base], ignore_index=True)
    )

    if exclude_feb23:
        pre_weekly_raw = pre_weekly_raw[
            pre_weekly_raw["post_week"] != DURBAN_EXCLUDE_WEEK
        ]
        lf = lf[lf["week"] != DURBAN_EXCLUDE_WEEK]

    # post rows — cohort fixed by Spark at extract time
    post_tagged = lf[(lf["period"] == "post") & lf["cohort"].notna()].copy()

    # pre canonical rows — for trend chart only
    pre_tagged = lf[(lf["period"] == "pre") & lf["canonical_cohort"].notna()].copy()
    pre_tagged = pre_tagged.drop(columns=["cohort"], errors="ignore")
    pre_tagged = pre_tagged.rename(columns={"canonical_cohort": "cohort"})

    # ── KPI computation ────────────────────────────────────────────────────────
    def safe_rate(num, den):
        try:
            return float(num) / float(den) if den and float(den) != 0 else float("nan")
        except Exception:
            return float("nan")

    def compute_lift_kpis(d):
        ib_mask = top_funnel_mask(d)
        ib_d = d[ib_mask]
        orders_rev_rows = d[order_revenue_mask(d)]

        net_call      = int(ib_mask.sum())
        orders        = orders_rev_rows["order_orders"].sum() if "order_orders" in orders_rev_rows.columns else 0
        revenue       = orders_rev_rows["gcv_revenue"].sum() if "gcv_revenue" in orders_rev_rows.columns else 0
        tt_avg        = safe_rate(ib_d["talk_time_minutes"].sum(), net_call)
        contact_calls = ib_d["ib_contact_calls"].sum()       if "ib_contact_calls"       in d.columns else 0
        credit_calls  = ib_d["credit_calls_ind"].sum()       if "credit_calls_ind"        in d.columns else 0
        pass_cr_calls = int((ib_d["passed_credit_call_ind"] == 1).sum()) \
                        if "passed_credit_call_ind" in d.columns else 0
        fail_cr_calls = int(
            ((ib_d["credit_calls_ind"] == 1) & (ib_d["passed_credit_call_ind"] != 1)).sum()
        ) if "credit_calls_ind" in d.columns and "passed_credit_call_ind" in d.columns else 0
        pass_cr_sold  = int(
            ((ib_d["passed_credit_call_ind"] == 1) & (ib_d["order_orders"] > 0)).sum()
        ) if "passed_credit_call_ind" in d.columns else 0
        fail_cr_sold  = int(
            (
                (ib_d["credit_calls_ind"] == 1) &
                (ib_d["passed_credit_call_ind"] != 1) &
                (ib_d["order_orders"] > 0)
            ).sum()
        ) if "credit_calls_ind" in d.columns and "passed_credit_call_ind" in d.columns else 0

        rpnc = safe_rate(revenue, net_call)
        return {
            "net_call":         net_call,
            "orders":           orders,
            "revenue":          revenue,
            "contact_rate":     safe_rate(contact_calls, net_call),
            "credit_rate":      safe_rate(credit_calls,  net_call),
            "pass_credit_rate": safe_rate(pass_cr_calls, credit_calls),
            "pass_credit_conv": safe_rate(pass_cr_sold,  pass_cr_calls),
            "fail_credit_conv": safe_rate(fail_cr_sold,  fail_cr_calls),
            "nc":               safe_rate(orders,        net_call),
            "rpo":              safe_rate(revenue,       orders),
            "rpnc":             rpnc,
            "tt":               tt_avg,
            "cm_call":          rpnc - CM_COST_PER_MIN * tt_avg
                                if not (pd.isna(rpnc) or pd.isna(tt_avg))
                                else float("nan"),
        }

    def safe_delta_pct(arc, atom):
        if pd.isna(arc) or pd.isna(atom) or atom == 0:
            return float("nan")
        return arc / atom - 1

    # ── Weighted-average summary ───────────────────────────────────────────────
    post_weeks = sorted(post_tagged["week"].dropna().unique())

    weekly_records = []
    for wk in post_weeks:
        post_wk_arc  = post_tagged[
            (post_tagged["week"] == wk) & (post_tagged["cohort"] == "Arcadia")
        ]
        post_wk_atom = post_tagged[
            (post_tagged["week"] == wk) & (post_tagged["cohort"] == "Atom")
        ]
        pre_wk_arc   = pre_weekly_raw[
            (pre_weekly_raw["post_week"] == wk) & (pre_weekly_raw["cohort"] == "Arcadia")
        ]
        pre_wk_atom  = pre_weekly_raw[
            (pre_weekly_raw["post_week"] == wk) & (pre_weekly_raw["cohort"] == "Atom")
        ]

        if any(x.empty for x in [post_wk_arc, post_wk_atom, pre_wk_arc, pre_wk_atom]):
            continue

        post_arc_k  = compute_lift_kpis(post_wk_arc)
        post_atom_k = compute_lift_kpis(post_wk_atom)
        pre_arc_k   = compute_lift_kpis(pre_wk_arc)
        pre_atom_k  = compute_lift_kpis(pre_wk_atom)

        week_weight = (
            top_funnel_call_count(post_wk_arc) +
            top_funnel_call_count(post_wk_atom)
        )

        rec = {"week": wk, "weight": week_weight}
        for k in LIFT_KPI_KEYS:
            pre_d  = safe_delta_pct(
                pre_arc_k.get(k,  float("nan")),
                pre_atom_k.get(k, float("nan"))
            )
            post_d = safe_delta_pct(
                post_arc_k.get(k, float("nan")),
                post_atom_k.get(k, float("nan"))
            )
            rec[f"pre_arc_{k}"]    = pre_arc_k.get(k,   float("nan"))
            rec[f"pre_atom_{k}"]   = pre_atom_k.get(k,  float("nan"))
            rec[f"post_arc_{k}"]   = post_arc_k.get(k,  float("nan"))
            rec[f"post_atom_{k}"]  = post_atom_k.get(k, float("nan"))
            rec[f"pre_delta_{k}"]  = pre_d
            rec[f"post_delta_{k}"] = post_d
            rec[f"swing_{k}"]      = (
                post_d - pre_d
                if not (pd.isna(post_d) or pd.isna(pre_d))
                else float("nan")
            )
        weekly_records.append(rec)

    weekly_df = pd.DataFrame(weekly_records)

    def weighted_avg(col):
        if weekly_df.empty:
            return float("nan")
        valid = weekly_df[["weight", col]].dropna()
        if valid.empty or valid["weight"].sum() == 0:
            return float("nan")
        return (valid[col] * valid["weight"]).sum() / valid["weight"].sum()

    n_weeks      = len(weekly_df)
    total_weight = int(weekly_df["weight"].sum()) if not weekly_df.empty else 0

    # ── Section 1: KPI cards ───────────────────────────────────────────────────
    st.subheader(f"{lift_center} — Test Period Lift Summary")

    # Show a notice when filters are active so users understand the
    # pre baseline is also scoped to the filtered call population
    active_filters = []
    if sel_mkt:      active_filters.append(f"Marketing: {', '.join(sel_mkt)}")
    if sel_mov:      active_filters.append(f"Mover/Switcher: {', '.join(sel_mov)}")
    if sel_calltype: active_filters.append(f"Call Type: {', '.join(sel_calltype)}")
    if sel_tenure:   active_filters.append(f"Tenure: {', '.join(sel_tenure)}")

    caption_base = (
        f"Pre: {cfg['pre_start']} → {cfg['pre_end']}  ·  "
        f"Post: {cfg['post_start']} → {cfg['post_end']}  ·  "
        f"Weighted avg of {n_weeks} weekly swings  ·  "
        f"Weight = post IB calls/week  ·  "
        f"Total post IB calls: {total_weight:,}"
    )
    if active_filters:
        caption_base += f"  ·  Filters active: {' | '.join(active_filters)}"
        caption_base += "  ·  Pre baseline scoped to same filtered call types"

    st.caption(caption_base)

    def fmt_swing_metric(k):
        s      = weighted_avg(f"swing_{k}")
        post_d = weighted_avg(f"post_delta_{k}")
        if pd.isna(s):
            return "—", None
        sign      = "+" if s > 0 else ""
        post_sign = "+" if not pd.isna(post_d) and post_d > 0 else ""
        return (
            f"{sign}{s*100:.1f}pp swing",
            f"Post Δ: {post_sign}{post_d*100:.1f}pp" if not pd.isna(post_d) else None,
        )

    top_kpis = [
        ("rpnc",        "RPNC"),
        ("nc",          "Net Conversion"),
        ("rpo",         "RPO"),
        ("credit_rate", "Calls Into Credit"),
        ("tt",          "Talk Time"),
    ]
    kc = st.columns(5)
    for i, (k, lbl) in enumerate(top_kpis):
        val, delta = fmt_swing_metric(k)
        kc[i].metric(
            lbl,
            val,
            delta=delta,
            delta_color="inverse" if k in LIFT_KPI_LOWER_IS_BETTER else "normal",
        )

    st.divider()

    # ── Section 2: Summary table ───────────────────────────────────────────────
    st.subheader("Pre vs Post Summary Table")
    st.caption(
        "All values are weighted averages across post weeks, "
        "weighted by total post IB calls per week. "
        "Pre baseline uses the same filters as the post period."
    )

    def fmt_kpi_val(k, v):
        if pd.isna(v):
            return "—"
        fmt = LIFT_KPI_FMTS[k]
        if fmt == "pct":    return f"{v:.1%}"
        if fmt == "dollar": return f"${v:,.1f}"
        return f"{v:.2f}"

    def fmt_delta_cell(v):
        if pd.isna(v):
            return "—"
        sign = "+" if v > 0 else ""
        return f"{sign}{v*100:.1f}%"

    table_rows = []
    for k, lbl, _ in LIFT_KPI_SPECS:
        table_rows.append({
            "KPI":            lbl,
            "Pre — Arcadia":  fmt_kpi_val(k, weighted_avg(f"pre_arc_{k}")),
            "Pre — Atom":     fmt_kpi_val(k, weighted_avg(f"pre_atom_{k}")),
            "Pre Δ":          fmt_delta_cell(weighted_avg(f"pre_delta_{k}")),
            "Post — Arcadia": fmt_kpi_val(k, weighted_avg(f"post_arc_{k}")),
            "Post — Atom":    fmt_kpi_val(k, weighted_avg(f"post_atom_{k}")),
            "Post Δ":         fmt_delta_cell(weighted_avg(f"post_delta_{k}")),
            "Swing":          fmt_delta_cell(weighted_avg(f"swing_{k}")),
        })

    _lift_lbl_to_key = {lbl: k for k, lbl, _ in LIFT_KPI_SPECS}

    def _style_lift_summary_row(row):
        k = _lift_lbl_to_key.get(row["KPI"])
        out = pd.Series("", index=row.index)
        if k is None:
            return out
        for col in ("Pre Δ", "Post Δ", "Swing"):
            if col not in out.index:
                continue
            p = parse_display_pct(row[col])
            if p is None:
                continue
            out[col] = pct_change_cell_style(k, p)
        return out

    summary_tbl = pd.DataFrame(table_rows)
    styler = summary_tbl.style.apply(_style_lift_summary_row, axis=1)
    st.dataframe(
        styler,
        use_container_width=True,
        hide_index=True,
        height=dataframe_display_height(len(summary_tbl)),
    )
    table_export_row(summary_tbl, "arcadia_vs_atom_summary.csv")

    st.divider()

    # ── Section 3: Trend chart ─────────────────────────────────────────────────
    st.subheader("Trend Over Time")
    st.caption(
        "Solid lines = Arcadia, dashed = Atom. "
        "Use 'View' to plot raw KPI values, Post Δ, or Swing. "
        "Sidebar filters apply to both pre and post."
    )

    lt_c1, lt_c2, lt_c3 = st.columns(3)
    with lt_c1:
        lift_metric     = st.selectbox(
            "Metric",
            options=[lbl for _, lbl, _ in LIFT_KPI_SPECS],
            key="lift_metric",
        )
        lift_metric_key = {lbl: k for k, lbl, _ in LIFT_KPI_SPECS}[lift_metric]
        lift_metric_fmt = LIFT_KPI_FMTS[lift_metric_key]
    with lt_c2:
        LIFT_GROUP_MAP = {
            "None (Overall)":   None,
            "Marketing Bucket": "marketing_bucket",
            "Mover / Switcher": "mover_switcher",
            "Tenure Bucket":    "tenure_bucket",
            "Call Type":        "call_type",
        }
        lift_group_choice = st.selectbox(
            "Group By",
            options=list(LIFT_GROUP_MAP.keys()),
            key="lift_group",
        )
        lift_group_col = LIFT_GROUP_MAP[lift_group_choice]
    with lt_c3:
        lift_view = st.selectbox(
            "View",
            options=["Raw KPI Value", "Post Δ (Arc/Atom−1)", "Swing (Post Δ − Pre Δ)"],
            key="lift_view",
        )

    def weekly_kpis_for_cohort(df_tagged, cohort, group_col=None):
        sub = df_tagged[df_tagged["cohort"] == cohort].copy()
        if sub.empty:
            return pd.DataFrame()
        group_cols = ["week"] + ([group_col] if group_col else [])
        rows = []
        for keys, grp in sub.groupby(group_cols):
            if not isinstance(keys, tuple):
                keys = (keys,)
            kpis = compute_lift_kpis(grp)
            row  = dict(zip(group_cols, keys))
            row["cohort"] = cohort
            row["value"]  = kpis.get(lift_metric_key, float("nan"))
            rows.append(row)
        return pd.DataFrame(rows)

    def pre_kpi_for_cohort(cohort, group_col=None, group_val=None):
        sub = pre_tagged[pre_tagged["cohort"] == cohort]
        if group_col and group_val:
            sub = sub[sub[group_col] == group_val]
        return compute_lift_kpis(sub).get(lift_metric_key, float("nan"))

    post_arc_weekly  = weekly_kpis_for_cohort(post_tagged, "Arcadia", lift_group_col)
    post_atom_weekly = weekly_kpis_for_cohort(post_tagged, "Atom",    lift_group_col)

    def build_trend_series(post_arc_w, post_atom_w, view, group_col):
        traces     = []
        group_vals = [None]
        if group_col:
            all_vals = pd.concat([
                post_arc_w[group_col]
                    if not post_arc_w.empty  and group_col in post_arc_w
                    else pd.Series(dtype=str),
                post_atom_w[group_col]
                    if not post_atom_w.empty and group_col in post_atom_w
                    else pd.Series(dtype=str),
            ]).dropna().unique().tolist()
            group_vals = sorted(all_vals)

        for gv in group_vals:
            for cohort, w_df, dash in [
                ("Arcadia", post_arc_w, "solid"),
                ("Atom",    post_atom_w, "dot"),
            ]:
                sub = w_df.copy() if w_df is not None else pd.DataFrame()
                if sub.empty:
                    continue
                if group_col and gv is not None:
                    sub = sub[sub[group_col] == gv]
                if sub.empty:
                    continue
                sub["week_dt"] = pd.to_datetime(
                    sub["week"], format="%m/%d/%Y", errors="coerce"
                )
                sub = sub.dropna(subset=["week_dt"]).sort_values("week_dt")

                if view == "Raw KPI Value":
                    y_vals = sub["value"].tolist()

                elif view == "Post Δ (Arc/Atom−1)":
                    if cohort != "Arcadia":
                        continue
                    atom_sub = post_atom_w.copy()
                    if group_col and gv is not None:
                        atom_sub = atom_sub[atom_sub[group_col] == gv]
                    atom_sub["week_dt"] = pd.to_datetime(
                        atom_sub["week"], format="%m/%d/%Y", errors="coerce"
                    )
                    atom_map = atom_sub.set_index("week_dt")["value"].to_dict()
                    y_vals = [
                        safe_delta_pct(v, atom_map.get(wk, float("nan")))
                        for v, wk in zip(sub["value"], sub["week_dt"])
                    ]

                elif view == "Swing (Post Δ − Pre Δ)":
                    if cohort != "Arcadia":
                        continue
                    atom_sub = post_atom_w.copy()
                    if group_col and gv is not None:
                        atom_sub = atom_sub[atom_sub[group_col] == gv]
                    atom_sub["week_dt"] = pd.to_datetime(
                        atom_sub["week"], format="%m/%d/%Y", errors="coerce"
                    )
                    atom_map = atom_sub.set_index("week_dt")["value"].to_dict()

                    # Compute pre_d from pre_weekly_raw (same source as summary
                    # table) rather than pre_tagged, so the swing baseline
                    # matches what the cards and table show.
                    pre_d_by_week = {}
                    for wk_label in post_weeks:
                        pw_arc_pre  = pre_weekly_raw[
                            (pre_weekly_raw["post_week"] == wk_label) &
                            (pre_weekly_raw["cohort"] == "Arcadia")
                        ]
                        pw_atom_pre = pre_weekly_raw[
                            (pre_weekly_raw["post_week"] == wk_label) &
                            (pre_weekly_raw["cohort"] == "Atom")
                        ]
                        if group_col and gv is not None:
                            pw_arc_pre  = pw_arc_pre[pw_arc_pre[group_col]  == gv]
                            pw_atom_pre = pw_atom_pre[pw_atom_pre[group_col] == gv]
                        if pw_arc_pre.empty or pw_atom_pre.empty:
                            pre_d_by_week[wk_label] = float("nan")
                            continue
                        arc_v  = compute_lift_kpis(pw_arc_pre).get(lift_metric_key,  float("nan"))
                        atom_v = compute_lift_kpis(pw_atom_pre).get(lift_metric_key, float("nan"))
                        pre_d_by_week[wk_label] = safe_delta_pct(arc_v, atom_v)

                    # Convert week labels to datetime for lookup
                    pre_d_by_week_dt = {
                        pd.to_datetime(wk, format="%m/%d/%Y"): v
                        for wk, v in pre_d_by_week.items()
                    }

                    y_vals = []
                    for v, wk in zip(sub["value"], sub["week_dt"]):
                        post_d = safe_delta_pct(v, atom_map.get(wk, float("nan")))
                        pre_d  = pre_d_by_week_dt.get(wk, float("nan"))
                        y_vals.append(
                            post_d - pre_d
                            if not (pd.isna(post_d) or pd.isna(pre_d))
                            else float("nan")
                        )
                else:
                    y_vals = sub["value"].tolist()

                label = f"{gv} — {cohort}" if gv else cohort
                traces.append((label, sub["week_dt"].tolist(), y_vals, dash))

        return traces

    traces = build_trend_series(
        post_arc_weekly, post_atom_weekly, lift_view, lift_group_col
    )

    if traces:
        fig_lift = go.Figure()
        for label, x_vals, y_vals, dash in traces:
            fig_lift.add_trace(go.Scatter(
                x=x_vals, y=y_vals,
                name=label,
                mode="lines+markers",
                line=dict(width=2, dash=dash),
                marker=dict(size=5),
            ))

        is_pct    = lift_metric_fmt == "pct" or lift_view in (
            "Post Δ (Arc/Atom−1)", "Swing (Post Δ − Pre Δ)"
        )
        is_dollar = lift_metric_fmt == "dollar" and lift_view == "Raw KPI Value"
        all_x     = sorted(set(x for _, xs, _, _ in traces for x in xs))

        _lift_ax = plotly_axis_lines()
        _lift_title = lift_chart_title(lift_metric, lift_group_choice, lift_view)
        _lift_tcol = "#0f172a" if chart_theme_is_light() else "#e8ecf4"
        apply_chart_theme(
            fig_lift,
            title=dict(text=_lift_title, x=0.02, xanchor="left", font=dict(size=16, color=_lift_tcol)),
            yaxis_tickformat=".1%" if is_pct else ("$,.1f" if is_dollar else ".2f"),
            yaxis_tickprefix="$" if is_dollar else "",
            xaxis=dict(
                tickvals=all_x,
                ticktext=[x.strftime("%b %d") for x in all_x],
                **_lift_ax,
            ),
            height=420,
            margin=dict(l=50, r=20, t=48, b=40),
            legend=dict(orientation="h", y=-0.25),
        )

        if lift_view in ("Post Δ (Arc/Atom−1)", "Swing (Post Δ − Pre Δ)"):
            fig_lift.add_hline(
                y=0,
                line_dash="dash",
                line_color="#4d5669",
                annotation_text="0",
                annotation_font_color="#4d5669",
            )

        st.plotly_chart(fig_lift, use_container_width=True)
    else:
        st.info("No data available for the selected combination.")