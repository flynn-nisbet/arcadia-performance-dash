"""App-wide CSS and sidebar light/dark theme toggle (custom Arcadia themes)."""

from __future__ import annotations

import streamlit as st

# Persisted choice: first option is default (Dark) on first visit.
THEME_RADIO_KEY = "arcadia_app_theme"


def is_light_theme() -> bool:
    """True when the user selected Light in the sidebar theme control."""
    return st.session_state.get(THEME_RADIO_KEY, "Dark") == "Light"


def render_app_theme_toggle() -> None:
    """Sidebar control: Dark (default) or Light custom theme."""
    st.radio(
        "App theme",
        ["Dark", "Light"],
        horizontal=True,
        key=THEME_RADIO_KEY,
        help="Custom Arcadia styling for the page and chart exports.",
    )


def _root_variables(light: bool) -> str:
    if light:
        return """
:root {
    --bg-base:       #ffffff;
    --bg-card:       #f8fafc;
    --bg-card-alt:   #f1f5f9;
    --bg-hover:      #e2e8f0;
    --border:        #e2e8f0;
    --border-bright: #cbd5e1;
    --accent:        #3d8ef8;
    --accent-dim:    #2563c4;
    --accent-glow:   rgba(61, 142, 248, 0.18);
    --teal:          #22d3c8;
    --amber:         #f5a623;
    --rose:          #f43f5e;
    --green:         #22c55e;
    --text-primary:  #0f172a;
    --text-secondary:#475569;
    --text-muted:    #64748b;
    --radius:        8px;
    --radius-lg:     12px;
    --header-bg:     rgba(255, 255, 255, 0.97);
    --header-border: #e2e8f0;
    --scrollbar-track: #f1f5f9;
}
"""
    return """
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
    --header-bg:     rgba(13, 15, 20, 0.92);
    --header-border: #252b3a;
    --scrollbar-track: #0d0f14;
}
"""


