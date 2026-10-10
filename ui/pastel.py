"""
The Grade Results page's "playful pastel campus" look, for the other pages.

Visual styles only: no course logic or grade calculations. The palette
and base styles are copied from pages/grade_results.py (which keeps its
own copy), so every page looks the same.

Each page calls apply_pastel_theme() once near the top. The styles exist
only while that page is open, and they never target the sidebar.
Streamlit sets `color-scheme: light` or `dark` on its app container for
the active theme, so each color uses light-dark(<light value>, <dark
value>) and follows the theme switch.
"""

import html

import streamlit as st

PASTEL_CSS = """
.stApp {
  --gp-page: light-dark(#FFFCF5, #14152E);
  --gp-ink: light-dark(#3525A8, #DCD5FF);
  --gp-text: light-dark(#2B2760, #E8E7F6);
  --gp-muted: light-dark(#5F5B86, #B3B1D1);
  --gp-card: light-dark(#FFFFFF, #1D1F45);
  --gp-border: light-dark(#E8E2F5, #353A70);
  --gp-shadow: light-dark(rgba(53,37,168,.08), rgba(0,0,0,.35));
  --gp-blue: light-dark(#DCE9FF, #233262);   --gp-blue-ink: light-dark(#1F4AA8, #BBD0FF);
  --gp-lavender: light-dark(#EAE2FF, #2F285E); --gp-lavender-ink: light-dark(#4A32B8, #D5C9FF);
  --gp-mint: light-dark(#D9F8EA, #173F38);   --gp-mint-ink: light-dark(#0D7350, #9DE9C8);
  --gp-yellow: light-dark(#FFF0B8, #433A1B); --gp-yellow-ink: light-dark(#6E5200, #FFE18E);
  --gp-pink: light-dark(#FFDDE8, #4A2336);   --gp-pink-ink: light-dark(#A1245A, #FFBAD2);
  --gp-ring-track: light-dark(rgba(53,37,168,.13), rgba(255,255,255,.14));
  --gp-ring: light-dark(#3525A8, #B9A8FF);
  --gp-glow: light-dark(rgba(255,255,255,.38), rgba(185,168,255,.10));
}
[data-testid="stMain"] {background: var(--gp-page);}
[data-testid="stHeader"] {background: var(--gp-page);}
[data-testid="stMain"] .block-container {max-width: 1320px; padding-top: 3.6rem; padding-bottom: 3rem;}
[data-testid="stMain"] h1 {color: var(--gp-ink); font-size: 3rem !important; letter-spacing: -.035em;
  line-height: 1.15 !important;}
[data-testid="stMain"] h2 {color: var(--gp-ink); font-size: 1.55rem !important; font-weight: 750 !important;}
[data-testid="stMain"] h3 {color: var(--gp-ink); font-size: 1.22rem !important; font-weight: 700 !important;}

.gp-intro {font-size: 1.15rem; color: var(--gp-muted) !important; margin: -.4rem 0 1.4rem;}
.gp-eyebrow {display: inline-flex; align-items: center; gap: .45rem; font-size: .8rem; font-weight: 700;
  letter-spacing: .12em; text-transform: uppercase; color: var(--gp-lavender-ink);
  background: var(--gp-lavender); border-radius: 999px; padding: .3rem .8rem; margin-bottom: .3rem;}
.gp-icon {display: inline-flex; width: 1.25rem; height: 1.25rem; flex: none;}
.gp-icon svg {width: 100%; height: 100%; fill: none; stroke: currentColor; stroke-width: 2;
  stroke-linecap: round; stroke-linejoin: round;}
.gp-card {background: var(--gp-card); border: 1px solid var(--gp-border); border-radius: 18px;
  box-shadow: 0 6px 18px var(--gp-shadow); padding: 1.2rem 1.3rem;}
.acc-blue {background: var(--gp-blue); color: var(--gp-blue-ink);}
.acc-lavender {background: var(--gp-lavender); color: var(--gp-lavender-ink);}
.acc-mint {background: var(--gp-mint); color: var(--gp-mint-ink);}
.acc-yellow {background: var(--gp-yellow); color: var(--gp-yellow-ink);}
.acc-pink {background: var(--gp-pink); color: var(--gp-pink-ink);}

/* Native Streamlit pieces used across pages */
[data-testid="stMain"] [data-testid="stMetric"] {background: var(--gp-blue); border: 1px solid var(--gp-border);
  border-radius: 16px; padding: 14px 18px;}
[data-testid="stMain"] [data-testid="stMetricValue"] {color: var(--gp-ink);}
[data-testid="stMain"] [data-testid="stExpander"] details {background: var(--gp-card); border-color: var(--gp-border);
  border-radius: 16px;}

/* Bordered boxes given a key starting with "gp-card" look like Results cards */
[data-testid="stMain"] [class*="st-key-gp-card"] {background: var(--gp-card); border: 1px solid var(--gp-border) !important;
  border-radius: 18px !important; box-shadow: 0 6px 18px var(--gp-shadow);}

/* Buttons, as on the Results page: indigo pills */
[data-testid="stMain"] .stButton button {border-radius: 999px; font-weight: 650;}
[data-testid="stMain"] .stButton button[kind="primary"] {background: var(--gp-ink); border-color: var(--gp-ink);
  color: var(--gp-page);}
[data-testid="stMain"] .stButton button[kind="primary"] p {color: var(--gp-page);}
[data-testid="stMain"] .stButton button[kind="secondary"] {background: var(--gp-card); border-color: var(--gp-border);
  color: var(--gp-ink);}
[data-testid="stMain"] .stButton button[kind="secondary"] p {color: var(--gp-ink);}
[data-testid="stMain"] .stButton button:disabled {opacity: .45;}
"""

