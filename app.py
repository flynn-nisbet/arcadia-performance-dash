import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import json
import re
import hashlib
from datetime import timedelta, date
from pathlib import Path
import traceback
import streamlit as st

def report_through_date(source: pd.DataFrame | None = None) -> date:
    """Latest report date available, including current-day/intra-day rows."""
    if source is not None and "call_date_est" in source.columns and source["call_date_est"].notna().any():
        return source["call_date_est"].max().date()
    return date.today()


def monday_of_week_containing(d: date) -> date:
    """Monday-start calendar week containing ``d`` (``d.weekday()``: Mon=0 … Sun=6)."""
    return d - timedelta(days=d.weekday())


st.set_page_config(
    page_title="Arcadia Performance Dash",
    page_icon="⚡",
    layout="wide",
)

import theme

theme.init_browser_query_state()

from charts import (
    PLOT_COLORWAY,
    apply_chart_theme,
    chart_hist_stroke_and_title,
    chart_hline_reference,
    chart_muted,
    chart_text_primary,
    colorway_cycled,
    funnel_metric_bar_hover_and_ticks,
    layout_chart_title,
    lift_chart_title,
    overview_chart_title,
    plotly_axis_extra,
    plotly_axis_lines,
    volume_comparison_bars_layout,
)


def dataframe_display_height(n_rows: int, min_rows: int = 4, row_px: int = 36, header_px: int = 52, cap: int = 2200) -> int:
    try:
        n = max(min_rows, int(n_rows))
    except (TypeError, ValueError):
        n = min_rows
    return int(min(cap, header_px + row_px * n))


def streamlit_version_at_least(major: int, minor: int) -> bool:
    parts = []
    for part in str(getattr(st, "__version__", "0.0")).split(".")[:2]:
        try:
            parts.append(int(re.match(r"\d+", part).group(0)))
        except (AttributeError, ValueError):
            parts.append(0)
    while len(parts) < 2:
        parts.append(0)
    return tuple(parts) >= (major, minor)


def stretch_width_kwargs() -> dict:
    if streamlit_version_at_least(1, 57):
        return {"width": "stretch"}
    return {"use_container_width": True}


def render_copy_html(html: str, height: int) -> None:
    if streamlit_version_at_least(1, 57) and hasattr(st, "iframe"):
        st.iframe(html, height=height, **stretch_width_kwargs())
    else:
        import streamlit.components.v1 as components
        components.html(html, height=height)