def _shared_stylesheet(light: bool) -> str:
    st_app_bg_img = (
        ""
        if light
        else """
    background-image:
        radial-gradient(ellipse 80% 40% at 50% -10%, rgba(61,142,248,0.06) 0%, transparent 58%),
        radial-gradient(ellipse 40% 30% at 90% 80%, rgba(34,211,200,0.03) 0%, transparent 50%);
"""
    )
    metric_hover_shadow = (
        "0 0 0 1px var(--border-bright), 0 4px 16px rgba(15, 23, 42, 0.08) !important;"
        if light
        else "0 0 0 1px var(--border-bright), 0 4px 20px rgba(0,0,0,0.4) !important;"
    )
    return f"""
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Mono:wght@300;400;500&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;1,300&display=swap');

{_root_variables(light)}

html, body, [class*="css"], .stApp, .stMarkdown, p, span, div, label {{
    font-family: 'DM Sans', sans-serif !important;
    color: var(--text-primary) !important;
}}

.stApp {{
    background-color: var(--bg-base) !important;
    color: var(--text-primary) !important;
{st_app_bg_img}
}}

[data-testid="stHeader"] {{
    background-color: var(--header-bg) !important;
    border-bottom: 1px solid var(--header-border) !important;
}}
[data-testid="stToolbar"] {{
    background-color: var(--bg-base) !important;
}}

.main .block-container {{
    padding: 2rem 2.5rem 4rem !important;
    max-width: 1600px !important;
}}

[data-testid="stSidebar"] {{
    background-color: var(--bg-card) !important;
    border-right: 1px solid var(--border) !important;
}}
[data-testid="stSidebar"] .stTitle > * {{
    font-family: 'Syne', sans-serif !important;
    font-size: 1.1rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: var(--accent) !important;
}}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stMultiSelect label,
[data-testid="stSidebar"] .stDateInput label,
[data-testid="stSidebar"] .stToggle label {{
    font-size: 0.7rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: var(--text-secondary) !important;
}}

h1, h2, h3, h4 {{
    font-family: 'Syne', sans-serif !important;
    color: var(--text-primary) !important;
}}
h1 {{ font-size: 1.8rem !important; font-weight: 800 !important; letter-spacing: -0.01em !important; }}
h2 {{ font-size: 1.25rem !important; font-weight: 700 !important; letter-spacing: 0.01em !important; }}
h3 {{ font-size: 1rem !important; font-weight: 600 !important; }}

[data-testid="stHeading"] h1 {{
    color: var(--text-primary) !important;
    font-size: 2rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.02em !important;
    padding-bottom: 0.1em;
}}

.stCaptionContainer, [data-testid="stCaptionContainer"], small, caption {{
    color: var(--text-secondary) !important;
    font-size: 0.78rem !important;
    line-height: 1.5 !important;
}}

[data-testid="stMetric"] {{
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    padding: 1rem 1.25rem !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
    position: relative;
    overflow: hidden;
}}
[data-testid="stMetric"]::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--accent), var(--teal));
    opacity: 0;
    transition: opacity 0.2s;
}}
[data-testid="stMetric"]:hover {{ border-color: var(--border-bright) !important; box-shadow: {metric_hover_shadow} }}
[data-testid="stMetric"]:hover::before {{ opacity: 1; }}
[data-testid="stMetricLabel"] {{ font-size: 0.68rem !important; font-weight: 500 !important; letter-spacing: 0.1em !important; text-transform: uppercase !important; color: var(--text-secondary) !important; font-family: 'DM Sans', sans-serif !important; }}
[data-testid="stMetricValue"] {{ font-family: 'DM Mono', monospace !important; font-size: 1.5rem !important; font-weight: 500 !important; color: var(--text-primary) !important; line-height: 1.2 !important; }}
[data-testid="stMetricDelta"] {{ font-family: 'DM Mono', monospace !important; font-size: 0.75rem !important; }}
[data-testid="stMetricDelta"] svg {{ display: none !important; }}

[data-testid="stTabs"] [role="tablist"] {{ border-bottom: 1px solid var(--border) !important; gap: 0 !important; background: transparent !important; }}
[data-testid="stTabs"] [role="tab"] {{ font-family: 'Syne', sans-serif !important; font-size: 0.78rem !important; font-weight: 600 !important; letter-spacing: 0.07em !important; text-transform: uppercase !important; color: var(--text-muted) !important; padding: 0.6rem 1.25rem !important; border: none !important; border-bottom: 2px solid transparent !important; background: transparent !important; transition: color 0.15s, border-color 0.15s !important; }}
[data-testid="stTabs"] [role="tab"]:hover {{ color: var(--text-secondary) !important; border-bottom-color: var(--border-bright) !important; }}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{ color: var(--accent) !important; border-bottom-color: var(--accent) !important; background: transparent !important; }}

hr {{ border: none !important; border-top: 1px solid var(--border) !important; margin: 2rem 0 !important; }}

.stSelectbox > div > div,
.stMultiSelect > div > div,
.stTextInput > div > div > input,
.stDateInput > div > div > input {{
    background-color: var(--bg-card-alt) !important;
    border: 1px solid var(--border-bright) !important;
    border-radius: var(--radius) !important;
    color: var(--text-primary) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
    transition: border-color 0.15s !important;
}}
.stSelectbox > div > div:focus-within,
.stMultiSelect > div > div:focus-within {{ border-color: var(--accent) !important; box-shadow: 0 0 0 2px var(--accent-glow) !important; outline: none !important; }}

[data-baseweb="menu"] {{ background-color: var(--bg-card-alt) !important; border: 1px solid var(--border-bright) !important; border-radius: var(--radius) !important; }}
[data-baseweb="menu"] li {{ font-family: 'DM Sans', sans-serif !important; font-size: 0.85rem !important; color: var(--text-primary) !important; }}
[data-baseweb="menu"] li:hover {{ background-color: var(--bg-hover) !important; }}
[data-baseweb="tag"] {{ background-color: var(--accent-dim) !important; border: none !important; border-radius: 4px !important; font-size: 0.75rem !important; }}

.stRadio > div {{ gap: 0.5rem !important; background: transparent !important; border: none !important; padding: 0 !important; display: inline-flex !important; }}
.stRadio label {{ font-size: 0.75rem !important; font-weight: 500 !important; letter-spacing: 0.05em !important; text-transform: uppercase !important; padding: 0.3rem 0.85rem !important; border-radius: 6px !important; cursor: pointer !important; color: var(--text-secondary) !important; background: transparent !important; transition: color 0.15s !important; }}

[data-testid="stDataFrame"], .stDataFrame {{ border: 1px solid var(--border) !important; border-radius: var(--radius-lg) !important; overflow: hidden !important; }}
[data-testid="stDataFrame"] thead th {{ background: var(--bg-card-alt) !important; font-family: 'DM Sans', sans-serif !important; font-size: 0.68rem !important; font-weight: 600 !important; letter-spacing: 0.1em !important; text-transform: uppercase !important; color: var(--text-secondary) !important; border-bottom: 1px solid var(--border-bright) !important; padding: 0.6rem 0.8rem !important; }}
[data-testid="stDataFrame"] thead th:not(:first-child),
[data-testid="stDataFrame"] tbody td:not(:first-child) {{ text-align: right !important; }}
[data-testid="stDataFrame"] thead th:first-child,
[data-testid="stDataFrame"] tbody td:first-child {{ text-align: left !important; }}
[data-testid="stDataFrame"] tbody td {{ font-family: 'DM Mono', monospace !important; font-size: 0.82rem !important; color: var(--text-primary) !important; border-bottom: 1px solid var(--border) !important; padding: 0.5rem 0.8rem !important; background: var(--bg-card) !important; }}
[data-testid="stDataFrame"] tbody tr:hover td {{ background: var(--bg-hover) !important; }}

.stButton > button {{ background: var(--accent) !important; color: white !important; border: none !important; border-radius: var(--radius) !important; font-family: 'DM Sans', sans-serif !important; font-size: 0.8rem !important; font-weight: 600 !important; letter-spacing: 0.05em !important; padding: 0.5rem 1.25rem !important; transition: all 0.15s !important; }}
.stButton > button:hover {{ background: var(--accent-dim) !important; box-shadow: 0 4px 12px rgba(61,142,248,0.3) !important; transform: translateY(-1px) !important; }}

[data-testid="stHeading"] h2, .stMarkdown h2 {{ color: var(--text-primary) !important; font-size: 1.1rem !important; font-weight: 700 !important; letter-spacing: 0.02em !important; padding-top: 0.25rem !important; padding-bottom: 0.5rem !important; border-bottom: 1px solid var(--border) !important; margin-bottom: 1rem !important; }}

[data-testid="stInfo"] {{ background: rgba(61,142,248,0.08) !important; border: 1px solid rgba(61,142,248,0.25) !important; border-radius: var(--radius) !important; color: var(--accent) !important; font-size: 0.85rem !important; }}
[data-testid="stWarning"] {{ background: rgba(245,166,35,0.08) !important; border: 1px solid rgba(245,166,35,0.25) !important; border-radius: var(--radius) !important; color: var(--amber) !important; }}

[data-testid="stCaptionContainer"] p {{ color: var(--text-muted) !important; font-size: 0.78rem !important; font-family: 'DM Mono', monospace !important; letter-spacing: 0.05em !important; }}
.stMarkdown strong {{ color: var(--text-primary) !important; font-weight: 600 !important; }}

::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: var(--scrollbar-track); }}
::-webkit-scrollbar-thumb {{ background: var(--border-bright); border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: var(--text-muted); }}
"""


def inject_app_styles() -> None:
    """Inject global CSS after sidebar widgets (so ``is_light_theme()`` is current)."""
    st.markdown(
        f"<style>{_shared_stylesheet(is_light_theme())}</style>",
        unsafe_allow_html=True,
    )
