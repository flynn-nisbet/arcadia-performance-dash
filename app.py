import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from datetime import timedelta, date

st.set_page_config(
    page_title="Arcadia Performance Dash",
    page_icon="⚡",
    layout="wide",
)

# ── Custom CSS (matching Product Rank Dash styling) ───────────────────────────
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
    color: var(--text-primary);
}

.stApp {
    background-color: var(--bg-base) !important;
    background-image:
        radial-gradient(ellipse 80% 40% at 50% -10%, rgba(61,142,248,0.08) 0%, transparent 60%),
        radial-gradient(ellipse 40% 30% at 90% 80%, rgba(34,211,200,0.04) 0%, transparent 50%);
}

.main .block-container {
    padding: 2rem 2.5rem 4rem !important;
    max-width: 1600px !important;
}

[data-testid="stSidebar"] {
    background-color: var(--bg-card) !important;
    border-right: 1px solid var(--border) !important;
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
    color: var(--text-primary) !important;
}
h1 { font-size: 1.8rem !important; font-weight: 800 !important; letter-spacing: -0.01em !important; }
h2 { font-size: 1.25rem !important; font-weight: 700 !important; letter-spacing: 0.01em !important; }
h3 { font-size: 1rem !important; font-weight: 600 !important; }

[data-testid="stHeading"] h1 {
    background: linear-gradient(135deg, var(--text-primary) 0%, var(--accent) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 2rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.02em !important;
    padding-bottom: 0.1em;
}

.stCaptionContainer, [data-testid="stCaptionContainer"], small, caption {
    color: var(--text-secondary) !important;
    font-size: 0.78rem !important;
    line-height: 1.5 !important;
}

[data-testid="stMetric"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
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
[data-testid="stMetricLabel"] { font-size: 0.68rem !important; font-weight: 500 !important; letter-spacing: 0.1em !important; text-transform: uppercase !important; color: var(--text-secondary) !important; font-family: 'DM Sans', sans-serif !important; }
[data-testid="stMetricValue"] { font-family: 'DM Mono', monospace !important; font-size: 1.5rem !important; font-weight: 500 !important; color: var(--text-primary) !important; line-height: 1.2 !important; }
[data-testid="stMetricDelta"] { font-family: 'DM Mono', monospace !important; font-size: 0.75rem !important; }
[data-testid="stMetricDelta"] svg { display: none !important; }

[data-testid="stTabs"] [role="tablist"] { border-bottom: 1px solid var(--border) !important; gap: 0 !important; background: transparent !important; }
[data-testid="stTabs"] [role="tab"] { font-family: 'Syne', sans-serif !important; font-size: 0.78rem !important; font-weight: 600 !important; letter-spacing: 0.07em !important; text-transform: uppercase !important; color: var(--text-muted) !important; padding: 0.6rem 1.25rem !important; border: none !important; border-bottom: 2px solid transparent !important; background: transparent !important; transition: color 0.15s, border-color 0.15s !important; }
[data-testid="stTabs"] [role="tab"]:hover { color: var(--text-secondary) !important; border-bottom-color: var(--border-bright) !important; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] { color: var(--accent) !important; border-bottom-color: var(--accent) !important; background: transparent !important; }

hr { border: none !important; border-top: 1px solid var(--border) !important; margin: 2rem 0 !important; }

.stSelectbox > div > div,
.stMultiSelect > div > div,
.stTextInput > div > div > input,
.stDateInput > div > div > input {
    background-color: var(--bg-card-alt) !important;
    border: 1px solid var(--border-bright) !important;
    border-radius: var(--radius) !important;
    color: var(--text-primary) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
    transition: border-color 0.15s !important;
}
.stSelectbox > div > div:focus-within,
.stMultiSelect > div > div:focus-within { border-color: var(--accent) !important; box-shadow: 0 0 0 2px var(--accent-glow) !important; outline: none !important; }

[data-baseweb="menu"] { background-color: var(--bg-card-alt) !important; border: 1px solid var(--border-bright) !important; border-radius: var(--radius) !important; }
[data-baseweb="menu"] li { font-family: 'DM Sans', sans-serif !important; font-size: 0.85rem !important; color: var(--text-primary) !important; }
[data-baseweb="menu"] li:hover { background-color: var(--bg-hover) !important; }
[data-baseweb="tag"] { background-color: var(--accent-dim) !important; border: none !important; border-radius: 4px !important; font-size: 0.75rem !important; }

.stRadio > div { gap: 0.5rem !important; background: transparent !important; border: none !important; padding: 0 !important; display: inline-flex !important; }
.stRadio label { font-size: 0.75rem !important; font-weight: 500 !important; letter-spacing: 0.05em !important; text-transform: uppercase !important; padding: 0.3rem 0.85rem !important; border-radius: 6px !important; cursor: pointer !important; color: var(--text-secondary) !important; background: transparent !important; transition: color 0.15s !important; }

[data-testid="stDataFrame"], .stDataFrame { border: 1px solid var(--border) !important; border-radius: var(--radius-lg) !important; overflow: hidden !important; }
[data-testid="stDataFrame"] thead th { background: var(--bg-card-alt) !important; font-family: 'DM Sans', sans-serif !important; font-size: 0.68rem !important; font-weight: 600 !important; letter-spacing: 0.1em !important; text-transform: uppercase !important; color: var(--text-secondary) !important; border-bottom: 1px solid var(--border-bright) !important; padding: 0.6rem 0.8rem !important; }
[data-testid="stDataFrame"] tbody td { font-family: 'DM Mono', monospace !important; font-size: 0.82rem !important; color: var(--text-primary) !important; border-bottom: 1px solid var(--border) !important; padding: 0.5rem 0.8rem !important; background: var(--bg-card) !important; }
[data-testid="stDataFrame"] tbody tr:hover td { background: var(--bg-hover) !important; }

.stButton > button { background: var(--accent) !important; color: white !important; border: none !important; border-radius: var(--radius) !important; font-family: 'DM Sans', sans-serif !important; font-size: 0.8rem !important; font-weight: 600 !important; letter-spacing: 0.05em !important; padding: 0.5rem 1.25rem !important; transition: all 0.15s !important; }
.stButton > button:hover { background: var(--accent-dim) !important; box-shadow: 0 4px 12px rgba(61,142,248,0.3) !important; transform: translateY(-1px) !important; }

[data-testid="stHeading"] h2, .stMarkdown h2 { color: var(--text-primary) !important; font-size: 1.1rem !important; font-weight: 700 !important; letter-spacing: 0.02em !important; padding-top: 0.25rem !important; padding-bottom: 0.5rem !important; border-bottom: 1px solid var(--border) !important; margin-bottom: 1rem !important; }

[data-testid="stInfo"] { background: rgba(61,142,248,0.08) !important; border: 1px solid rgba(61,142,248,0.25) !important; border-radius: var(--radius) !important; color: var(--accent) !important; font-size: 0.85rem !important; }
[data-testid="stWarning"] { background: rgba(245,166,35,0.08) !important; border: 1px solid rgba(245,166,35,0.25) !important; border-radius: var(--radius) !important; color: var(--amber) !important; }

[data-testid="stCaptionContainer"] p { color: var(--text-muted) !important; font-size: 0.78rem !important; font-family: 'DM Mono', monospace !important; letter-spacing: 0.05em !important; }
.stMarkdown strong { color: var(--text-primary) !important; font-weight: 600 !important; }

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg-base); }
::-webkit-scrollbar-thumb { background: var(--border-bright); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }
</style>
""", unsafe_allow_html=True)

# ── Plotly dark theme ──────────────────────────────────────────────────────────
PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, sans-serif", color="#8b95aa", size=12),
    xaxis=dict(gridcolor="#1e2330", linecolor="#252b3a", tickcolor="#252b3a", zerolinecolor="#252b3a"),
    yaxis=dict(gridcolor="#1e2330", linecolor="#252b3a", tickcolor="#252b3a", zerolinecolor="#252b3a"),
    legend=dict(bgcolor="rgba(19,22,29,0.8)", bordercolor="#252b3a", borderwidth=1, font=dict(size=11, color="#8b95aa")),
    colorway=["#3d8ef8", "#22d3c8", "#f5a623", "#f43f5e", "#a78bfa", "#22c55e"],
)

def apply_dark_theme(fig, **extra):
    fig.update_layout(**{**PLOT_LAYOUT, **extra})
    return fig

# ── Load data ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl="24h")
def load_data():
    path = "agent_calls_data.csv"
    df = pd.read_csv(path)
    df["call_date_est"] = pd.to_datetime(df["call_date_est"])
    return df

try:
    df_raw = load_data()
except FileNotFoundError:
    st.error("agent_calls_data.csv not found. Make sure the data pipeline has run.")
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
    serp_opts     = sorted(df_raw["site_serp"].dropna().unique().tolist()) if "site_serp" in df_raw.columns else []
    mov_opts      = sorted(df_raw["moverSwitcher"].dropna().unique().tolist()) if "moverSwitcher" in df_raw.columns else []
    tenure_opts   = sorted(df_raw["tenure_bucket"].dropna().unique().tolist()) if "tenure_bucket" in df_raw.columns else []
    calltype_opts = sorted(df_raw["call_type"].dropna().unique().tolist()) if "call_type" in df_raw.columns else []
    cohort_opts   = sorted(df_raw["membership"].dropna().unique().tolist()) if "membership" in df_raw.columns else []

    sel_center   = st.multiselect("Center",           options=center_opts,   default=[], key="f_center")
    sel_mkt      = st.multiselect("Marketing Bucket", options=mkt_opts,      default=[], key="f_mkt")
    sel_serp     = st.multiselect("Site / SERP",      options=serp_opts,     default=[], key="f_serp")
    sel_mov      = st.multiselect("Mover / Switcher", options=mov_opts,      default=[], key="f_mov")
    sel_tenure   = st.multiselect("Tenure Bucket",    options=tenure_opts,   default=[], key="f_tenure")
    sel_calltype = st.multiselect("Call Type",        options=calltype_opts, default=[], key="f_calltype")
    sel_cohort   = st.multiselect("Membership",       options=cohort_opts,   default=[], key="f_cohort")

# ── Apply filters ──────────────────────────────────────────────────────────────
def apply_filters(base):
    d = base.copy()
    if len(date_range) == 2:
        d = d[(d["call_date_est"].dt.date >= date_range[0]) & (d["call_date_est"].dt.date <= date_range[1])]
    if sel_center   and "center_location"  in d.columns: d = d[d["center_location"].isin(sel_center)]
    if sel_mkt      and "marketing_bucket" in d.columns: d = d[d["marketing_bucket"].isin(sel_mkt)]
    if sel_serp     and "site_serp"        in d.columns: d = d[d["site_serp"].isin(sel_serp)]
    if sel_mov      and "moverSwitcher"    in d.columns: d = d[d["moverSwitcher"].isin(sel_mov)]
    if sel_tenure   and "tenure_bucket"    in d.columns: d = d[d["tenure_bucket"].isin(sel_tenure)]
    if sel_calltype and "call_type"        in d.columns: d = d[d["call_type"].isin(sel_calltype)]
    if sel_cohort   and "membership"       in d.columns: d = d[d["membership"].isin(sel_cohort)]
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
    ib = d[d["ib_contact_calls"] >= 0] if "ib_contact_calls" in d.columns else d
    n_calls       = len(d)
    n_ib          = int(d["ib_contact_calls"].sum()) if "ib_contact_calls" in d.columns else n_calls
    n_contact     = int(d["ib_contact_calls"].sum()) if "ib_contact_calls" in d.columns else 0
    n_credit      = int(d["credit_calls_flag"].sum()) if "credit_calls_flag" in d.columns else 0
    n_pass_credit = int(d["passed_credit_call_flag"].sum()) if "passed_credit_call_flag" in d.columns else 0
    n_fail_credit = int(d["failed_credit_call_flag"].sum()) if "failed_credit_call_flag" in d.columns else 0
    n_pass_sale   = int(d["passed_credit_sale_flag"].sum()) if "passed_credit_sale_flag" in d.columns else 0
    n_fail_sale   = int(d["failed_credit_sale_flag"].sum()) if "failed_credit_sale_flag" in d.columns else 0
    n_orders      = int(d["orders"].sum()) if "orders" in d.columns else 0
    n_tpsales     = int(d["tpsales_flag"].sum()) if "tpsales_flag" in d.columns else 0
    total_gcv     = d["gcv_fo"].sum() if "gcv_fo" in d.columns else 0.0
    total_rev     = d["total_revenue"].sum() if "total_revenue" in d.columns else total_gcv
    tt_avg        = d["talk_time_minutes"].mean() if "talk_time_minutes" in d.columns else float("nan")
    tt_sold       = d[d["orders"] > 0]["talk_time_minutes"].mean() if ("talk_time_minutes" in d.columns and "orders" in d.columns) else float("nan")
    tt_unsold     = d[d["orders"] == 0]["talk_time_minutes"].mean() if ("talk_time_minutes" in d.columns and "orders" in d.columns) else float("nan")

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
st.caption(f"{date_str}  ·  {len(df):,} calls in view")

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_overview, tab_trends, tab_cohort, tab_agent = st.tabs([
    "Overview", "Trends Over Time", "Arcadia vs Atom", "Agent Level"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
with tab_overview:

    kpis = compute_kpis(df)

    # ── Week-over-week KPI metrics ─────────────────────────────────────────────
    st.subheader("Key Metrics")
    st.caption("Current filtered period · delta vs prior ISO week (ignores date filter for comparison)")

    def _wk(fn): return week_kpi(apply_filters(df_raw.copy()), fn)

    m1, m2, m3, m4, m5, m6 = st.columns(6)

    cv, pv = _wk(lambda d: len(d))
    m1.metric("Calls", f"{kpis['n_calls']:,}", delta=f"{cv - pv:+,} vs prior wk" if cv and pv else None)

    cv, pv = _wk(lambda d: safe_rate(d["orders"].sum(), len(d)) if "orders" in d.columns else float("nan"))
    m2.metric("Net Conversion", f"{kpis['net_conversion']:.1%}", delta=delta_str_pct(cv, pv))

    cv, pv = _wk(lambda d: d["total_revenue"].sum() if "total_revenue" in d.columns else d["gcv_fo"].sum() if "gcv_fo" in d.columns else 0)
    m3.metric("Total Revenue", f"${kpis['total_revenue']:,.0f}", delta=delta_str_dollar(cv, pv))

    cv, pv = _wk(lambda d: safe_rate((d["total_revenue"].sum() if "total_revenue" in d.columns else 0), len(d)))
    m4.metric("Rev / Call", f"${kpis['rev_per_call']:,.2f}", delta=delta_str_dollar(cv, pv))

    cv, pv = _wk(lambda d: safe_rate(d["tpsales_flag"].sum() if "tpsales_flag" in d.columns else 0, d["orders"].sum() if "orders" in d.columns else 0))
    m5.metric("Top Product Mix", f"{kpis['top_product_mix']:.1%}", delta=delta_str_pct(cv, pv))

    cv, pv = _wk(lambda d: d["talk_time_minutes"].mean() if "talk_time_minutes" in d.columns else float("nan"))
    m6.metric("Avg Talk Time", f"{kpis['talk_time']:.1f} min", delta=f"{cv - pv:+.2f} min vs prior wk" if cv and pv else None)

    st.divider()

    # ── Credit funnel ──────────────────────────────────────────────────────────
    st.subheader("Credit Funnel")

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Contact Rate",          f"{kpis['contact_rate']:.1%}")
    c2.metric("Credit Rate",           f"{kpis['credit_rate']:.1%}")
    c3.metric("Passed Credit Rate",    f"{kpis['pass_credit_rate']:.1%}")
    c4.metric("Failed Credit Rate",    f"{kpis['fail_credit_rate']:.1%}")
    c5.metric("Passed Credit Conv.",   f"{kpis['pass_credit_conv']:.1%}")
    c6.metric("Failed Credit Conv.",   f"{kpis['fail_credit_conv']:.1%}")

    st.divider()

    # ── KPI summary table ──────────────────────────────────────────────────────
    st.subheader("Summary by Center")

    if "center_location" in df.columns:
        rows = []
        for center, grp in df.groupby("center_location"):
            k = compute_kpis(grp)
            rows.append({
                "Center":             center,
                "Calls":              f"{k['n_calls']:,}",
                "Net Conv.":          f"{k['net_conversion']:.1%}",
                "Top Product Mix":    f"{k['top_product_mix']:.1%}",
                "Total Revenue":      f"${k['total_revenue']:,.0f}",
                "Rev / Call":         f"${k['rev_per_call']:,.2f}",
                "Rev / Order":        f"${k['rev_per_order']:,.2f}",
                "Contact Rate":       f"{k['contact_rate']:.1%}",
                "Credit Rate":        f"{k['credit_rate']:.1%}",
                "Pass Credit Rate":   f"{k['pass_credit_rate']:.1%}",
                "Pass Credit Conv.":  f"{k['pass_credit_conv']:.1%}",
                "Fail Credit Conv.":  f"{k['fail_credit_conv']:.1%}",
                "Avg Talk Time":      f"{k['talk_time']:.1f}",
                "Talk Time (Sold)":   f"{k['talk_time_sold']:.1f}",
                "Talk Time (Unsold)": f"{k['talk_time_unsold']:.1f}",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("center_location column not found.")

    st.divider()

    # ── Talk time breakdown bar ────────────────────────────────────────────────
    st.subheader("Talk Time — Sold vs Unsold")

    if "talk_time_minutes" in df.columns and "orders" in df.columns and "center_location" in df.columns:
        tt_rows = []
        for center, grp in df.groupby("center_location"):
            tt_rows.append({
                "center": center,
                "Sold":   grp[grp["orders"] > 0]["talk_time_minutes"].mean(),
                "Unsold": grp[grp["orders"] == 0]["talk_time_minutes"].mean(),
                "All":    grp["talk_time_minutes"].mean(),
            })
        tt_df = pd.DataFrame(tt_rows)

        fig_tt = go.Figure()
        for label, color in [("All", "#3d8ef8"), ("Sold", "#22c55e"), ("Unsold", "#f43f5e")]:
            fig_tt.add_trace(go.Bar(
                name=label, x=tt_df["center"], y=tt_df[label],
                marker_color=color, marker_line_width=0,
                text=tt_df[label].round(1).astype(str) + " min",
                textposition="outside", textfont=dict(color="#8b95aa", size=11),
            ))
        apply_dark_theme(fig_tt,
            barmode="group", yaxis_title="Minutes", height=300,
            margin=dict(l=40, r=20, t=10, b=40),
            legend=dict(orientation="h", y=-0.25),
        )
        st.plotly_chart(fig_tt, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — TRENDS OVER TIME
# ══════════════════════════════════════════════════════════════════════════════
with tab_trends:

    granularity = st.radio(
        "Granularity", PERIOD_OPTIONS, index=0, horizontal=True, key="trend_gran"
    )

    metric_choice = st.selectbox(
        "Primary Metric",
        ["Net Conversion", "Total Revenue", "Rev / Call", "Rev / Order",
         "Top Product Mix", "Contact Rate", "Credit Rate",
         "Passed Credit Rate", "Passed Credit Conv.", "Failed Credit Conv.",
         "Talk Time", "Calls"],
        key="trend_metric",
    )

    METRIC_MAP = {
        "Net Conversion":      ("orders", "n_calls",  "pct"),
        "Total Revenue":       ("total_revenue", None, "dollar"),
        "Rev / Call":          ("total_revenue", "n_calls", "dollar"),
        "Rev / Order":         ("total_revenue", "n_orders", "dollar"),
        "Top Product Mix":     ("tpsales_flag", "orders", "pct"),
        "Contact Rate":        ("ib_contact_calls", "n_calls", "pct"),
        "Credit Rate":         ("credit_calls_flag", "n_calls", "pct"),
        "Passed Credit Rate":  ("passed_credit_call_flag", "credit_calls_flag", "pct"),
        "Passed Credit Conv.": ("passed_credit_sale_flag", "passed_credit_call_flag", "pct"),
        "Failed Credit Conv.": ("failed_credit_sale_flag", "failed_credit_call_flag", "pct"),
        "Talk Time":           ("talk_time_minutes", None, "decimal"),
        "Calls":               (None, None, "count"),
    }

    if "call_date_est" in df.columns and len(df) > 0:
        ts_df = df.dropna(subset=["call_date_est"]).copy()
        ts_df["period"] = period_labels(ts_df["call_date_est"], granularity)

        num_col, denom_col, fmt = METRIC_MAP[metric_choice]

        def agg_metric(grp):
            if metric_choice == "Calls":
                return len(grp)
            elif metric_choice == "Talk Time":
                return grp["talk_time_minutes"].mean() if "talk_time_minutes" in grp.columns else float("nan")
            elif metric_choice == "Total Revenue":
                return grp["total_revenue"].sum() if "total_revenue" in grp.columns else grp["gcv_fo"].sum()
            elif fmt == "dollar" and denom_col:
                num = grp["total_revenue"].sum() if "total_revenue" in grp.columns else grp.get("gcv_fo", pd.Series([0])).sum()
                if denom_col == "n_calls":     denom = len(grp)
                elif denom_col == "n_orders":  denom = grp["orders"].sum() if "orders" in grp.columns else 0
                else:                          denom = 0
                return safe_rate(num, denom)
            elif fmt == "pct":
                if num_col in grp.columns:
                    num = grp[num_col].sum()
                else:
                    return float("nan")
                if denom_col == "n_calls":   denom = len(grp)
                elif denom_col and denom_col in grp.columns: denom = grp[denom_col].sum()
                else: return float("nan")
                return safe_rate(num, denom)
            return float("nan")

        # Overall trend
        ts_overall = (
            ts_df.groupby("period")
            .apply(agg_metric)
            .reset_index()
            .rename(columns={0: "value"})
            .sort_values("period")
        )
        ts_overall["period_display"] = period_display(ts_overall["period"], granularity)

        fig_trend = go.Figure()

        # Split by center if available
        if "center_location" in ts_df.columns:
            for center, grp_c in ts_df.groupby("center_location"):
                ts_c = (
                    grp_c.groupby("period")
                    .apply(agg_metric)
                    .reset_index()
                    .rename(columns={0: "value"})
                    .sort_values("period")
                )
                ts_c["period_display"] = period_display(ts_c["period"], granularity)
                fig_trend.add_trace(go.Scatter(
                    x=ts_c["period_display"], y=ts_c["value"],
                    name=center, mode="lines+markers",
                    line=dict(width=2), marker=dict(size=5),
                ))

        fig_trend.add_trace(go.Scatter(
            x=ts_overall["period_display"], y=ts_overall["value"],
            name="Overall", mode="lines+markers",
            line=dict(width=2, dash="dot", color="#8b95aa"),
            marker=dict(size=5, color="#8b95aa"),
        ))

        is_pct    = fmt == "pct"
        is_dollar = fmt == "dollar"
        apply_dark_theme(fig_trend,
            yaxis_tickformat=".1%" if is_pct else ("$,.0f" if is_dollar else ".2f"),
            yaxis_tickprefix="$" if is_dollar else "",
            height=380,
            margin=dict(l=50, r=20, t=10, b=40),
            legend=dict(orientation="h", y=-0.2),
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("No data available for trend chart.")

    st.divider()

    # ── Revenue & Volume dual axis ─────────────────────────────────────────────
    st.subheader("Revenue & Call Volume")

    if "call_date_est" in df.columns and "total_revenue" in df.columns:
        rv_df = df.dropna(subset=["call_date_est"]).copy()
        rv_df["period"] = period_labels(rv_df["call_date_est"], granularity)

        rv_ts = (
            rv_df.groupby("period")
            .agg(revenue=("total_revenue", "sum"), calls=("call_id", "count"))
            .reset_index()
            .sort_values("period")
        )
        rv_ts["period_display"] = period_display(rv_ts["period"], granularity)

        fig_rv = go.Figure()
        fig_rv.add_trace(go.Bar(
            x=rv_ts["period_display"], y=rv_ts["revenue"],
            name="Revenue", marker_color="rgba(61,142,248,0.5)",
            marker_line_width=0, yaxis="y",
        ))
        fig_rv.add_trace(go.Scatter(
            x=rv_ts["period_display"], y=rv_ts["calls"],
            name="Calls", mode="lines+markers",
            line=dict(color="#22d3c8", width=2),
            marker=dict(size=5), yaxis="y2",
        ))
        apply_dark_theme(fig_rv,
            yaxis=dict(title="Revenue ($)", tickprefix="$", gridcolor="#1e2330", linecolor="#252b3a", tickcolor="#252b3a", zerolinecolor="#252b3a"),
            yaxis2=dict(title="Calls", overlaying="y", side="right", gridcolor="rgba(0,0,0,0)", linecolor="#252b3a", tickcolor="#252b3a"),
            barmode="overlay",
            height=340,
            margin=dict(l=60, r=60, t=10, b=40),
            legend=dict(orientation="h", y=-0.2),
        )
        st.plotly_chart(fig_rv, use_container_width=True)

    st.divider()

    # ── Marketing bucket breakdown ─────────────────────────────────────────────
    st.subheader("Conversion by Marketing Bucket Over Time")

    if "marketing_bucket" in df.columns and "call_date_est" in df.columns:
        mb_df = df.dropna(subset=["call_date_est", "marketing_bucket"]).copy()
        mb_df["period"] = period_labels(mb_df["call_date_est"], granularity)

        mb_ts = (
            mb_df.groupby(["period", "marketing_bucket"])
            .apply(lambda g: safe_rate(g["orders"].sum() if "orders" in g.columns else 0, len(g)))
            .reset_index()
            .rename(columns={0: "conv"})
            .sort_values("period")
        )
        mb_ts["period_display"] = period_display(mb_ts["period"], granularity)

        top_buckets = mb_df["marketing_bucket"].value_counts().head(6).index.tolist()
        mb_ts = mb_ts[mb_ts["marketing_bucket"].isin(top_buckets)]

        fig_mb = go.Figure()
        for bucket in top_buckets:
            sub = mb_ts[mb_ts["marketing_bucket"] == bucket]
            fig_mb.add_trace(go.Scatter(
                x=sub["period_display"], y=sub["conv"],
                name=bucket, mode="lines+markers",
                line=dict(width=2), marker=dict(size=5),
            ))
        apply_dark_theme(fig_mb,
            yaxis_tickformat=".1%",
            height=320,
            margin=dict(l=50, r=20, t=10, b=40),
            legend=dict(orientation="h", y=-0.25),
        )
        st.plotly_chart(fig_mb, use_container_width=True)
        st.caption("Top 6 marketing buckets by call volume · Net Conversion rate over time")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — ARCADIA VS ATOM
# ══════════════════════════════════════════════════════════════════════════════
with tab_cohort:

    if "membership" not in df.columns:
        st.info("membership column not found in data.")
    else:
        arcadia_df = df[df["membership"] == "Arcadia"]
        atom_df    = df[df["membership"] == "Atomizer"]

        arc_kpis  = compute_kpis(arcadia_df)
        atom_kpis = compute_kpis(atom_df)

        def pct_delta(a, b):
            if pd.isna(a) or pd.isna(b) or b == 0: return None
            return f"{(a / b - 1) * 100:+.1f}% vs Atom"

        st.subheader("Arcadia vs Atom — Current Period")

        KPI_SPECS = [
            ("Calls",             "n_calls",        "count"),
            ("Net Conversion",    "net_conversion",  "pct"),
            ("Top Product Mix",   "top_product_mix", "pct"),
            ("Total Revenue",     "total_revenue",   "dollar"),
            ("Rev / Call",        "rev_per_call",    "dollar"),
            ("Rev / Order",       "rev_per_order",   "dollar"),
            ("Contact Rate",      "contact_rate",    "pct"),
            ("Credit Rate",       "credit_rate",     "pct"),
            ("Pass Credit Rate",  "pass_credit_rate","pct"),
            ("Pass Credit Conv.", "pass_credit_conv","pct"),
            ("Fail Credit Conv.", "fail_credit_conv","pct"),
            ("Talk Time",         "talk_time",       "decimal"),
        ]

        # Row 1: core KPIs
        cols = st.columns(4)
        for i, (label, key, fmt) in enumerate(KPI_SPECS[:4]):
            a_val = arc_kpis[key]
            b_val = atom_kpis[key]
            if fmt == "count":
                a_str = f"{a_val:,}"
            elif fmt == "pct":
                a_str = f"{a_val:.1%}"
            elif fmt == "dollar":
                a_str = f"${a_val:,.2f}"
            else:
                a_str = f"{a_val:.2f}"
            cols[i % 4].metric(f"Arcadia — {label}", a_str, delta=pct_delta(a_val, b_val))

        cols2 = st.columns(4)
        for i, (label, key, fmt) in enumerate(KPI_SPECS[4:8]):
            a_val = arc_kpis[key]
            b_val = atom_kpis[key]
            if fmt == "pct":    a_str = f"{a_val:.1%}"
            elif fmt == "dollar": a_str = f"${a_val:,.2f}"
            else: a_str = f"{a_val:.2f}"
            cols2[i % 4].metric(f"Arcadia — {label}", a_str, delta=pct_delta(a_val, b_val))

        st.divider()

        # ── Side-by-side comparison bar chart ─────────────────────────────────
        st.subheader("Head-to-Head Comparison")

        cmp_metric = st.selectbox(
            "Metric",
            ["Net Conversion", "Top Product Mix", "Rev / Call", "Rev / Order",
             "Contact Rate", "Credit Rate", "Passed Credit Rate",
             "Passed Credit Conv.", "Talk Time"],
            key="cohort_cmp_metric",
        )

        METRIC_KEY_MAP = {
            "Net Conversion":      ("net_conversion",  "pct"),
            "Top Product Mix":     ("top_product_mix", "pct"),
            "Rev / Call":          ("rev_per_call",    "dollar"),
            "Rev / Order":         ("rev_per_order",   "dollar"),
            "Contact Rate":        ("contact_rate",    "pct"),
            "Credit Rate":         ("credit_rate",     "pct"),
            "Passed Credit Rate":  ("pass_credit_rate","pct"),
            "Passed Credit Conv.": ("pass_credit_conv","pct"),
            "Talk Time":           ("talk_time",       "decimal"),
        }
        mk, mfmt = METRIC_KEY_MAP[cmp_metric]

        granularity_c = st.radio("Granularity", PERIOD_OPTIONS, index=0, horizontal=True, key="cohort_gran")

        if "call_date_est" in df.columns:
            coh_fig = go.Figure()
            for cohort_label, cohort_data, color in [
                ("Arcadia", arcadia_df, "#3d8ef8"),
                ("Atom",    atom_df,    "#22d3c8"),
            ]:
                tmp = cohort_data.dropna(subset=["call_date_est"]).copy()
                if tmp.empty:
                    continue
                tmp["period"] = period_labels(tmp["call_date_est"], granularity_c)

                def _agg_cohort(grp):
                    k = compute_kpis(grp)
                    return k[mk]

                ts_c = (
                    tmp.groupby("period")
                    .apply(_agg_cohort)
                    .reset_index()
                    .rename(columns={0: "value"})
                    .sort_values("period")
                )
                ts_c["period_display"] = period_display(ts_c["period"], granularity_c)
                coh_fig.add_trace(go.Scatter(
                    x=ts_c["period_display"], y=ts_c["value"],
                    name=cohort_label, mode="lines+markers",
                    line=dict(color=color, width=2), marker=dict(size=5, color=color),
                ))

            apply_dark_theme(coh_fig,
                yaxis_tickformat=".1%" if mfmt == "pct" else ("$,.2f" if mfmt == "dollar" else ".2f"),
                yaxis_tickprefix="$" if mfmt == "dollar" else "",
                height=340,
                margin=dict(l=50, r=20, t=10, b=40),
                legend=dict(orientation="h", y=-0.2),
            )
            st.plotly_chart(coh_fig, use_container_width=True)

        st.divider()

        # ── Full KPI comparison table ──────────────────────────────────────────
        st.subheader("Full KPI Table — Arcadia vs Atom")

        def fmt_kpi(val, fmt):
            if pd.isna(val): return "—"
            if fmt == "count":  return f"{val:,}"
            if fmt == "pct":    return f"{val:.1%}"
            if fmt == "dollar": return f"${val:,.2f}"
            return f"{val:.2f}"

        def delta_kpi(a, b, fmt):
            if pd.isna(a) or pd.isna(b) or b == 0: return "—"
            pct = (a / b - 1) * 100
            return f"{pct:+.1f}%"

        cmp_rows = []
        for label, key, fmt in KPI_SPECS:
            a_v = arc_kpis[key]
            b_v = atom_kpis[key]
            cmp_rows.append({
                "KPI":     label,
                "Arcadia": fmt_kpi(a_v, fmt),
                "Atom":    fmt_kpi(b_v, fmt),
                "Delta (Arcadia vs Atom)": delta_kpi(a_v, b_v, fmt),
            })

        cmp_df = pd.DataFrame(cmp_rows)

        def color_delta(val):
            if val == "—": return ""
            try:
                num = float(val.replace("%", "").replace("+", ""))
            except Exception:
                return ""
            if abs(num) < 2:   return "background-color: #2a2a1a; color: #c8a000"
            if num > 0:        return "background-color: #0f2a1a; color: #22c55e"
            return "background-color: #2a1018; color: #f43f5e"

        styler = cmp_df.style.map(color_delta, subset=["Delta (Arcadia vs Atom)"])
        st.dataframe(styler, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — AGENT LEVEL
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
                "Sort by",
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
            n = len(g)
            n_orders  = g["orders"].sum() if "orders" in g.columns else 0
            n_tpsales = g["tpsales_flag"].sum() if "tpsales_flag" in g.columns else 0
            rev       = g["total_revenue"].sum() if "total_revenue" in g.columns else g["gcv_fo"].sum() if "gcv_fo" in g.columns else 0
            tt_all    = g["talk_time_minutes"].mean() if "talk_time_minutes" in g.columns else float("nan")
            tt_sold   = g[g["orders"] > 0]["talk_time_minutes"].mean() if "talk_time_minutes" in g.columns else float("nan")
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

        with dc1:
            st.markdown("**Net Conversion Distribution**")
            fig_nc = go.Figure(go.Histogram(
                x=agent_df["Net Conv."].dropna() * 100, nbinsx=20,
                marker_color="#3d8ef8", opacity=0.8,
                marker_line_color="#252b3a", marker_line_width=1,
            ))
            apply_dark_theme(fig_nc,
                xaxis_title="Net Conversion (%)",
                yaxis_title="Agents",
                height=240, margin=dict(l=40, r=20, t=10, b=40),
            )
            st.plotly_chart(fig_nc, use_container_width=True)

        with dc2:
            st.markdown("**Rev / Call Distribution**")
            fig_rc = go.Figure(go.Histogram(
                x=agent_df["Rev / Call"].dropna(), nbinsx=20,
                marker_color="#22d3c8", opacity=0.8,
                marker_line_color="#252b3a", marker_line_width=1,
            ))
            apply_dark_theme(fig_rc,
                xaxis_title="Revenue per Call ($)",
                yaxis_title="Agents",
                height=240, margin=dict(l=40, r=20, t=10, b=40),
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

        st.dataframe(fmt_df, use_container_width=True, hide_index=True)