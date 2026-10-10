import html
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from logic.grade_calculator import evaluate, format_number
from logic.ui_adapter import convert_course_setup

st.set_page_config(page_title="Grade Pilot | Results", page_icon="🎓", layout="wide")

WHAT_IF_PAGE = Path(__file__).resolve().parent / "what_if.py"

# --------------------------------------------------
# Page styles: "playful pastel campus".
#
# These styles exist only while this page is open; Streamlit removes them
# when the student moves to another page. They only target the main area
# (never the sidebar). Streamlit sets `color-scheme: light` or `dark` on
# its app container for the active theme, so each color below uses
# light-dark(<light value>, <dark value>) and follows the theme toggle.
# --------------------------------------------------
st.markdown("""<style>
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
[data-testid="stMain"] {background: var(--gp-page); color: var(--gp-text);}
[data-testid="stHeader"] {background: var(--gp-page);}
[data-testid="stMain"] .block-container {max-width: 1320px; padding-top: 3.6rem; padding-bottom: 3rem;}
[data-testid="stMain"] h1 {color: var(--gp-ink); font-size: 3rem !important; letter-spacing: -.035em;}
[data-testid="stMain"] p, [data-testid="stMain"] li {color: var(--gp-text);}
.gp-intro {font-size: 1.15rem; color: var(--gp-muted) !important; margin: -.4rem 0 1.4rem;}
.gp-eyebrow {display: inline-flex; align-items: center; gap: .45rem; font-size: .8rem; font-weight: 700;
  letter-spacing: .12em; text-transform: uppercase; color: var(--gp-lavender-ink);
  background: var(--gp-lavender); border-radius: 999px; padding: .3rem .8rem; margin-bottom: .3rem;}
.gp-icon {display: inline-flex; width: 1.25rem; height: 1.25rem; flex: none;}
.gp-icon svg {width: 100%; height: 100%; fill: none; stroke: currentColor; stroke-width: 2;
  stroke-linecap: round; stroke-linejoin: round;}

/* Section headings */
.gp-section {display: flex; align-items: flex-start; gap: .8rem; margin: 2.2rem 0 1rem;}
.gp-section .badge {width: 2.4rem; height: 2.4rem; border-radius: 12px; display: flex; align-items: center;
  justify-content: center; background: var(--gp-lavender); color: var(--gp-lavender-ink); flex: none;}
.gp-section .title {font-size: 1.55rem; font-weight: 750; color: var(--gp-ink); line-height: 1.2;}
.gp-section .sub {font-size: .98rem; color: var(--gp-muted); margin-top: .2rem;}

/* Shared card look */
.gp-card {background: var(--gp-card); border: 1px solid var(--gp-border); border-radius: 18px;
  box-shadow: 0 6px 18px var(--gp-shadow); padding: 1.2rem 1.3rem;}

/* Current-grade hero */
.grade-hero {position: relative; overflow: hidden; display: flex; align-items: center; gap: 2rem;
  flex-wrap: wrap; padding: 1.8rem 2.2rem; border-radius: 26px; border: 1px solid var(--gp-border);
  background: linear-gradient(130deg, var(--gp-blue), var(--gp-lavender));
  box-shadow: 0 10px 28px var(--gp-shadow); margin: .2rem 0 1.1rem;}
.grade-hero::after {content: ""; position: absolute; right: -60px; top: -60px; width: 220px; height: 220px;
  border-radius: 50%; background: radial-gradient(circle, var(--gp-glow), transparent 70%);
  pointer-events: none;}
.gp-ring {position: relative; width: 148px; height: 148px; flex: none;}
.gp-ring svg {width: 148px; height: 148px; transform: rotate(-90deg);}
.gp-ring .track {stroke: var(--gp-ring-track);}
.gp-ring .bar {stroke: var(--gp-ring);}
.gp-ring .percent {position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
  font-size: 1.75rem; font-weight: 800; letter-spacing: -.03em; color: var(--gp-ink);}
.grade-hero .letter {width: 4.4rem; height: 4.4rem; border-radius: 20px; display: flex; align-items: center;
  justify-content: center; font-size: 2.3rem; font-weight: 800; color: #FFFFFF; flex: none;
  box-shadow: 0 6px 16px var(--gp-shadow);}
.grade-hero .summary {flex: 1; min-width: 260px; position: relative; z-index: 1;}
.grade-hero .headline {font-size: 1.45rem; font-weight: 750; color: var(--gp-ink); margin-bottom: .35rem;}
.grade-hero .detail {font-size: 1.05rem; line-height: 1.55; color: var(--gp-text);}
.grade-hero .note {display: inline-flex; align-items: center; gap: .4rem; margin-top: .6rem; font-size: .95rem;
  font-weight: 600; color: var(--gp-mint-ink); background: var(--gp-mint); border-radius: 999px; padding: .25rem .75rem;}

/* Replacement stat cards */
.gp-stats {display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 1rem; margin-bottom: 1rem;}
.gp-stat {display: flex; gap: .9rem; align-items: center;}
.gp-stat .tile {width: 2.6rem; height: 2.6rem; border-radius: 14px; display: flex; align-items: center;
  justify-content: center; flex: none;}
.gp-stat .label {font-size: .9rem; color: var(--gp-muted);}
.gp-stat .value {font-size: 1.35rem; font-weight: 750; color: var(--gp-ink); line-height: 1.25;}
.gp-stat .hint {font-size: .85rem; color: var(--gp-muted);}
.gp-stat.used {border-color: var(--gp-mint-ink);}

/* Accent pairs */
.acc-blue {background: var(--gp-blue); color: var(--gp-blue-ink);}
.acc-lavender {background: var(--gp-lavender); color: var(--gp-lavender-ink);}
.acc-mint {background: var(--gp-mint); color: var(--gp-mint-ink);}
.acc-yellow {background: var(--gp-yellow); color: var(--gp-yellow-ink);}
.acc-pink {background: var(--gp-pink); color: var(--gp-pink-ink);}

/* Warnings: native alerts, restyled on this page only */
.st-key-gp-alerts [data-testid="stAlertContainer"] {background: var(--gp-yellow) !important;
  border: 1px solid color-mix(in srgb, var(--gp-yellow-ink) 35%, transparent); border-radius: 16px;}
.st-key-gp-alerts [data-testid="stAlertContainer"] * {color: var(--gp-yellow-ink) !important;}

/* Category cards */
.gp-categories {display: grid; grid-template-columns: repeat(auto-fit, minmax(310px, 1fr)); gap: 1rem;}
.gp-category {border-top: 5px solid var(--accent);}
.gp-category .head {display: flex; align-items: center; gap: .75rem; margin-bottom: .7rem;}
.gp-category .tile {width: 2.5rem; height: 2.5rem; border-radius: 13px; display: flex; align-items: center;
  justify-content: center; flex: none;}
.gp-category .name {font-size: 1.2rem; font-weight: 750; color: var(--gp-ink);}
.gp-category .status {font-size: .88rem; color: var(--gp-muted);}
.gp-chips {display: flex; flex-wrap: wrap; gap: .45rem; margin-bottom: .7rem;}
.gp-chip {font-size: .88rem; font-weight: 600; border-radius: 999px; padding: .2rem .7rem;
  background: color-mix(in srgb, var(--gp-border) 55%, transparent); color: var(--gp-text);}
.gp-category ul {margin: 0; padding-left: 1.1rem;}
.gp-category li {font-size: .97rem; line-height: 1.5; margin: .15rem 0;}
.gp-category .empty {font-size: .95rem; color: var(--gp-muted);}

/* Tables */
.gp-table-wrap {overflow-x: auto;}
.gp-table, .rule-table {width: 100%; border-collapse: separate; border-spacing: 0; font-size: .98rem;}
.gp-table th, .gp-table td, .rule-table th, .rule-table td {border: none; padding: .6rem .8rem; color: var(--gp-text);}
.gp-table th, .rule-table th {font-size: .85rem; font-weight: 700; letter-spacing: .04em; text-transform: uppercase;
  color: var(--gp-muted); text-align: left; border-bottom: 1px solid var(--gp-border);}
.gp-table td, .rule-table td {border-top: 1px solid color-mix(in srgb, var(--gp-border) 70%, transparent);}
.gp-table tbody tr:first-child td, .rule-table tbody tr:first-child td {border-top: none;}
.gp-table .num, .rule-table .num {text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums;}
.gp-table th.num, .rule-table th.num {text-align: right;}
.gp-table tr.total td {font-weight: 750; color: var(--gp-ink); background: var(--gp-lavender);
  border-top: none;}
.gp-table tr.total td:first-child {border-radius: 12px 0 0 12px;}
.gp-table tr.total td:last-child {border-radius: 0 12px 12px 0;}
.gp-table .dim, .rule-table tr.off td, .dim {color: var(--gp-muted);}
.rule-table .up {color: var(--gp-mint-ink); font-weight: 700;}
.gp-table .cat {display: inline-flex; align-items: center; gap: .5rem;}
.gp-table .dot {width: .7rem; height: .7rem; border-radius: 50%; background: var(--accent); flex: none;}
.formula {margin-top: .9rem; background: var(--gp-blue); color: var(--gp-blue-ink); border-radius: 12px;
  padding: .8rem 1rem; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .98rem;
  overflow-x: auto; white-space: nowrap;}
.gp-note {font-size: .95rem; color: var(--gp-muted); margin: .6rem 0 .2rem;}

/* Two-column area and small cards */
.gp-pair {display: grid; grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr); gap: 1rem; align-items: start;}
@media (max-width: 900px) {.gp-pair {grid-template-columns: 1fr;}}
.gp-card .card-title {display: flex; align-items: center; gap: .55rem; font-size: 1.1rem; font-weight: 750;
  color: var(--gp-ink); margin-bottom: .4rem;}
.gp-card .card-title .tile {border-radius: 10px; padding: .3rem; display: flex;}
.gp-mini {display: grid; grid-template-columns: 1fr 1fr; gap: .7rem; margin: .6rem 0;}
.gp-mini > div {border-radius: 14px; padding: .7rem .9rem;}
.gp-mini .label {font-size: .85rem; opacity: .85;}
.gp-mini .value {font-size: 1.5rem; font-weight: 800;}
.gp-body {font-size: .97rem; line-height: 1.5; color: var(--gp-text);}

/* Looking ahead */
.gp-ahead {display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin-bottom: 1rem;}
.gp-pill {display: inline-block; font-size: .85rem; font-weight: 700; border-radius: 999px; padding: .15rem .65rem;}

/* Buttons on this page */
.st-key-gp-actions button {border-radius: 999px; font-weight: 650; padding: .45rem 1.2rem;}
.st-key-gp-actions button[kind="primary"] {background: var(--gp-ink); border-color: var(--gp-ink);
  color: var(--gp-page);}
.st-key-gp-actions button[kind="primary"] p {color: var(--gp-page);}
.st-key-gp-actions button[kind="secondary"] {background: var(--gp-card); border-color: var(--gp-border);}
.st-key-gp-actions button[kind="secondary"] p {color: var(--gp-ink);}
</style>""", unsafe_allow_html=True)