# Simple line icons (inline SVG), drawn in the text color of their tile.
ICONS = {
    "quizzes": '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/>',
    "homework": '<path d="M2 4h6a4 4 0 0 1 4 4v12a3 3 0 0 0-3-3H2z"/><path d="M22 4h-6a4 4 0 0 0-4 4v12a3 3 0 0 1 3-3h7z"/>',
    "exams": '<rect x="8" y="2" width="8" height="4" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="m9 14 2 2 4-4"/>',
    "final": '<path d="M22 10 12 5 2 10l10 5 10-5Z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/>',
    "attendance": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    "without": '<path d="m12 2 10 5-10 5L2 7Z"/><path d="m2 17 10 5 10-5"/><path d="m2 12 10 5 10-5"/>',
    "with": '<path d="M17 2l4 4-4 4"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><path d="M7 22l-4-4 4-4"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/>',
    "used": '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
    "breakdown": '<path d="M3 3h18v18H3z"/><path d="M3 9h18M3 15h18M9 3v18"/>',
    "categories": '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
    "rules": '<path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    "star": '<path d="M12 2l3.1 6.3 6.9 1-5 4.9 1.2 6.8L12 17.8 5.8 21l1.2-6.8-5-4.9 6.9-1z"/>',
    "floor": '<path d="M3 21h18"/><path d="M6 21V11M12 21V7M18 21v-6"/>',
    "list": '<path d="M9 6h12M9 12h12M9 18h12"/><circle cx="4" cy="6" r="1"/><circle cx="4" cy="12" r="1"/><circle cx="4" cy="18" r="1"/>',
    "setup": '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z"/>',
    "edit": '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/>',
    "chart": '<path d="M3 3v18h18"/><path d="m7 15 4-4 3 3 5-6"/>',
    "compass": '<circle cx="12" cy="12" r="10"/><path d="m16.2 7.8-2.1 6.3-6.3 2.1 2.1-6.3z"/>',
}


def apply_pastel_theme():
    """Add the shared pastel styles to the current page."""

    st.markdown(f"<style>{PASTEL_CSS}</style>", unsafe_allow_html=True)


def icon(name):
    """An inline SVG icon from ICONS."""

    return f'<span class="gp-icon"><svg viewBox="0 0 24 24" aria-hidden="true">{ICONS[name]}</svg></span>'


def eyebrow(icon_name, label):
    """The small rounded label shown above a page title."""

    st.markdown(
        f'<div class="gp-eyebrow">{icon(icon_name)}{html.escape(label)}</div>',
        unsafe_allow_html=True,
    )


def intro(text):
    """The muted line under a page title."""

    st.markdown(f'<p class="gp-intro">{html.escape(text, quote=False)}</p>', unsafe_allow_html=True)