def table_export_row(
    display_df: pd.DataFrame,
    download_filename: str,
    copy_label: str = "Copy",
    *,
    key_suffix: str = "",
) -> None:
    """Renders a compact copy action below a table."""
    tsv = display_df.to_csv(index=False, sep="\t")
    uid = hashlib.md5((download_filename + "\0" + key_suffix).encode(), usedforsecurity=False).hexdigest()[:12]
    copy_bg = "#f8fafc" if theme.is_light_theme() else "#181c25"
    copy_text = "#475569" if theme.is_light_theme() else "#8b95aa"
    copy_border = "#cbd5e1" if theme.is_light_theme() else "#2e3649"
    copy_col, _spacer = st.columns([0.65, 6.35])
    with copy_col:
        tsv_literal = json.dumps(tsv)
        lbl_literal = json.dumps(copy_label)
        render_copy_html(
            f"""<div style="font-family:DM Sans,sans-serif;padding:0;margin:0;">
<button type="button" id="cpbtn_{uid}"
style="background:{copy_bg};color:{copy_text};border:1px solid {copy_border};border-radius:999px;box-sizing:border-box;
width:100%;min-height:2.25rem;height:2.25rem;padding:0 0.85rem;font-size:0.78rem;font-weight:500;
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

# ── Load data ──────────────────────────────────────────────────────────────────
TEST_CENTER_LOCATIONS = {"unknown"}
DATA_DIR = Path("data")
SOLD_PROVIDER_COLUMN = "sold_provider"
SOLD_PROVIDER_MISSING_VALUES = {"", "(missing)", "missing", "nan", "none", "null", "<na>"}
SOLD_PROVIDER_COL_CANDIDATES = (
    "partner_name",
    SOLD_PROVIDER_COLUMN,
    "provider_name",
    "provider",
    "supplier_name",
    "supplier",
    "retailer_name",
    "brand_name",
    "utility_name",
)


def remove_test_center_locations(df: pd.DataFrame) -> pd.DataFrame:
    if "center_location" not in df.columns:
        return df
    center = df["center_location"].astype(str).str.strip().str.lower()
    return df.loc[~center.isin(TEST_CENTER_LOCATIONS)].copy()


def normalize_sold_provider_column(df: pd.DataFrame) -> pd.DataFrame:
    provider_col = next((c for c in SOLD_PROVIDER_COL_CANDIDATES if c in df.columns), None)
    if provider_col is None:
        df[SOLD_PROVIDER_COLUMN] = pd.NA
    elif provider_col != SOLD_PROVIDER_COLUMN:
        df[SOLD_PROVIDER_COLUMN] = df[provider_col]

    provider = df[SOLD_PROVIDER_COLUMN].astype("string").str.strip()
    provider_key = provider.str.lower()
    df[SOLD_PROVIDER_COLUMN] = provider.mask(provider.isna() | provider_key.isin(SOLD_PROVIDER_MISSING_VALUES))
    return df


def natural_path_sort_key(path: Path):
    return [
        int(part) if part.isdigit() else part
        for part in re.split(r"(\d+)", path.as_posix().lower())
    ]


def discover_agent_call_files(data_dir: Path = DATA_DIR) -> list[Path]:
    """Find agent-call CSV exports in old monthly files or new partitioned layouts."""
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    files = []
    for path in data_dir.rglob("*.csv"):
        rel_parts = path.relative_to(data_dir).parts
        rel_parts_lc = [p.lower() for p in rel_parts]
        filename_lc = path.name.lower()
        in_agent_calls_dir = any(p.startswith("agent_calls") for p in rel_parts_lc[:-1])
        is_agent_calls_file = filename_lc.startswith("agent_calls")
        if is_agent_calls_file or in_agent_calls_dir:
            files.append(path)

    return sorted(set(files), key=natural_path_sort_key)


def agent_call_file_manifest(files: list[Path]):
    return tuple(
        (
            path.as_posix(),
            path.stat().st_size,
            path.stat().st_mtime_ns,
        )
        for path in files
    )


@st.cache_data(ttl="24h")
def load_data(file_manifest):
    files = [Path(path) for path, _, _ in file_manifest]

    dfs = [pd.read_csv(path, low_memory=False) for path in files]

    df = pd.concat(dfs, ignore_index=True)
    df = remove_test_center_locations(df)
    df = normalize_sold_provider_column(df)
    df["call_date_est"] = pd.to_datetime(df["call_date_est"])
    if "call_time_est" in df.columns:
        df["call_time_est"] = pd.to_datetime(df["call_time_est"], errors="coerce")
    if "brand_test" in df.columns:
        df["brand_test"] = df["brand_test"].astype("string").str.strip().str.lower()
    if "call_type" in df.columns:
        df["call_type"] = df["call_type"].replace({"Permalease": "SERP", "Site Session": "Site"})
    return df


def load_agent_call_data():
    files = discover_agent_call_files()

    if not files:
        raise FileNotFoundError(
            "No agent-call CSV files found in data/. Expected root files like "
            "agent_calls_part1.csv or CSV parts inside data/agent_calls*/."
        )

    return load_data(agent_call_file_manifest(files))

try:
    df_raw = load_agent_call_data()
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()

PERIOD_OPTIONS = ["Daily", "Weekly", "Monthly"]
PERIOD_CODE    = {"Daily": "D", "Weekly": "W", "Monthly": "M"}
PERIOD_FMT     = {"Daily": "%b %d", "Weekly": "%b %d", "Monthly": "%b %Y"}

# ── Sidebar Filters ────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("Filters")

    min_d = df_raw["call_date_est"].min().date()
    max_d = df_raw["call_date_est"].max().date()
    if max_d < min_d:
        max_d = min_d
    default_start = max(min_d, max_d - timedelta(days=6))

    date_range = st.date_input(
        "Date Range",
        value=(default_start, max_d),
        min_value=min_d,
        max_value=max_d,
        key="filter_date",
    )

    center_opts   = sorted(df_raw["center_location"].dropna().unique().tolist()) if "center_location" in df_raw.columns else []
    center_opts   = [c for c in center_opts if c != "Z - Default Location"]
    default_centers = [c for c in ("Durban", "Jamaica") if c in center_opts]
    if "_default_center_selection_applied" not in st.session_state:
        st.session_state["f_center"] = default_centers
        st.session_state["_default_center_selection_applied"] = True
    mkt_opts      = sorted(df_raw["marketing_bucket"].dropna().unique().tolist()) if "marketing_bucket" in df_raw.columns else []
    mov_opts      = sorted(df_raw["moverSwitcher"].dropna().unique().tolist()) if "moverSwitcher" in df_raw.columns else []
    tenure_opts   = sorted(df_raw["tenure_bucket"].dropna().unique().tolist()) if "tenure_bucket" in df_raw.columns else []
    calltype_opts = sorted(df_raw["call_type"].dropna().unique().tolist()) if "call_type" in df_raw.columns else []
    if SOLD_PROVIDER_COLUMN in df_raw.columns:
        sold_provider_opts = sorted(
            p for p in df_raw[SOLD_PROVIDER_COLUMN].dropna().unique().tolist()
            if str(p).strip().lower() not in SOLD_PROVIDER_MISSING_VALUES
        )
    else:
        sold_provider_opts = []

    time_granularity   = st.selectbox("Time Granularity", PERIOD_OPTIONS, index=0, key="time_granularity")
    sel_center         = st.multiselect("Center",           options=center_opts,         key="f_center")
    sel_brand_nonbrand = st.multiselect("Brand / Non-Brand", options=["Brand", "Non-Brand"], default=[], key="f_brand_nonbrand")
    sel_mkt            = st.multiselect("Marketing Bucket", options=mkt_opts,            default=[], key="f_mkt")
    sel_mov            = st.multiselect("Mover / Switcher", options=mov_opts,            default=[], key="f_mov")
    sel_tenure         = st.multiselect("Tenure Bucket",    options=tenure_opts,         default=[], key="f_tenure")
    sel_calltype       = st.multiselect("Site/SERP",        options=calltype_opts,       default=[], key="f_calltype")
    sel_sold_provider  = st.multiselect(
        "Sold Partner",
        options=sold_provider_opts,
        default=[],
        key="f_sold_provider",
        help=(
            "Applying this filter limits the dashboard to sold calls for the selected partner(s). "
            "It is mainly useful for RPO and will not be useful for pre-sale analyses."
        ),
    )

    st.divider()
    _arcadia_theme_choice = theme.render_app_theme_toggle()

theme.inject_app_styles(light=_arcadia_theme_choice == "Light")

# Brand bucket names — both spellings seen in production data
BRAND_BUCKETS = {"Brand Partner", "Brand-Partner", "Competitor", "NRG"}
BRAND_TEST_LAUNCH_AT = pd.Timestamp("2026-05-27 09:00:00")
BRAND_TEST_VALUES = ("control", "test")
BRAND_TEST_DISPLAY = {"control": "Control", "test": "Test"}
BRAND_TEST_COL = "_brand_test_group"
BRAND_TEST_DT_COL = "_brand_test_dt"
ECP_MODULE_SELECTION_COL = "ecp_module_selection"
ECP_MODULE_SELECTION_CLEAN_COL = "_ecp_module_selection_clean"
ECP_MODULE_SELECTION_MISSING_VALUES = {"", "nan", "none", "null", "<na>"}
ECP_MODULE_SELECTION_DISPLAY = {
    "clicked_ecp": "Clicked ECP",
    "clicked_mover_or_switcher": "Clicked Mover / Switcher",
}

FMP_LAUNCH_AT = pd.Timestamp("2026-05-20 11:00:00")
FMP_HINT_COL_CANDIDATES = ("site_experience_hint", "siteExperienceHint")
FMP_HINT_PREFIX = "Find My Plan"
FMP_DT_COL = "_fmp_dt"
FMP_REC_TEXT_COL = "_fmp_recommended_text"
FMP_REC_PROVIDER_COL = "_fmp_recommended_provider"
FMP_REC_PLAN_COL = "_fmp_recommended_plan"
FMP_RECOMMENDED_PROVIDER_PREFIXES = (
    "Frontier Utilities",
    "Discount Power",
    "Rhythm Energy",
    "Express Energy",
    "4Change Energy",
    "Gexa Energy",
    "TXU Energy",
    "Constellation",
    "Reliant",
    "APG&E",
)

# ── Apply filters ──────────────────────────────────────────────────────────────
def apply_filters(base, use_date_range=True):
    d = base.copy()
    # Always filter to Arcadia only outside of the Arcadia vs Atom tab
    if "membership" in d.columns:
        d = d[d["membership"] == "Arcadia"]
    if use_date_range and len(date_range) == 2:
        d = d[(d["call_date_est"].dt.date >= date_range[0]) & (d["call_date_est"].dt.date <= date_range[1])]
    if sel_center and "center_location" in d.columns:
        d = d[d["center_location"].isin(sel_center)]
    if sel_brand_nonbrand and "marketing_bucket" in d.columns:
        implied: set = set()
        if "Brand" in sel_brand_nonbrand:
            implied |= BRAND_BUCKETS & set(mkt_opts)
        if "Non-Brand" in sel_brand_nonbrand:
            implied |= set(mkt_opts) - BRAND_BUCKETS
        d = d[d["marketing_bucket"].isin(implied)]
    if sel_mkt and "marketing_bucket" in d.columns:
        d = d[d["marketing_bucket"].isin(sel_mkt)]
    if sel_sold_provider:
        if SOLD_PROVIDER_COLUMN in d.columns:
            d = d[d[SOLD_PROVIDER_COLUMN].isin(sel_sold_provider)]
        else:
            d = d.iloc[0:0]
    if sel_mov      and "moverSwitcher"    in d.columns: d = d[d["moverSwitcher"].isin(sel_mov)]
    if sel_tenure   and "tenure_bucket"    in d.columns: d = d[d["tenure_bucket"].isin(sel_tenure)]
    if sel_calltype and "call_type"        in d.columns: d = d[d["call_type"].isin(sel_calltype)]
    return d

df = apply_filters(df_raw)

# ── Shared helpers ─────────────────────────────────────────────────────────────
def period_labels(date_series, period):
    code = PERIOD_CODE[period]
    pr = pd.DatetimeIndex(date_series).to_period(code)
    return pd.Series(pr.to_timestamp(how="start"), index=date_series.index)

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


def clean_ecp_module_selection(d: pd.DataFrame) -> pd.Series:
    if ECP_MODULE_SELECTION_COL not in d.columns:
        return pd.Series(pd.NA, index=d.index, dtype="string")
    values = d[ECP_MODULE_SELECTION_COL].astype("string").str.strip()
    missing = (
        values.isna()
        | values.str.lower().isin(ECP_MODULE_SELECTION_MISSING_VALUES)
    )
    return values.mask(missing, pd.NA)


def display_ecp_module_selection(value) -> str:
    if pd.isna(value):
        return "—"
    value_s = str(value).strip()
    return ECP_MODULE_SELECTION_DISPLAY.get(
        value_s,
        re.sub(r"[_-]+", " ", value_s).title(),
    )


def site_experience_hint_column(d: pd.DataFrame) -> str | None:
    return next((c for c in FMP_HINT_COL_CANDIDATES if c in d.columns), None)


def fmp_datetime_series(d: pd.DataFrame) -> tuple[pd.Series, bool]:
    if "call_time_est" in d.columns:
        call_ts = pd.to_datetime(d["call_time_est"], errors="coerce")
        has_time = call_ts.notna().any()
    else:
        call_ts = pd.Series(pd.NaT, index=d.index)
        has_time = False
    if "call_date_est" in d.columns:
        call_ts = call_ts.fillna(pd.to_datetime(d["call_date_est"], errors="coerce"))
    return call_ts, has_time


def normalize_fmp_recommendation_text(hints: pd.Series) -> pd.Series:
    rec = hints.astype("string").str.extract(
        r"(?i)\[?Find My Plan\]?:\s*Customer was recommended\s+(.*?),\s*but did not buy\.?",
        expand=False,
    )
    return rec.astype("string").str.replace(r"\s+", " ", regex=True).str.strip()


def add_fmp_recommendation_columns(d: pd.DataFrame, hint_col: str) -> pd.DataFrame:
    out = d.copy()
    out[FMP_REC_TEXT_COL] = normalize_fmp_recommendation_text(out[hint_col])

    provider_prefixes = {p.strip() for p in FMP_RECOMMENDED_PROVIDER_PREFIXES if p.strip()}
    if SOLD_PROVIDER_COLUMN in out.columns:
        provider_prefixes |= {
            str(p).strip()
            for p in out[SOLD_PROVIDER_COLUMN].dropna().unique().tolist()
            if str(p).strip()
        }
    provider_prefixes = sorted(provider_prefixes, key=len, reverse=True)

    def _split_recommendation(rec):
        if pd.isna(rec):
            return pd.Series({FMP_REC_PROVIDER_COL: pd.NA, FMP_REC_PLAN_COL: pd.NA})
        rec_s = str(rec).strip()
        rec_key = rec_s.casefold()
        for provider in provider_prefixes:
            provider_s = str(provider).strip()
            provider_key = provider_s.casefold()
            if rec_key == provider_key:
                return pd.Series({FMP_REC_PROVIDER_COL: provider_s, FMP_REC_PLAN_COL: ""})
            if rec_key.startswith(f"{provider_key} "):
                return pd.Series({
                    FMP_REC_PROVIDER_COL: provider_s,
                    FMP_REC_PLAN_COL: rec_s[len(provider_s):].strip(),
                })
        return pd.Series({FMP_REC_PROVIDER_COL: pd.NA, FMP_REC_PLAN_COL: rec_s})

    split = out[FMP_REC_TEXT_COL].apply(_split_recommendation)
    out[FMP_REC_PROVIDER_COL] = split[FMP_REC_PROVIDER_COL]
    out[FMP_REC_PLAN_COL] = split[FMP_REC_PLAN_COL]
    return out


def normalize_plan_match_text(values: pd.Series) -> pd.Series:
    return (
        values
        .astype("string")
        .str.replace("\u00a0", " ", regex=False)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
        .str.lower()
    )


def cmp_date_range_sort(pair):
    if pair is None or len(pair) != 2:
        return None
    a, b = pair[0], pair[1]
    return (a, b) if a <= b else (b, a)


def cmp_date_range_clamp(lo, hi, pair, fallback):
    fb = cmp_date_range_sort(fallback)
    if fb is None:
        fb = (lo, min(hi, lo + timedelta(days=6)))
    sp = cmp_date_range_sort(pair)
    if sp is None:
        return fb
    a, b = sp
    a = max(lo, min(hi, a))
    b = max(lo, min(hi, b))
    if a > b:
        return fb
    return (a, b)


def parse_display_pct(val):
    """Parse '+12.3%' / '-4.0%' / '—' from styled tables into a float or None."""
    if val is None or val == "—" or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip().replace("%", "").replace("+", "")
    try:
        return float(s)
    except ValueError:
        return None


def wtd_vs_four_week_pooled(source, metric_fn):
    """Partial Mon–Sun week through the latest available date vs P4WA on one pooled window.

    P4WA is computed on **all calls in the four prior full Mon–Sun weeks** (same calendar span as
    four separate weeks), then the metric function runs once on that combined slice — e.g. Rev/Call
    is total revenue over total calls in those 28 days, not the mean of each week's Rev/Call.
    """
    if "call_date_est" not in source.columns:
        return None, None
    tmp = source.dropna(subset=["call_date_est"]).copy()
    if tmp.empty:
        return None, None
    as_of = report_through_date(tmp)
    week_start = monday_of_week_containing(as_of)

    def _slice(d0: date, d1: date):
        m = (tmp["call_date_est"].dt.date >= d0) & (tmp["call_date_est"].dt.date <= d1)
        return tmp.loc[m]

    cur = metric_fn(_slice(week_start, as_of))
    # Four full Mon–Sun weeks immediately before the current week: Mon (week_start − 28) … Sun (week_start − 1)
    pool_start = week_start - timedelta(days=28)
    pool_end = week_start - timedelta(days=1)
    baseline = metric_fn(_slice(pool_start, pool_end))
    if baseline is not None and isinstance(baseline, float) and pd.isna(baseline):
        baseline = float("nan")
    return cur, baseline

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


# Funnel metrics (shared: Overview funnel table / period comparison + Volume shifts bucket comparison)
FUNNEL_METRICS = [
    ("Calls", "count"),
    ("CiContact", "pct"),
    ("CiCredit", "pct"),
    ("PCR", "pct"),
    ("PCC", "pct"),
    ("FCC", "pct"),
    ("NC", "pct"),
    ("TPM", "pct"),
    ("Revenue", "dollar"),
    ("RPNC", "dollar"),
    ("RPO", "dollar"),
    ("Talk Time", "decimal"),
    ("Sold Talk Time", "decimal"),
    ("Unsold Talk Time", "decimal"),
]
FUNNEL_METRIC_FMT = dict(FUNNEL_METRICS)


def compute_funnel_row(grp, metric):
    inbound = grp[top_funnel_mask(grp)]
    orders_rev_rows = grp[order_revenue_mask(grp)]
    n = top_funnel_call_count(grp)
    n_contact = inbound["ib_contact_calls"].sum() if "ib_contact_calls" in inbound.columns else 0
    n_credit = inbound["credit_calls_flag"].sum() if "credit_calls_flag" in inbound.columns else 0
    n_pass_cr = inbound["passed_credit_call_flag"].sum() if "passed_credit_call_flag" in inbound.columns else 0
    n_fail_cr = inbound["failed_credit_call_flag"].sum() if "failed_credit_call_flag" in inbound.columns else 0
    n_pass_sale = inbound["passed_credit_sale_flag"].sum() if "passed_credit_sale_flag" in inbound.columns else 0
    n_fail_sale = inbound["failed_credit_sale_flag"].sum() if "failed_credit_sale_flag" in inbound.columns else 0
    n_orders = orders_rev_rows["orders"].sum() if "orders" in orders_rev_rows.columns else 0
    n_tpsales = orders_rev_rows["tpsales_flag"].sum() if "tpsales_flag" in orders_rev_rows.columns else 0
    rev = (
        orders_rev_rows["total_revenue"].sum()
        if "total_revenue" in orders_rev_rows.columns
        else orders_rev_rows["gcv_fo"].sum() if "gcv_fo" in orders_rev_rows.columns else 0
    )
    tt_all = inbound["talk_time_minutes"].mean() if "talk_time_minutes" in inbound.columns else float("nan")
    tt_sold = (
        inbound[inbound["orders"] > 0]["talk_time_minutes"].mean()
        if ("talk_time_minutes" in inbound.columns and "orders" in inbound.columns)
        else float("nan")
    )
    tt_unsold = (
        inbound[inbound["orders"] == 0]["talk_time_minutes"].mean()
        if ("talk_time_minutes" in inbound.columns and "orders" in inbound.columns)
        else float("nan")
    )

    val_map = {
        "Calls": n,
        "CiContact": safe_rate(n_contact, n),
        "CiCredit": safe_rate(n_credit, n),
        "PCR": safe_rate(n_pass_cr, n_credit),
        "PCC": safe_rate(n_pass_sale, n_pass_cr),
        "FCC": safe_rate(n_fail_sale, n_fail_cr),
        "NC": safe_rate(n_orders, n),
        "TPM": safe_rate(n_tpsales, n_orders),
        "Revenue": rev,
        "RPNC": safe_rate(rev, n),
        "RPO": safe_rate(rev, n_orders),
        "Talk Time": tt_all,
        "Sold Talk Time": tt_sold,
        "Unsold Talk Time": tt_unsold,
    }
    return val_map.get(metric, float("nan"))


def fmt_funnel(val, fmt):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "—"
    if fmt == "count":
        return f"{int(val):,}"
    if fmt == "pct":
        return f"{val:.1%}"
    if fmt == "dollar":
        return f"${val:,.2f}"
    return f"{val:.2f}"


def pct_change_vs_prior(v1, v2):
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


def fmt_pct_change_str(p):
    if p is None or (isinstance(p, float) and pd.isna(p)):
        return "—"
    return f"{p:+.1f}%"


def fmt_funnel_delta(v1, v2, fmt):
    if v1 is None or v2 is None:
        return "—"
    if (isinstance(v1, float) and pd.isna(v1)) or (isinstance(v2, float) and pd.isna(v2)):
        return "—"
    try:
        v1 = float(v1)
        v2 = float(v2)
    except (TypeError, ValueError):
        return "—"
    if fmt == "pct":
        return f"{(v2 - v1) * 100:+.2f} ppt"
    if fmt == "count":
        return f"{int(round(v2)) - int(round(v1)):+,}"
    if fmt == "dollar":
        return f"${v2 - v1:+,.2f}"
    return f"{v2 - v1:+.2f}"


def mix_shift_decomposition(w1_frac: np.ndarray, w2_frac: np.ndarray, r1: np.ndarray, r2: np.ndarray) -> dict:
    """Blended = Σ w·r; total change = mix + rate + interaction (same units as r).

    Mix effect uses the relative form ``(w2 - w1) * (r1 - blended_P1)`` so that
    each bucket's mix contribution is signed against the P1 weighted-average
    rate. With weights summing to 1, this keeps the overall mix-impact total
    identical to the absolute form while making per-bucket signs reflect
    whether the bucket sits above or below the P1 blended rate.
    """
    w1 = np.asarray(w1_frac, dtype=float)
    w2 = np.asarray(w2_frac, dtype=float)
    r1 = np.nan_to_num(np.asarray(r1, dtype=float), nan=0.0, posinf=0.0, neginf=0.0)
    r2 = np.nan_to_num(np.asarray(r2, dtype=float), nan=0.0, posinf=0.0, neginf=0.0)
    b1 = float(np.dot(w1, r1))
    b2 = float(np.dot(w2, r2))
    mix_e = (w2 - w1) * (r1 - b1)
    rate_e = w1 * (r2 - r1)
    inter_e = (w2 - w1) * (r2 - r1)
    return {
        "blend1": b1,
        "blend2": b2,
        "total_change": b2 - b1,
        "mix_e": mix_e,
        "rate_e": rate_e,
        "inter_e": inter_e,
        "sum_mix": float(np.sum(mix_e)),
        "sum_rate": float(np.sum(rate_e)),
        "sum_inter": float(np.sum(inter_e)),
    }


# ── Header ─────────────────────────────────────────────────────────────────────
date_str = ""
if df["call_date_est"].notna().any():
    mn = df["call_date_est"].min().strftime("%b %d")
    mx = df["call_date_est"].max().strftime("%b %d, %Y")
    date_str = f"{mn} – {mx}"

title_help = f"{date_str} · {top_funnel_call_count(df):,} inbound calls in view"
st.title("⚡ Arcadia Performance Dash", help=title_help)
st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_overview, tab_volume, tab_agent, tab_current_tests, tab_lift = st.tabs([
    "Overview",
    "Volume Shifts",
    "Agent Level",
    "Current Tests",
    "Arcadia vs Atom",
])

with tab_current_tests:
    tab_brand, tab_fmp = st.tabs([
        "Branded Flow Test",
        "Find My Plan",
    ])

# ══════════════════════════════════════════════════════════════════════════════
# TAB — OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
with tab_overview:

    # One filtered frame without sidebar date range (WTD KPIs + custom period comparison share it).
    _df_no_dr = apply_filters(df_raw.copy(), use_date_range=False)

    # ── Top KPI row — partial Mon–Sun week through latest data vs pooled P4WA, ignores date filter ─
    _wtd_asof = report_through_date(_df_no_dr)
    _wtd_ws = monday_of_week_containing(_wtd_asof)
    st.subheader(
        "Performance So Far This Week",
        help=(
            "Mon–Sun calendar weeks · partial current week through latest loaded data vs **P4WA** "
            "(same KPIs computed on all calls in the **four prior full Mon–Sun weeks** together — pooled, "
            "not a weekly average) · ignores date filter · Center and other sidebar filters apply. "
            f"Comparison dates: {_wtd_ws:%b %d}–{_wtd_asof:%b %d} vs P4WA."
        ),
    )

    def _wk_raw(fn):
        """Uses df_raw with sidebar filters except date."""
        return wtd_vs_four_week_pooled(_df_no_dr, fn)

    def wk_pct_delta_vs_avg(cur, baseline):
        if cur is None or baseline is None or pd.isna(cur) or pd.isna(baseline) or baseline == 0:
            return None
        return f"{(cur / baseline - 1) * 100:+.1f}% vs P4WA"

    def wtd_display_val(fn):
        cur, _ = _wk_raw(fn)
        return cur

    lw_rev_call  = wtd_display_val(lambda d: safe_rate(d.loc[order_revenue_mask(d), "total_revenue"].sum() if "total_revenue" in d.columns else 0, top_funnel_call_count(d)))
    lw_net_conv  = wtd_display_val(lambda d: safe_rate(d.loc[order_revenue_mask(d), "orders"].sum() if "orders" in d.columns else 0, top_funnel_call_count(d)))
    lw_rev_order = wtd_display_val(lambda d: safe_rate(d.loc[order_revenue_mask(d), "total_revenue"].sum() if "total_revenue" in d.columns else 0, d.loc[order_revenue_mask(d), "orders"].sum() if "orders" in d.columns else 0))
    lw_cic       = wtd_display_val(lambda d: safe_rate(d.loc[top_funnel_mask(d), "credit_calls_flag"].sum() if "credit_calls_flag" in d.columns else 0, top_funnel_call_count(d)))
    lw_tt        = wtd_display_val(lambda d: d.loc[top_funnel_mask(d), "talk_time_minutes"].mean() if "talk_time_minutes" in d.columns else float("nan"))

    cv1, bv1 = _wk_raw(lambda d: safe_rate(d.loc[order_revenue_mask(d), "total_revenue"].sum() if "total_revenue" in d.columns else 0, top_funnel_call_count(d)))
    cv2, bv2 = _wk_raw(lambda d: safe_rate(d.loc[order_revenue_mask(d), "orders"].sum() if "orders" in d.columns else 0, top_funnel_call_count(d)))
    cv3, bv3 = _wk_raw(lambda d: safe_rate(d.loc[order_revenue_mask(d), "total_revenue"].sum() if "total_revenue" in d.columns else 0, d.loc[order_revenue_mask(d), "orders"].sum() if "orders" in d.columns else 0))
    cv4, bv4 = _wk_raw(lambda d: safe_rate(d.loc[top_funnel_mask(d), "credit_calls_flag"].sum() if "credit_calls_flag" in d.columns else 0, top_funnel_call_count(d)))
    cv5, bv5 = _wk_raw(lambda d: d.loc[top_funnel_mask(d), "talk_time_minutes"].mean() if "talk_time_minutes" in d.columns else float("nan"))

    km1, km2, km3, km4, km5 = st.columns(5)
    km1.metric("Rev / Call",         f"${lw_rev_call:,.2f}"  if lw_rev_call  and not pd.isna(lw_rev_call)  else "—", delta=wk_pct_delta_vs_avg(cv1, bv1))
    km2.metric("Net Conversion",     f"{lw_net_conv:.1%}"    if lw_net_conv  and not pd.isna(lw_net_conv)  else "—", delta=wk_pct_delta_vs_avg(cv2, bv2))
    km3.metric("Rev / Order",        f"${lw_rev_order:,.2f}" if lw_rev_order and not pd.isna(lw_rev_order) else "—", delta=wk_pct_delta_vs_avg(cv3, bv3))
    km4.metric("Calls Into Credit",  f"{lw_cic:.1%}"         if lw_cic       and not pd.isna(lw_cic)       else "—", delta=wk_pct_delta_vs_avg(cv4, bv4))
    km5.metric(
        "Talk Time",
        f"{lw_tt:.1f} min" if lw_tt and not pd.isna(lw_tt) else "—",
        delta=wk_pct_delta_vs_avg(cv5, bv5),
        delta_color="inverse",
    )

    st.divider()

    # ── Funnel table ───────────────────────────────────────────────────────────
    st.subheader("Funnel Over Time")

    ov_gran = time_granularity

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
            **stretch_width_kwargs(),
            hide_index=True,
            height=dataframe_display_height(len(funnel_table)),
        )
        table_export_row(funnel_table, "funnel_over_time.csv")
    else:
        st.info("No data available.")

    overview_visuals_container = st.container()
    st.divider()

    # ── Custom period comparison (ignores sidebar date filter) ─────────────────
    st.subheader(
        "Custom Period Comparison",
        help=(
            "Ignores the sidebar **Date Range**. Uses Center, Marketing, Mover/Switcher, Tenure, and Call Type filters. "
            "Each period is one aggregate over its date window (same metrics as the funnel table)."
        ),
    )
    df_cmp = _df_no_dr
    if "call_date_est" in df_cmp.columns and len(df_cmp) > 0:
        _cmp_min = df_cmp["call_date_est"].min().date()
        _cmp_max = df_cmp["call_date_est"].max().date()
        _cmp_cap = _cmp_max
        if _cmp_cap < _cmp_min:
            _cmp_cap = _cmp_min
        _w = timedelta(days=6)
        _d2_end = max(_cmp_min, _cmp_cap)
        _d2_start = max(_cmp_min, _d2_end - _w)
        _d1_end = _d2_start - timedelta(days=1)
        _d1_start = max(_cmp_min, _d1_end - _w)
        if _d1_start > _d1_end:
            _d1_start = _cmp_min
            _d1_end = min(_cmp_cap, _d1_start + _w)

        _OCK1, _OCK2 = "ov_cmp_period1", "ov_cmp_period2"

        if _OCK1 not in st.session_state:
            st.session_state[_OCK1] = (_d1_start, _d1_end)
        if _OCK2 not in st.session_state:
            st.session_state[_OCK2] = (_d2_start, _d2_end)
        # Only clamp complete ranges — range pickers briefly hold 0–1 dates; clamping would reset to defaults.
        _rv1 = st.session_state.get(_OCK1)
        if isinstance(_rv1, (tuple, list)) and len(_rv1) == 2:
            st.session_state[_OCK1] = cmp_date_range_clamp(
                _cmp_min, _cmp_cap, tuple(_rv1), (_d1_start, _d1_end)
            )
        _rv2 = st.session_state.get(_OCK2)
        if isinstance(_rv2, (tuple, list)) and len(_rv2) == 2:
            st.session_state[_OCK2] = cmp_date_range_clamp(
                _cmp_min, _cmp_cap, tuple(_rv2), (_d2_start, _d2_end)
            )

        pc_a, pc_b = st.columns(2)
        with pc_a:
            cmp_range_1 = st.date_input(
                "Period 1",
                min_value=_cmp_min,
                max_value=_cmp_cap,
                key=_OCK1,
            )
        with pc_b:
            cmp_range_2 = st.date_input(
                "Period 2",
                min_value=_cmp_min,
                max_value=_cmp_cap,
                key=_OCK2,
            )

        theme.persist_ov_cmp_dates_browser()

        def _slice_period(d_all, dr):
            if len(dr) != 2:
                return d_all.iloc[0:0]
            a, b = dr[0], dr[1]
            if a > b:
                a, b = b, a
            m = (d_all["call_date_est"].dt.date >= a) & (d_all["call_date_est"].dt.date <= b)
            return d_all.loc[m]

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
                pch = pct_change_vs_prior(raw1, raw2)
                cmp_rows.append(
                    {
                        "Metric": metric,
                        col1: disp1,
                        col2: disp2,
                        "% Change (P2 vs P1)": fmt_pct_change_str(pch),
                    }
                )
            cmp_table = pd.DataFrame(cmp_rows)
            _pch_col = "% Change (P2 vs P1)"

            def _style_cmp_row(row):
                m = row["Metric"]
                p = parse_display_pct(row[_pch_col])
                out = pd.Series("", index=row.index)
                if p is not None:
                    out[_pch_col] = theme.pct_change_cell_style(m, p)
                return out

            cmp_styler = cmp_table.style.apply(_style_cmp_row, axis=1)
            st.dataframe(
                cmp_styler,
                **stretch_width_kwargs(),
                hide_index=True,
                height=dataframe_display_height(len(cmp_table)),
            )
            table_export_row(cmp_table, "period_comparison.csv")
        else:
            st.info("Select a full start and end date for each period.")
    else:
        st.info("No data available for period comparison with current filters.")

    overview_visuals_container.divider()

    # ── Trend chart — shares granularity with funnel table ────────────────────
    overview_visuals_container.subheader("Trend Over Time")

    tr_c1, tr_c2 = overview_visuals_container.columns(2)
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
            "Sold Partner":     SOLD_PROVIDER_COLUMN,
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
                num = orders_rev_rows["total_revenue"].sum() if "total_revenue" in orders_rev_rows.columns else orders_rev_rows["gcv_fo"].sum() if "gcv_fo" in orders_rev_rows.columns else 0
                denom = top_funnel_call_count(grp) if denom_col_ov == "n_calls" else (orders_rev_rows["orders"].sum() if "orders" in orders_rev_rows.columns else 0)
                return safe_rate(num, denom)
            elif ov_metric_choice == "Net Conversion":
                num = orders_rev_rows["orders"].sum() if "orders" in orders_rev_rows.columns else 0
                return safe_rate(num, top_funnel_call_count(grp))
            elif ov_metric_choice == "Top Product Mix":
                num = orders_rev_rows["tpsales_flag"].sum() if "tpsales_flag" in orders_rev_rows.columns else 0
                denom = orders_rev_rows["orders"].sum() if "orders" in orders_rev_rows.columns else 0
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
        _muted = chart_muted()

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

        _trend_title = overview_chart_title(ov_metric_choice, ov_group_choice)
        apply_chart_theme(
            fig_ov_trend,
            title=layout_chart_title(_trend_title),
            yaxis_tickformat=y_fmt,
            yaxis_tickprefix=y_prefix,
            yaxis_ticksuffix=y_suffix,
            yaxis_title=y_title,
            xaxis=dict(tickvals=tick_vals, ticktext=tick_text, **_ax_ov),
            height=400,
            margin=dict(l=50, r=20, t=48, b=40),
            legend=dict(orientation="h", y=-0.2),
        )
        overview_visuals_container.plotly_chart(fig_ov_trend, **stretch_width_kwargs())

        # ── Performance snapshot (bar) — same metric / group as trend ───────────
        overview_visuals_container.divider()
        overview_visuals_container.subheader(
            "Performance Snapshot",
            help="Same metric and group by as above · one value per category for the full filtered date range.",
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

        _mline, _tbar = chart_hist_stroke_and_title()
        fig_ov_bar = go.Figure(
            go.Bar(
                x=bar_df["Category"],
                y=bar_df["Value"],
                marker_color=colorway_cycled(len(bar_df)),
                opacity=0.92,
                marker_line_color=_mline,
                marker_line_width=1,
                text=[_fmt_bar_val(v) for v in bar_df["Value"]],
                textposition="outside",
                textfont=dict(size=11, color=_tbar),
            )
        )
        apply_chart_theme(
            fig_ov_bar,
            title=layout_chart_title(_snap_title),
            yaxis_tickformat=y_fmt,
            yaxis_tickprefix=y_prefix,
            yaxis_ticksuffix=y_suffix,
            yaxis_title=y_title,
            xaxis=dict(tickangle=-22, automargin=True, **_ax_ov),
            height=min(920, 320 + 48 * max(len(bar_df), 1)),
            margin=dict(l=50, r=28, t=56, b=120),
            showlegend=False,
        )
        snapshot_chart_slot = overview_visuals_container.empty()
        snapshot_chart_slot.plotly_chart(
            fig_ov_bar,
            **stretch_width_kwargs(),
            key="ov_performance_snapshot_chart",
        )
    else:
        overview_visuals_container.info("No data available for trend chart.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB — BRANDED FLOW TEST
# ══════════════════════════════════════════════════════════════════════════════
with tab_brand:
    st.subheader(
        "Branded Flow Test",
        help=(
            "Compares calls where **brand_test** is `control` vs `test`. "
            "The sidebar Date Range is ignored; other sidebar filters still apply."
        ),
    )

    if "brand_test" not in df_raw.columns:
        st.info("The loaded call data does not include a brand_test field.")
    else:
        brand_base = apply_filters(df_raw.copy(), use_date_range=False)

        if "call_date_est" not in brand_base.columns or brand_base.empty:
            st.info("No branded-flow data is available with the current filters.")
        else:
            brand_base = brand_base.dropna(subset=["call_date_est"]).copy()
            brand_base[BRAND_TEST_COL] = (
                brand_base["brand_test"].astype("string").str.strip().str.lower()
            )
            brand_base = brand_base[brand_base[BRAND_TEST_COL].isin(BRAND_TEST_VALUES)].copy()

            if brand_base.empty:
                st.info("No control/test branded-flow calls match the current filters.")
            else:
                if "call_time_est" in brand_base.columns:
                    brand_base[BRAND_TEST_DT_COL] = pd.to_datetime(
                        brand_base["call_time_est"], errors="coerce"
                    )
                    brand_has_time = brand_base["call_time_est"].notna().any()
                else:
                    brand_base[BRAND_TEST_DT_COL] = pd.NaT
                    brand_has_time = False

                brand_base[BRAND_TEST_DT_COL] = brand_base[BRAND_TEST_DT_COL].fillna(
                    brand_base["call_date_est"]
                )
                launch_floor = (
                    BRAND_TEST_LAUNCH_AT
                    if brand_has_time
                    else pd.Timestamp(BRAND_TEST_LAUNCH_AT.date())
                )
                brand_base = brand_base[brand_base[BRAND_TEST_DT_COL] >= launch_floor].copy()

                if brand_base.empty:
                    st.info("No control/test branded-flow calls are available since launch.")
                else:
                    max_brand_dt = brand_base[BRAND_TEST_DT_COL].max()
                    min_brand_date = BRAND_TEST_LAUNCH_AT.date()
                    max_brand_date = max_brand_dt.date()
                    if max_brand_date < min_brand_date:
                        max_brand_date = min_brand_date

                    _BRAND_DATE_KEY = "brand_flow_date_range"
                    _brand_default_range = (min_brand_date, max_brand_date)
                    if _BRAND_DATE_KEY not in st.session_state:
                        st.session_state[_BRAND_DATE_KEY] = _brand_default_range

                    _brand_rv = st.session_state.get(_BRAND_DATE_KEY)
                    if isinstance(_brand_rv, (tuple, list)) and len(_brand_rv) == 2:
                        st.session_state[_BRAND_DATE_KEY] = cmp_date_range_clamp(
                            min_brand_date,
                            max_brand_date,
                            tuple(_brand_rv),
                            _brand_default_range,
                        )

                    brand_date_range = st.date_input(
                        "Date Range",
                        min_value=min_brand_date,
                        max_value=max_brand_date,
                        key=_BRAND_DATE_KEY,
                        help=(
                            "Defaults to launch: May 27, 2026 at 9:00 AM through "
                            "the latest loaded branded-flow row. "
                            f"Current default launch window: {BRAND_TEST_LAUNCH_AT:%b %d, %Y %I:%M %p} "
                            f"through latest loaded branded-flow row ({max_brand_dt:%b %d, %Y %I:%M %p})."
                        ),
                    )

                    def _slice_brand_dates(d_all: pd.DataFrame, dr):
                        if len(dr) != 2:
                            return d_all.iloc[0:0]
                        a, b = dr[0], dr[1]
                        if a > b:
                            a, b = b, a
                        start_at = pd.Timestamp(a)
                        if a == BRAND_TEST_LAUNCH_AT.date():
                            start_at = BRAND_TEST_LAUNCH_AT if brand_has_time else start_at
                        start_at = max(start_at, launch_floor)
                        end_exclusive = pd.Timestamp(b) + pd.Timedelta(days=1)
                        m = (
                            (d_all[BRAND_TEST_DT_COL] >= start_at) &
                            (d_all[BRAND_TEST_DT_COL] < end_exclusive)
                        )
                        return d_all.loc[m].copy()

                    if len(brand_date_range) != 2:
                        st.info("Select a full start and end date for the branded-flow window.")
                        brand_df = brand_base.iloc[0:0].copy()
                    else:
                        brand_df = _slice_brand_dates(brand_base, brand_date_range)

                    if not brand_df.empty:
                        control_df = brand_df[brand_df[BRAND_TEST_COL] == "control"]
                        test_df = brand_df[brand_df[BRAND_TEST_COL] == "test"]

                        kc1, kc2, kc3 = st.columns(3)
                        kc1.metric("Control Calls", f"{top_funnel_call_count(control_df):,}")
                        kc2.metric("Test Calls", f"{top_funnel_call_count(test_df):,}")
                        kc3.metric("Total Calls", f"{top_funnel_call_count(brand_df):,}")

                        st.divider()
                        st.subheader("Control vs Test Funnel")

                        brand_rows = []
                        for metric, fmt in FUNNEL_METRICS:
                            raw_control = compute_funnel_row(control_df, metric)
                            raw_test = compute_funnel_row(test_df, metric)
                            brand_rows.append(
                                {
                                    "Metric": metric,
                                    "Control": fmt_funnel(raw_control, fmt),
                                    "Test": fmt_funnel(raw_test, fmt),
                                    "% Change (Test vs Control)": fmt_pct_change_str(
                                        pct_change_vs_prior(raw_control, raw_test)
                                    ),
                                }
                            )
                        brand_table = pd.DataFrame(brand_rows)
                        _brand_pch_col = "% Change (Test vs Control)"

                        def _style_brand_funnel_row(row):
                            out = pd.Series("", index=row.index)
                            p = parse_display_pct(row[_brand_pch_col])
                            if p is not None:
                                out[_brand_pch_col] = theme.pct_change_cell_style(row["Metric"], p)
                            return out

                        st.dataframe(
                            brand_table.style.apply(_style_brand_funnel_row, axis=1),
                            **stretch_width_kwargs(),
                            hide_index=True,
                            height=dataframe_display_height(len(brand_table)),
                        )
                        table_export_row(brand_table, "branded_flow_test_funnel.csv")

                        st.divider()
                        st.subheader("Trend Over Time")

                        brand_gran = time_granularity
                        bt_c1, bt_c2 = st.columns(2)
                        with bt_c1:
                            brand_metric_choice = st.selectbox(
                                "Metric",
                                [
                                    "Net Conversion", "Total Revenue", "Rev / Call", "Rev / Order",
                                    "Top Product Mix", "Contact Rate", "Credit Rate",
                                    "Passed Credit Rate", "Passed Credit Conv.", "Failed Credit Conv.",
                                    "Talk Time", "Calls",
                                ],
                                key="brand_flow_metric",
                            )
                        with bt_c2:
                            BRAND_GROUP_COL_MAP = {
                                "Center":           "center_location",
                                "Marketing Bucket": "marketing_bucket",
                                "Mover / Switcher": "moverSwitcher",
                                "Tenure Bucket":    "tenure_bucket",
                                "Call Type":        "call_type",
                                "Sold Partner":     SOLD_PROVIDER_COLUMN,
                                "None (Overall)":   None,
                            }
                            brand_group_choice = st.selectbox(
                                "Group By",
                                options=list(BRAND_GROUP_COL_MAP.keys()),
                                index=0,
                                key="brand_flow_group",
                            )
                            brand_group_col = BRAND_GROUP_COL_MAP[brand_group_choice]

                        BRAND_METRIC_MAP = {
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
                        num_col_bt, denom_col_bt, fmt_bt = BRAND_METRIC_MAP[brand_metric_choice]

                        def agg_metric_brand(grp):
                            inbound = grp[top_funnel_mask(grp)]
                            orders_rev_rows = grp[order_revenue_mask(grp)]
                            if brand_metric_choice == "Calls":
                                return top_funnel_call_count(grp)
                            elif brand_metric_choice == "Talk Time":
                                return (
                                    inbound["talk_time_minutes"].mean()
                                    if "talk_time_minutes" in inbound.columns
                                    else float("nan")
                                )
                            elif brand_metric_choice == "Total Revenue":
                                return (
                                    orders_rev_rows["total_revenue"].sum()
                                    if "total_revenue" in orders_rev_rows.columns
                                    else orders_rev_rows["gcv_fo"].sum()
                                    if "gcv_fo" in orders_rev_rows.columns
                                    else 0
                                )
                            elif fmt_bt == "dollar" and denom_col_bt:
                                num = (
                                    orders_rev_rows["total_revenue"].sum()
                                    if "total_revenue" in orders_rev_rows.columns
                                    else orders_rev_rows["gcv_fo"].sum()
                                    if "gcv_fo" in orders_rev_rows.columns
                                    else 0
                                )
                                denom = (
                                    top_funnel_call_count(grp)
                                    if denom_col_bt == "n_calls"
                                    else (
                                        orders_rev_rows["orders"].sum()
                                        if "orders" in orders_rev_rows.columns
                                        else 0
                                    )
                                )
                                return safe_rate(num, denom)
                            elif brand_metric_choice == "Net Conversion":
                                num = (
                                    orders_rev_rows["orders"].sum()
                                    if "orders" in orders_rev_rows.columns
                                    else 0
                                )
                                return safe_rate(num, top_funnel_call_count(grp))
                            elif brand_metric_choice == "Top Product Mix":
                                num = (
                                    orders_rev_rows["tpsales_flag"].sum()
                                    if "tpsales_flag" in orders_rev_rows.columns
                                    else 0
                                )
                                denom = (
                                    orders_rev_rows["orders"].sum()
                                    if "orders" in orders_rev_rows.columns
                                    else 0
                                )
                                return safe_rate(num, denom)
                            elif fmt_bt == "pct":
                                if num_col_bt not in inbound.columns:
                                    return float("nan")
                                num = inbound[num_col_bt].sum()
                                if denom_col_bt == "n_calls":
                                    denom = top_funnel_call_count(grp)
                                elif denom_col_bt and denom_col_bt in inbound.columns:
                                    denom = inbound[denom_col_bt].sum()
                                else:
                                    return float("nan")
                                return safe_rate(num, denom)
                            return float("nan")

                        brand_ts = brand_df.dropna(subset=[BRAND_TEST_DT_COL]).copy()
                        brand_ts["period"] = period_labels(brand_ts[BRAND_TEST_DT_COL], brand_gran)

                        fig_brand_trend = go.Figure()
                        _ax_brand = plotly_axis_lines()
                        _muted_brand = chart_muted()
                        _dash_by_test = {"control": "solid", "test": "dot"}
                        _color_by_test = {"control": PLOT_COLORWAY[0], "test": PLOT_COLORWAY[1]}

                        if brand_group_col and brand_group_col in brand_ts.columns:
                            group_items = [
                                (str(group_val), grp_c)
                                for group_val, grp_c in brand_ts.dropna(subset=[brand_group_col]).groupby(brand_group_col)
                            ]
                        else:
                            group_items = []

                        def _add_brand_traces(label, source, color=None):
                            for brand_value in BRAND_TEST_VALUES:
                                sub = source[source[BRAND_TEST_COL] == brand_value]
                                if sub.empty:
                                    continue
                                ts_c = (
                                    sub.groupby("period")
                                    .apply(agg_metric_brand)
                                    .reset_index()
                                    .rename(columns={0: "value"})
                                )
                                ts_c["period"] = pd.to_datetime(ts_c["period"])
                                ts_c = ts_c.sort_values("period")
                                trace_name = (
                                    BRAND_TEST_DISPLAY[brand_value]
                                    if label == "Overall" and not group_items
                                    else f"{label} - {BRAND_TEST_DISPLAY[brand_value]}"
                                )
                                trace_color = color or _color_by_test[brand_value]
                                fig_brand_trend.add_trace(
                                    go.Scatter(
                                        x=ts_c["period"],
                                        y=ts_c["value"],
                                        name=trace_name,
                                        mode="lines+markers",
                                        line=dict(
                                            width=2,
                                            dash=_dash_by_test[brand_value],
                                            color=trace_color,
                                        ),
                                        marker=dict(size=5, color=trace_color),
                                    )
                                )

                        for i, (group_label, group_df) in enumerate(group_items):
                            _add_brand_traces(group_label, group_df, colorway_cycled(len(group_items))[i])

                        _add_brand_traces("Overall", brand_ts, _muted_brand if group_items else None)

                        if len(fig_brand_trend.data) == 0:
                            st.info("No data available for the selected trend combination.")
                        else:
                            tick_vals = sorted(pd.to_datetime(brand_ts["period"].dropna().unique()).tolist())
                            tick_text = [pd.Timestamp(x).strftime(PERIOD_FMT[brand_gran]) for x in tick_vals]

                            if fmt_bt == "pct":
                                y_fmt, y_prefix, y_suffix, y_title = ".1%", "", "", brand_metric_choice
                            elif fmt_bt == "dollar":
                                y_fmt, y_prefix, y_suffix, y_title = ",.0f", "$", "", brand_metric_choice
                            elif brand_metric_choice == "Talk Time":
                                y_fmt, y_prefix, y_suffix, y_title = ".2f", "", "", "Talk Time (Minutes)"
                            else:
                                y_fmt, y_prefix, y_suffix, y_title = ",.0f", "", "", brand_metric_choice

                            _brand_title = (
                                "Control vs Test - "
                                f"{overview_chart_title(brand_metric_choice, brand_group_choice)}"
                            )
                            apply_chart_theme(
                                fig_brand_trend,
                                title=layout_chart_title(_brand_title),
                                yaxis_tickformat=y_fmt,
                                yaxis_tickprefix=y_prefix,
                                yaxis_ticksuffix=y_suffix,
                                yaxis_title=y_title,
                                xaxis=dict(tickvals=tick_vals, ticktext=tick_text, **_ax_brand),
                                height=420,
                                margin=dict(l=50, r=20, t=48, b=76),
                                legend=dict(orientation="h", y=-0.24),
                            )
                            st.plotly_chart(fig_brand_trend, **stretch_width_kwargs())

                        st.divider()
                        st.subheader(
                            "ECP Module Funnel",
                            help=(
                                "`ecp_module_selection` tracks whether someone clicked anything in the new experience, "
                                "then which module they selected."
                            ),
                        )

                        if ECP_MODULE_SELECTION_COL not in brand_df.columns:
                            st.info("The loaded call data does not include an ecp_module_selection field.")
                        else:
                            module_df = brand_df[top_funnel_mask(brand_df)].copy()
                            module_df[ECP_MODULE_SELECTION_CLEAN_COL] = clean_ecp_module_selection(module_df)
                            module_df["_ecp_interacted"] = module_df[ECP_MODULE_SELECTION_CLEAN_COL].notna()

                            side_totals = {}
                            side_interacted = {}
                            for brand_value in BRAND_TEST_VALUES:
                                side_df = module_df[module_df[BRAND_TEST_COL] == brand_value]
                                side_totals[brand_value] = len(side_df)
                                side_interacted[brand_value] = int(side_df["_ecp_interacted"].sum())

                            def _fmt_module_cell(count, rate=None):
                                if rate is None:
                                    return f"{count:,}"
                                return f"{count:,} ({rate:.1%})" if pd.notna(rate) else f"{count:,} (—)"

                            def _fmt_module_pct_change(control_value, test_value):
                                return fmt_pct_change_str(pct_change_vs_prior(control_value, test_value))

                            control_clicked_rate = safe_rate(
                                side_interacted["control"],
                                side_totals["control"],
                            )
                            test_clicked_rate = safe_rate(
                                side_interacted["test"],
                                side_totals["test"],
                            )
                            module_funnel_rows = [
                                {
                                    "Step": "All People",
                                    "Control": _fmt_module_cell(side_totals["control"]),
                                    "Test": _fmt_module_cell(side_totals["test"]),
                                    "% Change": _fmt_module_pct_change(
                                        side_totals["control"],
                                        side_totals["test"],
                                    ),
                                },
                                {
                                    "Step": "Clicked Anything",
                                    "Control": _fmt_module_cell(
                                        side_interacted["control"],
                                        control_clicked_rate,
                                    ),
                                    "Test": _fmt_module_cell(
                                        side_interacted["test"],
                                        test_clicked_rate,
                                    ),
                                    "% Change": _fmt_module_pct_change(
                                        control_clicked_rate,
                                        test_clicked_rate,
                                    ),
                                },
                            ]

                            interacted_module_df = module_df[module_df["_ecp_interacted"]].copy()
                            if not interacted_module_df.empty:
                                response_order = (
                                    interacted_module_df[ECP_MODULE_SELECTION_CLEAN_COL]
                                    .map(display_ecp_module_selection)
                                    .value_counts()
                                    .index
                                    .tolist()
                                )
                                for response in response_order:
                                    response_counts = {}
                                    response_rates = {}
                                    for brand_value in BRAND_TEST_VALUES:
                                        side_response_count = int(
                                            (
                                                (interacted_module_df[BRAND_TEST_COL] == brand_value)
                                                & (
                                                    interacted_module_df[ECP_MODULE_SELECTION_CLEAN_COL]
                                                    .map(display_ecp_module_selection)
                                                    == response
                                                )
                                            ).sum()
                                        )
                                        response_counts[brand_value] = side_response_count
                                        response_rates[brand_value] = safe_rate(
                                            side_response_count,
                                            side_interacted[brand_value],
                                        )

                                    module_funnel_rows.append(
                                        {
                                            "Step": response,
                                            "Control": _fmt_module_cell(
                                                response_counts["control"],
                                                response_rates["control"],
                                            ),
                                            "Test": _fmt_module_cell(
                                                response_counts["test"],
                                                response_rates["test"],
                                            ),
                                            "% Change": _fmt_module_pct_change(
                                                response_rates["control"],
                                                response_rates["test"],
                                            ),
                                        }
                                    )

                            module_funnel_table = pd.DataFrame(module_funnel_rows)
                            st.dataframe(
                                module_funnel_table,
                                **stretch_width_kwargs(),
                                hide_index=True,
                                height=dataframe_display_height(len(module_funnel_table)),
                            )
                            table_export_row(module_funnel_table, "branded_flow_ecp_module_funnel.csv")
                    else:
                        st.info("No control/test branded-flow calls match the selected tab date range.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB — FIND MY PLAN
# ══════════════════════════════════════════════════════════════════════════════
with tab_fmp:
    fmp_help_base = (
        "Uses the site experience hint launched May 20, 2026 around 11:00 AM EST. "
        "The sidebar Date Range is ignored; other sidebar filters still apply."
    )
    fmp_header = st.empty()
    fmp_header.subheader("Find My Plan", help=fmp_help_base)

    fmp_hint_col = site_experience_hint_column(df_raw)

    if fmp_hint_col is None:
        st.info("The loaded call data does not include a site experience hint field.")
    else:
        fmp_base = apply_filters(df_raw.copy(), use_date_range=False)

        if "call_date_est" not in fmp_base.columns or fmp_base.empty:
            st.info("No Find My Plan data is available with the current filters.")
        else:
            fmp_base = fmp_base.dropna(subset=["call_date_est"]).copy()
            fmp_base[FMP_DT_COL], fmp_has_time = fmp_datetime_series(fmp_base)
            fmp_launch_floor = (
                FMP_LAUNCH_AT
                if fmp_has_time
                else pd.Timestamp(FMP_LAUNCH_AT.date())
            )
            fmp_base = fmp_base[fmp_base[FMP_DT_COL] >= fmp_launch_floor].copy()

            if fmp_base.empty:
                st.info("No calls are available since the Find My Plan launch.")
            else:
                hint_text = fmp_base[fmp_hint_col].astype("string").fillna("")
                fmp_df = fmp_base[
                    hint_text.str.contains(FMP_HINT_PREFIX, case=False, na=False)
                ].copy()
                if not fmp_df.empty:
                    fmp_df = add_fmp_recommendation_columns(fmp_df, fmp_hint_col)

                latest_fmp_base_dt = fmp_base[FMP_DT_COL].max()
                fmp_header.subheader(
                    "Find My Plan",
                    help=(
                        f"{fmp_help_base} Launch window: {FMP_LAUNCH_AT:%b %d, %Y %I:%M %p} "
                        f"through latest loaded row ({latest_fmp_base_dt:%b %d, %Y %I:%M %p})."
                    ),
                )

                fmp_orders_rows = fmp_df[order_revenue_mask(fmp_df)] if not fmp_df.empty else fmp_df
                fmp_orders = (
                    int(fmp_orders_rows["orders"].sum())
                    if "orders" in fmp_orders_rows.columns
                    else 0
                )
                fmp_sales_rows = (
                    fmp_orders_rows[
                        pd.to_numeric(fmp_orders_rows["orders"], errors="coerce")
                        .fillna(0)
                        .gt(0)
                    ].copy()
                    if "orders" in fmp_orders_rows.columns
                    else fmp_orders_rows.iloc[0:0].copy()
                )
                fmp_same_plan_orders = 0
                if (
                    not fmp_sales_rows.empty
                    and FMP_REC_PLAN_COL in fmp_sales_rows.columns
                    and "product_name" in fmp_sales_rows.columns
                    and "orders" in fmp_sales_rows.columns
                ):
                    rec_plan_key = normalize_plan_match_text(fmp_sales_rows[FMP_REC_PLAN_COL])
                    sold_plan_key = normalize_plan_match_text(fmp_sales_rows["product_name"])
                    same_plan_mask = (
                        rec_plan_key.notna()
                        & sold_plan_key.notna()
                        & rec_plan_key.ne("")
                        & rec_plan_key.eq(sold_plan_key)
                    )
                    fmp_same_plan_orders = int(
                        pd.to_numeric(
                            fmp_sales_rows.loc[same_plan_mask, "orders"],
                            errors="coerce",
                        ).fillna(0).sum()
                    )
                fmp_same_plan_rate = safe_rate(fmp_same_plan_orders, fmp_orders)
                fmp_calls = top_funnel_call_count(fmp_df)
                since_launch_calls = top_funnel_call_count(fmp_base)
                fmp_rec_count = (
                    fmp_df[FMP_REC_TEXT_COL].dropna().nunique()
                    if FMP_REC_TEXT_COL in fmp_df.columns
                    else 0
                )

                fk1, fk2, fk3, fk4, fk5, fk6 = st.columns(6)
                fk1.metric("FMP Calls", f"{fmp_calls:,}")
                fk2.metric(
                    "FMP Share",
                    f"{safe_rate(fmp_calls, since_launch_calls):.1%}"
                    if since_launch_calls
                    else "—",
                )
                fk3.metric("Orders", f"{fmp_orders:,}")
                fk4.metric(
                    "Net Conversion",
                    f"{safe_rate(fmp_orders, fmp_calls):.1%}" if fmp_calls else "—",
                )
                fk5.metric("Recommendations", f"{fmp_rec_count:,}")
                fk6.metric(
                    "Same Plan Sales",
                    f"{fmp_same_plan_rate:.1%}" if fmp_orders else "—",
                    help=(
                        "Share of FMP orders where the sold product_name matches "
                        "the recommended plan parsed from the FMP hint."
                    ),
                )

                st.divider()
                st.subheader("FMP Funnel Since Launch")

                if fmp_df.empty:
                    st.info("No Find My Plan calls match the current filters.")
                else:
                    fmp_funnel_rows = []
                    for metric, fmt in FUNNEL_METRICS:
                        fmp_funnel_rows.append({
                            "Metric": metric,
                            "FMP Since Launch": fmt_funnel(
                                compute_funnel_row(fmp_df, metric),
                                fmt,
                            ),
                        })
                    fmp_funnel_table = pd.DataFrame(fmp_funnel_rows)
                    st.dataframe(
                        fmp_funnel_table,
                        **stretch_width_kwargs(),
                        hide_index=True,
                        height=dataframe_display_height(len(fmp_funnel_table)),
                    )
                    table_export_row(fmp_funnel_table, "find_my_plan_funnel.csv")

                    st.divider()
                    st.subheader("Recommended Plan Mix")

                    fmp_mix_source = fmp_df.dropna(subset=[FMP_REC_TEXT_COL]).copy()
                    if fmp_mix_source.empty:
                        st.info("No parseable Find My Plan recommendations are available.")
                    else:
                        fmp_mix_source["Recommended Brand / Provider"] = (
                            fmp_mix_source[FMP_REC_PROVIDER_COL]
                            .astype("string")
                            .fillna("Unparsed")
                            .str.strip()
                            .replace("", "Unparsed")
                        )
                        fmp_mix_source["Recommended Plan"] = (
                            fmp_mix_source[FMP_REC_PLAN_COL]
                            .astype("string")
                            .fillna(fmp_mix_source[FMP_REC_TEXT_COL])
                            .str.strip()
                        )
                        fmp_mix = (
                            fmp_mix_source
                            .groupby(["Recommended Brand / Provider", "Recommended Plan"], dropna=False)
                            .size()
                            .reset_index(name="FMP Calls")
                        )
                        fmp_mix["Share"] = fmp_mix["FMP Calls"] / fmp_mix["FMP Calls"].sum()
                        fmp_mix["Recommended"] = np.where(
                            fmp_mix["Recommended Brand / Provider"].eq("Unparsed"),
                            fmp_mix["Recommended Plan"],
                            fmp_mix["Recommended Brand / Provider"] + " - " + fmp_mix["Recommended Plan"],
                        )
                        fmp_mix = fmp_mix.sort_values(
                            ["FMP Calls", "Recommended"],
                            ascending=[False, True],
                        )

                        fmp_mix_plot = fmp_mix.sort_values(
                            ["FMP Calls", "Recommended"],
                            ascending=[True, False],
                        )
                        fig_fmp_mix = go.Figure(
                            go.Bar(
                                x=fmp_mix_plot["FMP Calls"],
                                y=fmp_mix_plot["Recommended"],
                                orientation="h",
                                marker_color=colorway_cycled(len(fmp_mix_plot)),
                                text=[
                                    f"{calls:,} ({share:.1%})"
                                    for calls, share in zip(
                                        fmp_mix_plot["FMP Calls"],
                                        fmp_mix_plot["Share"],
                                    )
                                ],
                                textposition="outside",
                                cliponaxis=False,
                                hovertemplate=(
                                    "%{y}<br>FMP calls: %{x:,}<br>"
                                    "Mix: %{customdata:.1%}<extra></extra>"
                                ),
                                customdata=fmp_mix_plot["Share"],
                            )
                        )
                        apply_chart_theme(
                            fig_fmp_mix,
                            title=layout_chart_title("FMP recommended plan mix"),
                            xaxis=plotly_axis_extra("FMP calls", rangemode="tozero"),
                            yaxis=plotly_axis_extra("Recommended brand / provider and plan", automargin=True),
                            height=min(920, max(360, 240 + 28 * len(fmp_mix_plot))),
                            margin=dict(l=52, r=110, t=52, b=52),
                            showlegend=False,
                        )
                        st.plotly_chart(fig_fmp_mix, **stretch_width_kwargs())

                    st.divider()
                    st.subheader("FMP Calls")

                    fmp_table = fmp_df.sort_values(FMP_DT_COL, ascending=False).copy()
                    fmp_table["_display_call_time"] = pd.to_datetime(
                        fmp_table[FMP_DT_COL],
                        errors="coerce",
                    ).dt.strftime("%b %d, %Y %I:%M %p")

                    sold_mask = (
                        fmp_table["orders"].fillna(0).astype(float).gt(0)
                        if "orders" in fmp_table.columns
                        else pd.Series(False, index=fmp_table.index)
                    )
                    fmp_table["_sold_provider_display"] = (
                        fmp_table[SOLD_PROVIDER_COLUMN]
                        if SOLD_PROVIDER_COLUMN in fmp_table.columns
                        else pd.Series(pd.NA, index=fmp_table.index)
                    )
                    fmp_table["_sold_plan_display"] = (
                        fmp_table["product_name"]
                        if "product_name" in fmp_table.columns
                        else pd.Series(pd.NA, index=fmp_table.index)
                    )
                    fmp_table.loc[~sold_mask, ["_sold_provider_display", "_sold_plan_display"]] = pd.NA

                    fmp_table_cols = [
                        ("_display_call_time", "Call Time"),
                        ("call_id", "Call ID"),
                        ("agent_name", "Agent"),
                        ("center_location", "Center"),
                        ("marketing_bucket", "Marketing Bucket"),
                        ("moverSwitcher", "Mover / Switcher"),
                        (FMP_REC_PROVIDER_COL, "Recommended Brand / Provider"),
                        (FMP_REC_PLAN_COL, "Recommended Plan"),
                        ("_sold_provider_display", "Sold Provider"),
                        ("_sold_plan_display", "Sold Plan"),
                        ("orders", "Orders"),
                        ("total_revenue", "Revenue"),
                        (fmp_hint_col, "Site Experience Hint"),
                    ]
                    display_cols = [
                        (src, label)
                        for src, label in fmp_table_cols
                        if src in fmp_table.columns
                    ]
                    fmp_call_table = fmp_table[[src for src, _ in display_cols]].copy()
                    fmp_call_table.columns = [label for _, label in display_cols]

                    for col in [
                        "Call Time",
                        "Call ID",
                        "Agent",
                        "Center",
                        "Marketing Bucket",
                        "Mover / Switcher",
                        "Recommended Brand / Provider",
                        "Recommended Plan",
                        "Sold Provider",
                        "Sold Plan",
                        "Site Experience Hint",
                    ]:
                        if col in fmp_call_table.columns:
                            fmp_call_table[col] = (
                                fmp_call_table[col]
                                .astype("string")
                                .str.strip()
                                .replace({"": pd.NA, "<NA>": pd.NA})
                                .fillna("—")
                            )
                    if "Orders" in fmp_call_table.columns:
                        fmp_call_table["Orders"] = (
                            pd.to_numeric(fmp_call_table["Orders"], errors="coerce")
                            .fillna(0)
                            .astype(int)
                            .map(lambda x: f"{x:,}")
                        )
                    if "Revenue" in fmp_call_table.columns:
                        fmp_call_table["Revenue"] = (
                            pd.to_numeric(fmp_call_table["Revenue"], errors="coerce")
                            .map(lambda x: f"${x:,.2f}" if pd.notna(x) else "—")
                        )

                    st.dataframe(
                        fmp_call_table,
                        **stretch_width_kwargs(),
                        hide_index=True,
                        height=dataframe_display_height(len(fmp_call_table), cap=2400),
                    )
                    table_export_row(fmp_call_table, "find_my_plan_calls.csv")

# ══════════════════════════════════════════════════════════════════════════════
# TAB — VOLUME SHIFTS (SECOND TAB): INBOUND MIX + CUSTOM-PERIOD MIX / METRIC BY BUCKET
# ══════════════════════════════════════════════════════════════════════════════
with tab_volume:
    st.subheader(
        "Mix Shifts",
        help=(
            "**Trend line chart** uses the sidebar **Date Range** plus Center, Marketing, Mover/Switcher, Tenure, and Site/SERP. "
            "Choose a **funnel step** to plot that step’s **mix** across the selected dimension (shares sum to 100% within each period). "
            "**Custom period mix** below ignores the sidebar date range "
            "(same rule as Overview → Custom Period Comparison) and compares **mix %** for Period 1 vs Period 2."
        ),
    )

    VOL_DIM_CHOICES = {
        "Center": "center_location",
        "Marketing Bucket": "marketing_bucket",
        "Mover / Switcher": "moverSwitcher",
        "Tenure Bucket": "tenure_bucket",
        "Site/SERP": "call_type",
        "Brand / Non-Brand": "_brand_nonbrand",
        "Sold Partner": SOLD_PROVIDER_COLUMN,
    }
    # Funnel-step mix for the trend line chart (denominator = period total of that step).
    VOL_MIX_STEP_CHOICES = {
        "Net Calls": "calls",
        "Contact Calls": "ci_contact",
        "Credit Calls": "ci_credit",
        "Sales": "sales",
    }
    VOL_MIX_STEP_YAXIS = {
        "calls": "Share of inbound calls (%)",
        "ci_contact": "Share of contact events (%)",
        "ci_credit": "Share of credit events (%)",
        "sales": "Share of orders (%)",
    }

    def _vol_inbound_frame(base: pd.DataFrame) -> pd.DataFrame:
        if base is None or base.empty or "call_date_est" not in base.columns:
            return base.iloc[0:0].copy()
        out = base.dropna(subset=["call_date_est"]).copy()
        return out.loc[top_funnel_mask(out)].copy()

    def _vol_topn_labels(s: pd.Series, top_n: int) -> pd.Series:
        s = s.fillna("(missing)").astype(str)
        if top_n <= 0:
            return s
        keep = set(s.value_counts().nlargest(top_n).index)
        return s.where(s.isin(keep), "Other")

    def _get_vol_dim_labels(df: pd.DataFrame, dim_col: str, top_n: int) -> pd.Series:
        """Return a label series for dim_col, handling the virtual '_brand_nonbrand' dimension."""
        if dim_col == "_brand_nonbrand":
            if "marketing_bucket" not in df.columns:
                return pd.Series("(missing)", index=df.index)
            brand_mask = df["marketing_bucket"].fillna("").isin(BRAND_BUCKETS)
            return pd.Series(np.where(brand_mask, "Brand", "Non-Brand"), index=df.index)
        if dim_col not in df.columns:
            return pd.Series("(missing)", index=df.index)
        return _vol_topn_labels(df[dim_col], top_n)

    def _vol_uses_sold_partner_dim(dim_col: str, dim2_col: str = "") -> bool:
        return dim_col == SOLD_PROVIDER_COLUMN or dim2_col == SOLD_PROVIDER_COLUMN

    def _vol_sold_partner_frame(base: pd.DataFrame) -> pd.DataFrame:
        if base is None:
            return pd.DataFrame()
        if base.empty or SOLD_PROVIDER_COLUMN not in base.columns:
            return base.iloc[0:0].copy()
        provider = base[SOLD_PROVIDER_COLUMN].astype("string").str.strip()
        provider_key = provider.str.lower()
        provider_mask = provider.notna() & ~provider_key.isin(SOLD_PROVIDER_MISSING_VALUES)
        if "orders" in base.columns:
            sold_mask = base["orders"].fillna(0).gt(0)
        else:
            sold_mask = pd.Series(True, index=base.index)
        return base.loc[provider_mask & sold_mask & order_revenue_mask(base)].copy()

    def _vol_funnel_step_mix_pivot(
        base: pd.DataFrame, gran: str, dim_col: str, top_n: int, step: str, dim2_col: str = ""
    ) -> pd.DataFrame:
        """Wide volumes per period × category for ``step``; convert to mix % with row-wise totals."""
        if base is None or base.empty or "call_date_est" not in base.columns:
            return pd.DataFrame()
        if dim_col not in base.columns and dim_col != "_brand_nonbrand":
            return pd.DataFrame()
        out = base.dropna(subset=["call_date_est"]).copy()
        if _vol_uses_sold_partner_dim(dim_col, dim2_col):
            w = _vol_sold_partner_frame(out)
        elif step == "sales":
            w = out.loc[order_revenue_mask(out)].copy()
        else:
            w = out.loc[top_funnel_mask(out)].copy()
        if w.empty:
            return pd.DataFrame()
        w["period"] = period_labels(w["call_date_est"], gran)
        lbl1 = _get_vol_dim_labels(w, dim_col, top_n)
        if dim2_col:
            lbl2 = _get_vol_dim_labels(w, dim2_col, top_n)
            w["_lbl"] = lbl2.astype(str) + " " + lbl1.astype(str)
        else:
            w["_lbl"] = lbl1
        if step == "calls":
            ct = w.groupby(["period", "_lbl"], sort=False).size().reset_index(name="val")
        elif step == "ci_contact":
            if "ib_contact_calls" not in w.columns:
                return pd.DataFrame()
            ct = w.groupby(["period", "_lbl"], sort=False)["ib_contact_calls"].sum().reset_index(name="val")
        elif step == "ci_credit":
            if "credit_calls_flag" not in w.columns:
                return pd.DataFrame()
            ct = w.groupby(["period", "_lbl"], sort=False)["credit_calls_flag"].sum().reset_index(name="val")
        elif step == "sales":
            if "orders" not in w.columns:
                return pd.DataFrame()
            ct = w.groupby(["period", "_lbl"], sort=False)["orders"].sum().reset_index(name="val")
        else:
            return pd.DataFrame()
        ct["period"] = pd.to_datetime(ct["period"])
        pivot = ct.pivot(index="period", columns="_lbl", values="val").fillna(0)
        return pivot.sort_index()

    v_ts = _vol_inbound_frame(df)
    vol_cmp_base = apply_filters(df_raw.copy(), use_date_range=False)
    v_cmp_in = _vol_inbound_frame(vol_cmp_base)
    v_sold_partner_ts = _vol_sold_partner_frame(df)
    v_sold_partner_cmp = _vol_sold_partner_frame(vol_cmp_base)

    if v_ts.empty and v_cmp_in.empty and v_sold_partner_ts.empty and v_sold_partner_cmp.empty:
        st.info("No inbound or sold partner calls match the current filters.")
    else:
        vol_gran = time_granularity
        vc1, vc2, vc3 = st.columns([1, 1, 1])
        with vc1:
            vol_dim_label = st.selectbox(
                "Mix dimension 1",
                list(VOL_DIM_CHOICES.keys()),
                index=0,
                key="vol_mix_dim",
            )
        with vc2:
            _dim2_options = ["All"] + list(VOL_DIM_CHOICES.keys())
            vol_dim2_label = st.selectbox(
                "Mix dimension 2",
                _dim2_options,
                index=0,
                key="vol_mix_dim2",
            )
        with vc3:
            vol_top_n = st.slider("Top categories (rest → Other)", 4, 14, 8, key="vol_top_n")

        vol_mix_step_label = st.selectbox(
            "Funnel step (mix)",
            list(VOL_MIX_STEP_CHOICES.keys()),
            index=0,
            key="vol_funnel_mix_step",
            help="Net Calls = inbound call counts. Contact Calls / Credit Calls = inbound flag sums by bucket. Sales = inbound + manual outbound order counts by bucket. If Sold Partner is selected as a mix dimension, all steps are limited to sold calls only.",
        )
        vol_mix_step = VOL_MIX_STEP_CHOICES[vol_mix_step_label]

        vol_dim_col = VOL_DIM_CHOICES[vol_dim_label]
        vol_dim2_col = "" if vol_dim2_label == "All" else VOL_DIM_CHOICES[vol_dim2_label]
        _dim_title = vol_dim_label if not vol_dim2_col else f"{vol_dim_label} × {vol_dim2_label}"

        # — Mix over time (sidebar date range): line chart by funnel step
        pivot = _vol_funnel_step_mix_pivot(df, vol_gran, vol_dim_col, vol_top_n, vol_mix_step, vol_dim2_col)
        if not pivot.empty:
            cats = list(pivot.columns)
            xdisp = pivot.index.strftime(PERIOD_FMT[vol_gran]).tolist()

            row_sum = pivot.sum(axis=1).replace(0, np.nan)
            mix_pct = pivot.div(row_sum, axis=0) * 100.0
            fig_lines = go.Figure()
            _cw = colorway_cycled(len(cats))
            for i, c in enumerate(cats):
                fig_lines.add_trace(
                    go.Scatter(
                        x=xdisp,
                        y=mix_pct[c].values,
                        mode="lines+markers",
                        name=str(c),
                        line=dict(width=2, color=_cw[i]),
                        marker=dict(size=6, color=_cw[i]),
                    )
                )
            _y_mix_title = VOL_MIX_STEP_YAXIS.get(vol_mix_step, "Share (%)")
            apply_chart_theme(
                fig_lines,
                title=layout_chart_title(f"{vol_mix_step_label} mix (%) — {_dim_title}"),
                xaxis=plotly_axis_extra("Period"),
                yaxis=plotly_axis_extra(_y_mix_title, tickformat=".0f"),
                height=420,
                margin=dict(l=52, r=20, t=52, b=100),
                legend=dict(orientation="h", yanchor="bottom", y=-0.38, x=0),
            )
            st.plotly_chart(fig_lines, **stretch_width_kwargs())
        elif not v_ts.empty:
            st.info(
                "Not enough data to chart this funnel step for the selected dimension and granularity "
                "(or a required column is missing)."
            )

        # — Custom period mix comparison (same date rules as Overview custom period)
        st.divider()
        st.subheader(
            "Custom Period Mix Comparison",
            help=(
                "Ignores the sidebar **Date Range**; uses Center, Marketing, Mover/Switcher, Tenure, and Call Type filters. "
                "Table: inbound **call mix** by category (top-N + Other) vs **Performance metric** per bucket. "
                "When **Sold Partner** is a mix dimension, the mix and bucket metrics are limited to sold calls only. "
                "**Mix / rate / interaction / total impact** columns decompose **P2 − P1** in the selected metric using "
                "call-mix weights × bucket rates (percentage metrics in **ppt**). The four impacts **sum** to total change per row and overall."
            ),
        )

        if "call_date_est" not in vol_cmp_base.columns or len(vol_cmp_base) == 0:
            st.info("No data available for period comparison with current filters.")
        elif v_cmp_in.empty:
            st.info("No inbound calls for period comparison with current filters.")
        else:
            _cmp_min = vol_cmp_base["call_date_est"].min().date()
            _cmp_max = vol_cmp_base["call_date_est"].max().date()
            _cmp_cap = _cmp_max
            if _cmp_cap < _cmp_min:
                _cmp_cap = _cmp_min
            _w = timedelta(days=6)
            _d2_end = max(_cmp_min, _cmp_cap)
            _d2_start = max(_cmp_min, _d2_end - _w)
            _d1_end = _d2_start - timedelta(days=1)
            _d1_start = max(_cmp_min, _d1_end - _w)
            if _d1_start > _d1_end:
                _d1_start = _cmp_min
                _d1_end = min(_cmp_cap, _d1_start + _w)

            _VCK1, _VCK2 = "vol_cmp_period1", "vol_cmp_period2"

            if _VCK1 not in st.session_state:
                st.session_state[_VCK1] = (_d1_start, _d1_end)
            if _VCK2 not in st.session_state:
                st.session_state[_VCK2] = (_d2_start, _d2_end)
            _rv1 = st.session_state.get(_VCK1)
            if isinstance(_rv1, (tuple, list)) and len(_rv1) == 2:
                st.session_state[_VCK1] = cmp_date_range_clamp(
                    _cmp_min, _cmp_cap, tuple(_rv1), (_d1_start, _d1_end)
                )
            _rv2 = st.session_state.get(_VCK2)
            if isinstance(_rv2, (tuple, list)) and len(_rv2) == 2:
                st.session_state[_VCK2] = cmp_date_range_clamp(
                    _cmp_min, _cmp_cap, tuple(_rv2), (_d2_start, _d2_end)
                )

            vpc_a, vpc_b = st.columns(2)
            with vpc_a:
                vol_cmp_range_1 = st.date_input(
                    "Period 1",
                    min_value=_cmp_min,
                    max_value=_cmp_cap,
                    key=_VCK1,
                )
            with vpc_b:
                vol_cmp_range_2 = st.date_input(
                    "Period 2",
                    min_value=_cmp_min,
                    max_value=_cmp_cap,
                    key=_VCK2,
                )

            _vol_metric_opts = [m for m, _ in FUNNEL_METRICS]
            _vol_metric_default_i = _vol_metric_opts.index("NC") if "NC" in _vol_metric_opts else 0
            vol_cmp_metric = st.selectbox(
                "Performance Metric",
                _vol_metric_opts,
                index=_vol_metric_default_i,
                key="vol_cmp_funnel_metric",
                help="Same definitions as the Overview funnel table. Values are computed on all calls in each mix bucket.",
            )

            def _vol_slice_period(d_all, dr):
                if len(dr) != 2:
                    return d_all.iloc[0:0]
                a, b = dr[0], dr[1]
                if a > b:
                    a, b = b, a
                m = (d_all["call_date_est"].dt.date >= a) & (d_all["call_date_est"].dt.date <= b)
                return d_all.loc[m]

            def _vol_mix_counts(sub: pd.DataFrame) -> pd.Series:
                if sub.empty or (vol_dim_col not in sub.columns and vol_dim_col != "_brand_nonbrand"):
                    return pd.Series(dtype=int)
                if _vol_uses_sold_partner_dim(vol_dim_col, vol_dim2_col):
                    sub = _vol_sold_partner_frame(sub)
                    if sub.empty:
                        return pd.Series(dtype=int)
                lbl1 = _get_vol_dim_labels(sub, vol_dim_col, vol_top_n)
                if vol_dim2_col:
                    lbl2 = _get_vol_dim_labels(sub, vol_dim2_col, vol_top_n)
                    lbl = lbl2.astype(str) + " " + lbl1.astype(str)
                else:
                    lbl = lbl1
                return lbl.value_counts()

            if len(vol_cmp_range_1) == 2 and len(vol_cmp_range_2) == 2:
                _vol_mix_base = vol_cmp_base if _vol_uses_sold_partner_dim(vol_dim_col, vol_dim2_col) else v_cmp_in
                g1 = _vol_slice_period(_vol_mix_base, vol_cmp_range_1)
                g2 = _vol_slice_period(_vol_mix_base, vol_cmp_range_2)
                c1a, c1b = sorted([vol_cmp_range_1[0], vol_cmp_range_1[1]])
                c2a, c2b = sorted([vol_cmp_range_2[0], vol_cmp_range_2[1]])
                col1 = f"P1 ({c1a:%b %d, %Y} – {c1b:%b %d, %Y})"
                col2 = f"P2 ({c2a:%b %d, %Y} – {c2b:%b %d, %Y})"

                n1 = _vol_mix_counts(g1)
                n2 = _vol_mix_counts(g2)
                union_ix = sorted(set(n1.index.astype(str)) | set(n2.index.astype(str)), key=lambda x: (x == "Other", x))
                n1a = n1.reindex(union_ix).fillna(0)
                n2a = n2.reindex(union_ix).fillna(0)
                t1 = float(n1a.sum()) or 1.0
                t2 = float(n2a.sum()) or 1.0
                p1 = (n1a / t1 * 100.0).rename("p1")
                p2 = (n2a / t2 * 100.0).rename("p2")

                _m_fmt = FUNNEL_METRIC_FMT[vol_cmp_metric]

                g1_all = _vol_slice_period(vol_cmp_base, vol_cmp_range_1)
                g2_all = _vol_slice_period(vol_cmp_base, vol_cmp_range_2)
                if _vol_uses_sold_partner_dim(vol_dim_col, vol_dim2_col):
                    g1_all = _vol_sold_partner_frame(g1_all)
                    g2_all = _vol_sold_partner_frame(g2_all)
                _raw_m1, _raw_m2 = [], []
                for cat in union_ix:
                    if (
                        (vol_dim_col not in g1_all.columns and vol_dim_col != "_brand_nonbrand")
                        or (vol_dim_col not in g2_all.columns and vol_dim_col != "_brand_nonbrand")
                        or g1_all.empty
                        or g2_all.empty
                    ):
                        _raw_m1.append(float("nan"))
                        _raw_m2.append(float("nan"))
                        continue
                    _lbl1_g1 = _get_vol_dim_labels(g1_all, vol_dim_col, vol_top_n)
                    _lbl1_g2 = _get_vol_dim_labels(g2_all, vol_dim_col, vol_top_n)
                    if vol_dim2_col:
                        _lbl2_g1 = _get_vol_dim_labels(g1_all, vol_dim2_col, vol_top_n)
                        _lbl2_g2 = _get_vol_dim_labels(g2_all, vol_dim2_col, vol_top_n)
                        l1 = _lbl2_g1.astype(str) + " " + _lbl1_g1.astype(str)
                        l2 = _lbl2_g2.astype(str) + " " + _lbl1_g2.astype(str)
                    else:
                        l1 = _lbl1_g1
                        l2 = _lbl1_g2
                    s1 = g1_all.loc[l1.eq(cat)]
                    s2 = g2_all.loc[l2.eq(cat)]
                    _raw_m1.append(compute_funnel_row(s1, vol_cmp_metric))
                    _raw_m2.append(compute_funnel_row(s2, vol_cmp_metric))

                w1f = (p1.values / 100.0).astype(float)
                w2f = (p2.values / 100.0).astype(float)
                r1a = np.array(
                    [float(x) if x is not None and not (isinstance(x, float) and pd.isna(x)) else 0.0 for x in _raw_m1],
                    dtype=float,
                )
                r2a = np.array(
                    [float(x) if x is not None and not (isinstance(x, float) and pd.isna(x)) else 0.0 for x in _raw_m2],
                    dtype=float,
                )
                dec = mix_shift_decomposition(w1f, w2f, r1a, r2a)
                _ppt = 100.0 if _m_fmt == "pct" else 1.0
                tot_ch = dec["total_change"]

                def _fmt_delta_card(v: float) -> str:
                    if _m_fmt == "pct":
                        return f"{v * _ppt:+.1f} ppt"
                    if _m_fmt == "count":
                        return f"{v:+,.1f}"
                    if _m_fmt == "dollar":
                        return f"${v:+,.2f}"
                    return f"{v:+.2f}"

                k1, k2, k3, k4 = st.columns(4)
                with k1:
                    st.metric("Mix effect", _fmt_delta_card(dec["sum_mix"]))
                with k2:
                    st.metric("Rate effect", _fmt_delta_card(dec["sum_rate"]))
                with k3:
                    st.metric("Interaction effect", _fmt_delta_card(dec["sum_inter"]))
                with k4:
                    st.metric("Total change", _fmt_delta_card(tot_ch))

                _c_met1 = "Metric P1"
                _c_met2 = "Metric P2"

                def _metric_cell_display(rv: float) -> float:
                    if _m_fmt == "pct":
                        return round(float(rv) * _ppt, 1)
                    return round(float(rv), 1)

                cmp_rows = []
                for i, cat in enumerate(union_ix):
                    p1v = float(p1.iloc[i])
                    p2v = float(p2.iloc[i])
                    r1v, r2v = float(r1a[i]), float(r2a[i])
                    mix_pct_ch = (p2v / p1v - 1.0) * 100.0 if p1v > 0 else float("nan")
                    met_ch = pct_change_vs_prior(r1v, r2v)
                    mi = float(dec["mix_e"][i]) * _ppt
                    ri = float(dec["rate_e"][i]) * _ppt
                    ii = float(dec["inter_e"][i]) * _ppt
                    ti = mi + ri + ii
                    mix_ch_s = "—" if p1v <= 0 or (isinstance(mix_pct_ch, float) and pd.isna(mix_pct_ch)) else f"{mix_pct_ch:+.1f}%"
                    met_ch_s = fmt_pct_change_str(met_ch)
                    cmp_rows.append(
                        {
                            "Category": cat,
                            "Mix P1": round(p1v, 1),
                            "Mix P2": round(p2v, 1),
                            "Percent change (mix)": mix_ch_s,
                            _c_met1: _metric_cell_display(r1v),
                            _c_met2: _metric_cell_display(r2v),
                            "Percent change (metric)": met_ch_s,
                            "Mix impact": round(mi, 1),
                            "Rate impact": round(ri, 1),
                            "Interaction impact": round(ii, 1),
                            "Total impact": round(ti, 1),
                        }
                    )

                _b1 = float(dec["blend1"])
                _b2 = float(dec["blend2"])
                _tot_mix_p1 = round(float(np.sum(w1f) * 100.0), 1)
                _tot_mix_p2 = round(float(np.sum(w2f) * 100.0), 1)
                _tot_mix_pct_ch = (
                    (_tot_mix_p2 / _tot_mix_p1 - 1.0) * 100.0 if _tot_mix_p1 > 0 else float("nan")
                )
                _tot_mix_ch_s = (
                    "—"
                    if _tot_mix_p1 <= 0 or (isinstance(_tot_mix_pct_ch, float) and pd.isna(_tot_mix_pct_ch))
                    else f"{_tot_mix_pct_ch:+.1f}%"
                )
                _tot_met_ch = pct_change_vs_prior(_b1, _b2)
                total_row = {
                    "Category": "Total",
                    "Mix P1": _tot_mix_p1,
                    "Mix P2": _tot_mix_p2,
                    "Percent change (mix)": _tot_mix_ch_s,
                    _c_met1: _metric_cell_display(_b1),
                    _c_met2: _metric_cell_display(_b2),
                    "Percent change (metric)": fmt_pct_change_str(_tot_met_ch),
                    "Mix impact": round(float(dec["sum_mix"]) * _ppt, 1),
                    "Rate impact": round(float(dec["sum_rate"]) * _ppt, 1),
                    "Interaction impact": round(float(dec["sum_inter"]) * _ppt, 1),
                    "Total impact": round(float(tot_ch) * _ppt, 1),
                }
                cmp_df = pd.DataFrame(cmp_rows + [total_row])
                _impact_cols = ["Mix impact", "Rate impact", "Interaction impact", "Total impact"]
                _pch_mix = "Percent change (mix)"
                _pch_met = "Percent change (metric)"

                def _style_vol_mix_cmp_row(row):
                    """Match Overview custom period table: :func:`theme.pct_change_cell_style`."""
                    out = pd.Series("", index=row.index)
                    pm = parse_display_pct(row.get(_pch_mix))
                    if pm is not None:
                        out[_pch_mix] = theme.pct_change_cell_style("mix_share_pct", pm)
                    pr = parse_display_pct(row.get(_pch_met))
                    if pr is not None:
                        out[_pch_met] = theme.pct_change_cell_style(vol_cmp_metric, pr)
                    for _ic in _impact_cols:
                        v = row.get(_ic)
                        try:
                            x = float(v)
                        except (TypeError, ValueError):
                            continue
                        if isinstance(x, float) and (pd.isna(x) or np.isinf(x)):
                            continue
                        out[_ic] = theme.pct_change_cell_style(vol_cmp_metric, x)
                    return out

                _fmt_cols = {c: "{:.1f}" for c in ["Mix P1", "Mix P2", _c_met1, _c_met2] + _impact_cols}
                _sty_cmp = cmp_df.style.apply(_style_vol_mix_cmp_row, axis=1).format(_fmt_cols, na_rep="—")

                st.dataframe(
                    _sty_cmp,
                    **stretch_width_kwargs(),
                    hide_index=True,
                    height=dataframe_display_height(len(cmp_df)),
                )
                table_export_row(cmp_df, "volume_mix_period_comparison.csv")

                pa = p1
                pb = p2
                _n_cat = len(union_ix)
                _vol_cmp_layout = volume_comparison_bars_layout(_n_cat)
                fig_cmp = go.Figure()
                fig_cmp.add_trace(
                    go.Bar(
                        name="Period 1",
                        x=union_ix,
                        y=pa.values,
                        marker_color=PLOT_COLORWAY[0],
                        hovertemplate="%{x}<br>" + col1 + "<br>%{y:.2f}%<extra></extra>",
                    )
                )
                fig_cmp.add_trace(
                    go.Bar(
                        name="Period 2",
                        x=union_ix,
                        y=pb.values,
                        marker_color=PLOT_COLORWAY[1],
                        hovertemplate="%{x}<br>" + col2 + "<br>%{y:.2f}%<extra></extra>",
                    )
                )
                apply_chart_theme(
                    fig_cmp,
                    title=layout_chart_title(f"Mix Comparison — {_dim_title} (% of inbound calls)"),
                    barmode="group",
                    xaxis=plotly_axis_extra(
                        _dim_title,
                        tickangle=-28,
                        automargin=True,
                    ),
                    yaxis=plotly_axis_extra("Share (%)", tickformat=".1f"),
                    **_vol_cmp_layout,
                )
                st.plotly_chart(fig_cmp, **stretch_width_kwargs())

                _y1 = [float(x) if x is not None and not (isinstance(x, float) and pd.isna(x)) else float("nan") for x in _raw_m1]
                _y2 = [float(x) if x is not None and not (isinstance(x, float) and pd.isna(x)) else float("nan") for x in _raw_m2]
                _ht1, _ht2, _ytf, _ytp, _yts = funnel_metric_bar_hover_and_ticks(_m_fmt)

                fig_m_cmp = go.Figure()
                fig_m_cmp.add_trace(
                    go.Bar(
                        name="Period 1",
                        x=union_ix,
                        y=_y1,
                        marker_color=PLOT_COLORWAY[0],
                        hovertemplate=_ht1,
                    )
                )
                fig_m_cmp.add_trace(
                    go.Bar(
                        name="Period 2",
                        x=union_ix,
                        y=_y2,
                        marker_color=PLOT_COLORWAY[1],
                        hovertemplate=_ht2,
                    )
                )
                apply_chart_theme(
                    fig_m_cmp,
                    title=layout_chart_title(f"{vol_cmp_metric} by {_dim_title} (P1 vs P2)"),
                    barmode="group",
                    xaxis=plotly_axis_extra(
                        _dim_title,
                        tickangle=-28,
                        automargin=True,
                    ),
                    yaxis_tickformat=_ytf,
                    yaxis_tickprefix=_ytp,
                    yaxis_ticksuffix=_yts,
                    yaxis_title=vol_cmp_metric,
                    **_vol_cmp_layout,
                )
                st.plotly_chart(fig_m_cmp, **stretch_width_kwargs())

                _eff_unit = "ppt" if _m_fmt == "pct" else str(_m_fmt)
                _y_title = f"Effect ({_eff_unit})"
                _per_tot = (dec["mix_e"] + dec["rate_e"] + dec["inter_e"]) * _ppt
                _x_dec = list(union_ix) + ["Total"]
                _n_x = len(_x_dec)
                _vol_dec_layout = volume_comparison_bars_layout(_n_x)
                _ym = np.concatenate([dec["mix_e"] * _ppt, [dec["sum_mix"] * _ppt]])
                _yr = np.concatenate([dec["rate_e"] * _ppt, [dec["sum_rate"] * _ppt]])
                _yi = np.concatenate([dec["inter_e"] * _ppt, [dec["sum_inter"] * _ppt]])
                _yt = np.concatenate([_per_tot, [float(tot_ch) * _ppt]])
                _c_mix = "#22d3c8"
                _c_rate = "#3d8ef8"
                _c_int = "#94a3b8" if theme.is_light_theme() else "#64748b"
                _c_tot = "#a78bfa"
                _show_interaction = st.toggle("Show interaction impact", value=True, key="vol_show_interaction")
                fig_dec = go.Figure()
                fig_dec.add_trace(
                    go.Bar(
                        name="Mix impact",
                        x=_x_dec,
                        y=_ym,
                        marker_color=_c_mix,
                        hovertemplate="%{x}<br>mix %{y:.1f}<extra></extra>",
                    )
                )
                fig_dec.add_trace(
                    go.Bar(
                        name="Rate impact",
                        x=_x_dec,
                        y=_yr,
                        marker_color=_c_rate,
                        hovertemplate="%{x}<br>rate %{y:.1f}<extra></extra>",
                    )
                )
                if _show_interaction:
                    fig_dec.add_trace(
                        go.Bar(
                            name="Interaction impact",
                            x=_x_dec,
                            y=_yi,
                            marker_color=_c_int,
                            hovertemplate="%{x}<br>interaction %{y:.1f}<extra></extra>",
                        )
                    )
                fig_dec.add_trace(
                    go.Bar(
                        name="Total impact",
                        x=_x_dec,
                        y=_yt,
                        marker_color=_c_tot,
                        hovertemplate="%{x}<br>total %{y:.1f}<extra></extra>",
                    )
                )
                _dec_title = f"{vol_cmp_metric} change decomposition: mix vs. rate effects"
                apply_chart_theme(
                    fig_dec,
                    title=layout_chart_title(_dec_title),
                    barmode="group",
                    xaxis=plotly_axis_extra(_dim_title, tickangle=-28, automargin=True),
                    yaxis=plotly_axis_extra(_y_title, tickformat=".1f"),
                    **{**_vol_dec_layout, "legend": dict(orientation="h", yanchor="top", y=1.0, x=0, xanchor="left")},
                )
                fig_dec.add_hline(
                    y=0,
                    line_dash="dash",
                    line_color=chart_hline_reference(),
                    layer="below",
                )
                st.plotly_chart(fig_dec, **stretch_width_kwargs())
            else:
                st.info("Select a full start and end date for each period.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB — AGENT LEVEL
# ══════════════════════════════════════════════════════════════════════════════
with tab_agent:

    st.subheader(
        "Agent Level Performance",
        help=(
            "One row per agent. All sidebar filters apply. "
            "GCV metrics are per-call averages. Rates are computed from calls in the filtered date range."
        ),
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

        _hist_line, _ht = chart_hist_stroke_and_title()
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
                title=layout_chart_title("Net conversion × agents", size=14),
                xaxis_tickformat=".1%",
                xaxis_title="Net conversion",
                yaxis_title="Agents",
                height=260,
                margin=dict(l=44, r=20, t=40, b=44),
            )
            st.plotly_chart(fig_nc, **stretch_width_kwargs())

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
                title=layout_chart_title("Revenue per call × agents", size=14),
                xaxis_tickformat="$,.0f",
                xaxis_title="Revenue per call",
                yaxis_title="Agents",
                height=260,
                margin=dict(l=44, r=20, t=40, b=44),
            )
            st.plotly_chart(fig_rc, **stretch_width_kwargs())

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
            **stretch_width_kwargs(),
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
        df = remove_test_center_locations(df)
        df = normalize_sold_provider_column(df)
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
    max_post_selectable = max_post_date
    if max_post_selectable < min_post_date:
        max_post_selectable = min_post_date

    lift_date_col1, lift_date_col2 = st.columns(2)
    with lift_date_col1:
        lift_start_date = st.date_input(
            "Post Period From",
            value=min_post_date,
            min_value=min_post_date,
            max_value=max_post_selectable,
            key="lift_start_date",
        )
    with lift_date_col2:
        lift_end_date = st.date_input(
            "Post Period To",
            value=max_post_selectable,
            min_value=min_post_date,
            max_value=max_post_selectable,
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
        if sel_sold_provider:
            if SOLD_PROVIDER_COLUMN in df.columns:
                df = df[df[SOLD_PROVIDER_COLUMN].isin(sel_sold_provider)]
            else:
                df = df.iloc[0:0]
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

    # ── Section 1: KPI cards ───────────────────────────────────────────────────
    st.subheader(f"{lift_center} — Test Period Lift Summary", help=caption_base)

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
            delta_color="inverse" if k in theme.LIFT_KPI_LOWER_IS_BETTER else "normal",
        )

    st.divider()

    # ── Section 2: Summary table ───────────────────────────────────────────────
    st.subheader(
        "Pre vs Post Summary Table",
        help=(
            "All values are weighted averages across post weeks, "
            "weighted by total post IB calls per week. "
            "Pre baseline uses the same filters as the post period."
        ),
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
            out[col] = theme.pct_change_cell_style(k, p)
        return out

    summary_tbl = pd.DataFrame(table_rows)
    styler = summary_tbl.style.apply(_style_lift_summary_row, axis=1)
    st.dataframe(
        styler,
        **stretch_width_kwargs(),
        hide_index=True,
        height=dataframe_display_height(len(summary_tbl)),
    )
    table_export_row(summary_tbl, "arcadia_vs_atom_summary.csv")

    st.divider()

    # ── Section 3: Trend chart ─────────────────────────────────────────────────
    st.subheader(
        "Trend Over Time",
        help=(
            "Solid lines = Arcadia, dashed = Atom. "
            "Use 'View' to plot raw KPI values, Post Δ, or Swing. "
            "Sidebar filters apply to both pre and post."
        ),
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
        apply_chart_theme(
            fig_lift,
            title=layout_chart_title(_lift_title),
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
            _hcol = chart_hline_reference()
            fig_lift.add_hline(
                y=0,
                line_dash="dash",
                line_color=_hcol,
                annotation_text="0",
                annotation_font_color=_hcol,
            )

        st.plotly_chart(fig_lift, **stretch_width_kwargs())
    else:
        st.info("No data available for the selected combination.")