# Simple line icons (inline SVG, drawn in the text color of their tile).
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
}

CATEGORY_ACCENTS = {
    "quizzes": "blue", "homework": "mint", "exams": "lavender", "final": "yellow", "attendance": "pink",
}

# Solid badge colors chosen for white text in both themes.
LETTER_COLORS = {"A": "#0D7350", "B": "#3525A8", "C": "#8A6200", "D": "#B4466E", "F": "#B42318"}


def icon(name):
    return f'<span class="gp-icon"><svg viewBox="0 0 24 24" aria-hidden="true">{ICONS[name]}</svg></span>'


def text(value):
    """Escape engine text for HTML without touching quotes."""
    return html.escape(str(value), quote=False)


def section(icon_name, title, subtitle=""):
    sub = f'<div class="sub">{text(subtitle)}</div>' if subtitle else ""
    st.markdown(
        f'<div class="gp-section"><div class="badge">{icon(icon_name)}</div>'
        f'<div><div class="title">{text(title)}</div>{sub}</div></div>',
        unsafe_allow_html=True,
    )


st.sidebar.markdown("### 🎓 Grade Pilot")
st.sidebar.caption("Your course grade planner")
st.markdown(f'<div class="gp-eyebrow">{icon("final")}Grade report</div>', unsafe_allow_html=True)
st.title("Grade Pilot")

course_policy = st.session_state.get("course_policy")
course_scores = st.session_state.get("course_scores")


def back_to_setup(label="Back to course setup"):
    if st.button(label, type="primary"):
        st.switch_page("pages/course_setup.py")


if course_policy is None or course_scores is None:
    st.markdown('<p class="gp-intro">See your current grade and how it was calculated.</p>', unsafe_allow_html=True)
    st.info("Set up your course and enter your grades first.")
    back_to_setup("Go to course setup")
    st.stop()

converted = convert_course_setup(course_policy, course_scores)

if not converted["ok"]:
    st.error("Grade Pilot can't calculate this course yet:")
    for error in converted["errors"]:
        st.write(f"• {error}")
    back_to_setup()
    st.stop()

result = evaluate(converted["scores"], converted["policy"])

if not result["ok"]:
    st.error("Please fix these entries on the course setup page:")
    for error in result["errors"]:
        st.write(f"• {error}")
    back_to_setup()
    st.stop()

# Shared with the what-if page (Task 3).
st.session_state["engine_policy"] = converted["policy"]
st.session_state["engine_scores"] = converted["scores"]
st.session_state["grade_results"] = result

course_name = (st.session_state.get("course_name") or "").strip()
intro = f"Here's where your grade stands in {course_name}." if course_name else "Here's where your grade stands."
st.markdown(f'<p class="gp-intro">{text(intro)}</p>', unsafe_allow_html=True)

current = result["current"]
policy = result["policy"]
names = policy["category_names"]

if current["current_percentage"] is None:
    st.info("No scores entered yet. Add some grades on the course setup page to see your current grade.")
    back_to_setup()
    st.stop()

# Group the explanation lines by category.
sections = {}
for line in result["explanation"]:
    sections.setdefault(line["category"], []).append(line)

averages = current["category_averages_used"]
weights = policy["weights"]
order = ["quizzes", "homework", "exams", "final", "attendance"]
categories = [category for category in order if weights.get(category, 0) > 0]
attendance = result["attendance_status"]

# --------------------------------------------------
# 1. Current grade (the centerpiece)
# --------------------------------------------------
percent = current["current_percentage"]
letter = current["letter_grade"]
left_out = [line["message"] for line in sections.get("overall", []) if line["rule"] == "left_out"]

if left_out:
    detail = "Based on the work you've completed so far. " + text(left_out[0])
else:
    detail = "Every graded category has scores, so the full syllabus weights are used."

note = ""
if current["replacement_used"]:
    note = f'<div class="note">{icon("used")}Your final exam replaced your lowest exam because it raised your grade.</div>'

# Progress ring: the arc shows the engine's percentage, kept within 0-100.
radius = 60
circumference = 2 * 3.141592653589793 * radius
filled = max(0.0, min(100.0, percent)) / 100 * circumference
article = "an" if letter in ("A", "F") else "a"

st.markdown(f"""<div class="grade-hero">
  <div class="gp-ring" role="img" aria-label="Current grade {percent:.2f} percent">
    <svg viewBox="0 0 148 148">
      <circle class="track" cx="74" cy="74" r="{radius}" fill="none" stroke-width="13"/>
      <circle class="bar" cx="74" cy="74" r="{radius}" fill="none" stroke-width="13" stroke-linecap="round"
        stroke-dasharray="{filled:.2f} {circumference:.2f}"/>
    </svg>
    <div class="percent">{percent:.2f}%</div>
  </div>
  <div class="letter" style="background:{LETTER_COLORS.get(letter, '#3525A8')}">{letter}</div>
  <div class="summary">
    <div class="headline">You have {article} {letter} right now</div>
    <div class="detail">{detail}</div>
    {note}
  </div>
</div>""", unsafe_allow_html=True)

# --------------------------------------------------
# 2. Final-exam replacement: without, with, and which one is used
# --------------------------------------------------
with_replacement = current["grade_with_replacement"]
replacement_on = policy.get("final_replaces_lowest_exam", False)


def stat_card(icon_name, accent, label, value, hint, used=False):
    return (
        f'<div class="gp-card gp-stat{" used" if used else ""}" data-stat="{text(label)}" data-value="{text(value)}">'
        f'<div class="tile acc-{accent}">{icon(icon_name)}</div>'
        f'<div><div class="label">{text(label)}</div><div class="value">{text(value)}</div>'
        f'<div class="hint">{text(hint)}</div></div></div>'
    )


if not replacement_on:
    with_hint = "Not part of this syllabus."
elif with_replacement is None:
    with_hint = "Available once the final has a score."
else:
    with_hint = "Your grade if the final replaces your lowest exam."

st.markdown(
    '<div class="gp-stats">'
    + stat_card("without", "blue", "Without final replacement",
                f"{current['grade_without_replacement']:.2f}%",
                "Your grade if the final does not replace an exam.")
    + stat_card("with", "lavender", "With final replacement",
                "Not yet" if with_replacement is None else f"{with_replacement:.2f}%", with_hint)
    + stat_card("used", "mint", "Grade used",
                "With replacement" if current["replacement_used"] else "Without replacement",
                "The syllabus keeps whichever grade is higher.", used=True)
    + "</div>",
    unsafe_allow_html=True,
)

# Warnings keep their existing conditions; only their look changes here.
with st.container(key="gp-alerts"):
    for message in result["warnings"] + converted["notes"]:
        st.warning(message, icon=":material/info:")
    if attendance["warning"]:
        st.warning(attendance["message"], icon=":material/warning:")

# --------------------------------------------------
# 3. Category cards
# --------------------------------------------------
section("categories", "How your grade was calculated",
        "Each category's average after your syllabus rules, then combined using the category weights.")

category_results = current["category_results"]
remaining = result["remaining"]

cards = []
for category in categories:
    accent = CATEGORY_ACCENTS[category]
    average = averages.get(category)

    if category == "final":
        average_text = "Not taken yet" if average is None else f"Score {format_number(average)}"
        status = "Not taken yet" if average is None else "Scored"
    else:
        average_text = "No scores yet" if average is None else f"Average {format_number(average)}"
        status = ""

    if category in ("quizzes", "homework", "exams"):
        done = category_results[category]["completed_count"]
        left = remaining.get(category, 0)
        status = f"All {done} scored" if left == 0 else f"{done} scored, {left} remaining"
    elif category == "attendance":
        status = f"{attendance['recorded']} marks recorded"

    lines = sections.get(category, [])
    body = (
        "<ul>" + "".join(f"<li>{text(line['message'])}</li>" for line in lines) + "</ul>"
        if lines else '<div class="empty">No rules applied yet.</div>'
    )

    cards.append(
        f'<div class="gp-card gp-category" style="--accent: var(--gp-{accent}-ink)">'
        f'<div class="head"><div class="tile acc-{accent}">{icon(category)}</div>'
        f'<div><div class="name">{text(names.get(category, category))}</div>'
        f'<div class="status">{text(status)}</div></div></div>'
        f'<div class="gp-chips"><span class="gp-chip">Weight {weights[category]:g}%</span>'
        f'<span class="gp-chip">{text(average_text)}</span></div>'
        f"{body}</div>"
    )

st.markdown(f'<div class="gp-categories">{"".join(cards)}</div>', unsafe_allow_html=True)

# --------------------------------------------------
# 4. Detailed breakdown: weights, contributions, and the formula
# --------------------------------------------------
section("breakdown", "Detailed breakdown",
        "How much each category adds to your current grade. Categories without scores are not counted yet.")

counted = sum(weights[category] for category in categories if averages.get(category) is not None)
total_weight = sum(weights[category] for category in categories)

rows = []
for category in categories:
    accent = CATEGORY_ACCENTS[category]
    average = averages.get(category)
    name = (
        f'<span class="cat"><span class="dot" style="--accent: var(--gp-{accent}-ink)"></span>'
        f"{text(names.get(category, category))}</span>"
    )
    if average is None:
        rows.append(
            f'<tr><td>{name}</td><td class="num">{weights[category]:g}%</td>'
            f'<td class="num dim">No scores yet</td><td class="num dim">Not counted yet</td>'
            f'<td class="num dim">Not counted yet</td></tr>'
        )
    else:
        share = weights[category] / counted * 100
        contribution = average * weights[category] / counted
        rows.append(
            f'<tr><td>{name}</td><td class="num">{weights[category]:g}%</td>'
            f'<td class="num">{format_number(average)}</td><td class="num">{share:.1f}%</td>'
            f'<td class="num">{contribution:.2f}</td></tr>'
        )

rows.append(
    f'<tr class="total"><td>Total scored weight</td><td class="num">{counted:g}% of {total_weight:g}%</td>'
    f'<td class="num"></td><td class="num">100%</td><td class="num">{percent:.2f}%</td></tr>'
)

overall_notes = "".join(
    f'<div class="gp-note">{text(line["message"])}</div>'
    for line in sections.get("overall", []) if line["rule"] != "formula"
)
formula = "".join(
    f'<div class="formula">{text(line["message"])}</div>'
    for line in sections.get("overall", []) if line["rule"] == "formula"
)

st.markdown(
    '<div class="gp-card"><div class="gp-table-wrap"><table class="gp-table"><thead><tr>'
    '<th>Category</th><th class="num">Weight</th><th class="num">Average</th>'
    '<th class="num">Share of current grade</th><th class="num">Contribution</th>'
    "</tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>"
    + overall_notes + formula + "</div>",
    unsafe_allow_html=True,
)

# --------------------------------------------------
# 5. What each rule did, and attendance
# --------------------------------------------------
section("rules", "What each syllabus rule did",
        "Your grade with each rule applied, compared with the same rule turned off.")

rule_rows = []
for item in result["rule_impact"]:
    name = text(item["name"][0].upper() + item["name"][1:])
    if not item["enabled"]:
        rule_rows.append(f'<tr class="off"><td>{name}</td><td class="num" colspan="3">Not in this syllabus</td></tr>')
        continue
    change = item["change"]
    change_text = "No change" if abs(change) < 0.005 else f'<span class="up">{change:+.2f} points</span>'
    rule_rows.append(
        f'<tr><td>{name}</td><td class="num">{item["grade_without"]:.2f}%</td>'
        f'<td class="num">{item["grade_with"]:.2f}%</td><td class="num">{change_text}</td></tr>'
    )

rule_table = (
    '<div class="gp-card"><div class="gp-table-wrap"><table class="rule-table"><thead><tr><th>Rule</th>'
    '<th class="num">Without rule</th><th class="num">With rule</th><th class="num">Effect</th>'
    "</tr></thead><tbody>" + "".join(rule_rows) + "</tbody></table></div></div>"
)

if weights.get("attendance", 0) > 0:
    attendance_stats = (
        '<div class="gp-mini">'
        f'<div class="acc-pink"><div class="label">Marks recorded</div><div class="value">{attendance["recorded"]}</div></div>'
        f'<div class="acc-pink"><div class="label">Absent or late</div><div class="value">{attendance["missed"]}</div></div>'
        "</div>"
    )
else:
    attendance_stats = ""
attendance_text = (
    "See the warning near the top of the page." if attendance["warning"] else text(attendance["message"])
)
attendance_card = (
    f'<div class="gp-card"><div class="card-title"><span class="tile acc-pink">{icon("attendance")}</span>'
    f'{text(names.get("attendance", "Attendance"))}</div>{attendance_stats}'
    f'<div class="gp-body">{attendance_text}</div></div>'
)

st.markdown(f'<div class="gp-pair">{rule_table}{attendance_card}</div>', unsafe_allow_html=True)

# --------------------------------------------------
# 6. Looking ahead: targets and best possible grade
# --------------------------------------------------
section("target", "Looking ahead",
        "Where your remaining work can take you. Try specific scores in the What-If Planner.")

best = result["best_possible"]
outlook = result["letter_outlook"]
final_targets = result["final_targets"]
remaining_targets = result["remaining_targets"]["targets"]
work_left = sum(remaining.values())

ahead = []
if best["percentage"] is not None:
    ahead.append(stat_card("star", "mint", "Best possible grade",
                           f"{best['percentage']:.2f}% ({best['letter_grade']})",
                           "With 100% on everything that is left."))
if outlook.get("worst") is not None:
    ahead.append(stat_card("floor", "pink", "Lowest possible grade", f"{outlook['worst']:.2f}%",
                           "With zeros on everything that is left."))
ahead.append(stat_card("list", "blue", "Work still to come",
                       "Nothing left" if work_left == 0 else f"{work_left} item{'s' if work_left != 1 else ''}",
                       "Including the final exam." if remaining.get("final") else "No final exam left."))
st.markdown(f'<div class="gp-ahead">{"".join(ahead)}</div>', unsafe_allow_html=True)


def target_cell(target):
    if target is None:
        return '<span class="dim">Not in this syllabus</span>'
    status = target["status"]
    if status == "locked":
        return '<span class="gp-pill acc-mint">Secured</span>'
    if status == "needed":
        return f"{target['score']:.2f}%"
    if status == "needs_other_work":
        return '<span class="dim">Needs better scores elsewhere too</span>'
    return '<span class="gp-pill acc-pink">Out of reach</span>'


OUTLOOK_LABELS = {
    "secured": '<span class="gp-pill acc-mint">Secured</span>',
    "possible": '<span class="gp-pill acc-blue">Still possible</span>',
    "impossible": '<span class="gp-pill acc-pink">No longer possible</span>',
}

if outlook["letters"]:
    target_rows = []
    for target_letter, info in outlook["letters"].items():
        if final_targets.get("final_taken"):
            final_cell = '<span class="dim">Final already scored</span>'
        else:
            targets = final_targets["targets"].get(target_letter, {})
            chosen = targets.get("with_replacement") or targets.get("without_replacement")
            final_cell = target_cell(chosen)
        remaining_cell = (
            target_cell(remaining_targets[target_letter]) if target_letter in remaining_targets
            else '<span class="dim">Nothing left</span>'
        )
        target_rows.append(
            f'<tr><td><strong>{target_letter}</strong> <span class="dim">({info["cutoff"]:g}% and up)</span></td>'
            f'<td>{OUTLOOK_LABELS[info["status"]]}</td><td class="num">{final_cell}</td>'
            f'<td class="num">{remaining_cell}</td></tr>'
        )
    st.markdown(
        '<div class="gp-card"><div class="gp-table-wrap"><table class="gp-table"><thead><tr>'
        '<th>Letter</th><th>Outlook</th><th class="num">Final exam needed</th>'
        '<th class="num">Same score on all remaining work</th></tr></thead><tbody>'
        + "".join(target_rows) + "</tbody></table></div>"
        '<div class="gp-note">Final exam targets assume your other remaining work matches your current '
        "average in each category, and use the final-replacement rule when your syllabus has it.</div></div>",
        unsafe_allow_html=True,
    )

st.write("")
# A wrapping row, so the buttons keep their full labels on narrow screens.
with st.container(key="gp-actions", horizontal=True, wrap=True, gap="small"):
    back_to_setup("Edit course and grades")
    if WHAT_IF_PAGE.exists() and st.button("Open the What-If Planner"):
        st.switch_page("pages/what_if.py")

if not WHAT_IF_PAGE.exists():
    st.caption("What you need on the final, the best grade you can still get, and other what-if results are on the What-If page.")
