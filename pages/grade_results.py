import html
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from logic.grade_calculator import evaluate, format_number
from logic.ui_adapter import convert_course_setup

st.set_page_config(page_title="Grade Pilot | Results", page_icon="🎓", layout="wide")

# This page sets its own styles. Colors are soft tints over the theme's
# own background and text colors, so everything reads well in both the
# light and the dark theme.
st.markdown("""<style>
.block-container {max-width: 1450px; padding-top: 2rem; padding-bottom: 3rem;}
h1 {font-size: 3.1rem !important; letter-spacing: -.035em;}
h2 {font-size: 1.8rem !important;}
h3 {font-size: 1.4rem !important;}
p, label, [data-testid="stMarkdownContainer"] {font-size: 1.06rem;}
.page-intro {font-size: 1.25rem; opacity: .8; margin-bottom: 1.2rem;}
[data-testid="stMetric"] {background: rgba(128,140,160,.08); border: 1px solid rgba(128,140,160,.28);
  padding: 14px 18px; border-radius: 14px;}
[data-testid="stMetricLabel"] p {opacity: .8; font-size: 1rem;}
.grade-hero {background: linear-gradient(115deg, rgba(79,124,255,.12), rgba(155,110,255,.12));
  border: 1px solid rgba(128,140,160,.28); border-radius: 22px; padding: 2rem 2.4rem;
  display: flex; align-items: center; gap: 2.2rem; flex-wrap: wrap; margin: .4rem 0 1.4rem;}
.grade-hero .percent {font-size: 3.6rem; font-weight: 800; letter-spacing: -.04em; line-height: 1;}
.grade-hero .letter {font-size: 2.2rem; font-weight: 800; color: #fff; width: 4.2rem; height: 4.2rem;
  border-radius: 18px; display: flex; align-items: center; justify-content: center;}
.grade-hero .summary {flex: 1; min-width: 260px; font-size: 1.12rem; line-height: 1.55; opacity: .9;}
.category-stats {display: flex; gap: .6rem; flex-wrap: wrap; margin: -.2rem 0 .7rem;}
.category-stats span {background: rgba(128,140,160,.12); border: 1px solid rgba(128,140,160,.28);
  border-radius: 999px; padding: .2rem .75rem; font-size: .95rem;}
.rule-table {width: 100%; border-collapse: separate; border-spacing: 0; font-size: 1rem;
  border: 1px solid rgba(128,140,160,.28); border-radius: 12px; overflow: hidden;}
.rule-table th, .rule-table td {border: none; padding: .65rem .9rem;}
.rule-table th {background: rgba(128,140,160,.10); font-weight: 600; text-align: left; opacity: .85;}
.rule-table td {border-top: 1px solid rgba(128,140,160,.22);}
.rule-table td.num {text-align: right; white-space: nowrap;}
.rule-table tr.off td {opacity: .55;}
.formula {background: rgba(128,140,160,.08); border: 1px solid rgba(128,140,160,.28); border-radius: 12px;
  padding: .9rem 1.1rem; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 1rem;
  overflow-x: auto; white-space: nowrap;}
</style>""", unsafe_allow_html=True)

LETTER_COLORS = {
    "A": "#2f855a", "B": "#2b6cb0", "C": "#b7791f", "D": "#c05621", "F": "#c53030",
}

st.sidebar.markdown("### 🎓 Grade Pilot")
st.sidebar.caption("Your course grade planner")
st.title("Grade Pilot")

course_policy = st.session_state.get("course_policy")
course_scores = st.session_state.get("course_scores")


def back_to_setup(label="Back to course setup"):
    if st.button(label, type="primary"):
        st.switch_page("pages/course_setup.py")


if course_policy is None or course_scores is None:
    st.markdown('<p class="page-intro">See your current grade and how it was calculated.</p>', unsafe_allow_html=True)
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
st.markdown(f'<p class="page-intro">{html.escape(intro)}</p>', unsafe_allow_html=True)

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

# --------------------------------------------------
# 1. Headline grade
# --------------------------------------------------
st.header("Your current grade")

percent = current["current_percentage"]
letter = current["letter_grade"]
left_out = [line["message"] for line in sections.get("overall", []) if line["rule"] == "left_out"]

if left_out:
    summary = "<strong>Based on the work you've completed so far.</strong> " + html.escape(left_out[0])
else:
    summary = "<strong>Every graded category has scores</strong>, so the full syllabus weights are used."

if current["replacement_used"]:
    summary += "<br>Your final exam replaced your lowest exam because it raised your grade."

st.markdown(f"""<div class="grade-hero">
  <div class="percent">{percent:.2f}%</div>
  <div class="letter" style="background:{LETTER_COLORS.get(letter, '#2b6cb0')}">{letter}</div>
  <div class="summary">{summary}</div>
</div>""", unsafe_allow_html=True)

with_replacement = current["grade_with_replacement"]
without_col, with_col, used_col = st.columns(3)
with without_col:
    st.metric(
        "Without final replacement",
        f"{current['grade_without_replacement']:.2f}%",
        help="Your grade if the final exam does not replace an exam.",
    )
with with_col:
    st.metric(
        "With final replacement",
        "Not yet" if with_replacement is None else f"{with_replacement:.2f}%",
        help="Your grade if the final exam replaces your lowest exam. Available once the final has a score.",
    )
with used_col:
    st.metric(
        "Grade used",
        "With replacement" if current["replacement_used"] else "Without replacement",
        help="The syllabus keeps whichever grade is higher.",
    )

for message in result["warnings"] + converted["notes"]:
    st.warning(message)

attendance = result["attendance_status"]
if attendance["warning"]:
    st.warning(attendance["message"])

# --------------------------------------------------
# 2. How the grade was calculated
# --------------------------------------------------
st.divider()
st.header("How your grade was calculated")
st.caption("Each category's average after your syllabus rules, then combined using the category weights.")

averages = current["category_averages_used"]
weights = policy["weights"]
order = ["quizzes", "homework", "exams", "final", "attendance"]
categories = [category for category in order if weights.get(category, 0) > 0]

columns = st.columns(2, gap="large")
for index, category in enumerate(categories):
    average = averages.get(category)
    if category == "final" and average is None:
        average_text = "Not taken yet"
    elif average is None:
        average_text = "No scores yet"
    else:
        average_text = f"Average {format_number(average)}"

    with columns[index % 2]:
        with st.container(border=True):
            st.subheader(names.get(category, category))
            st.markdown(
                f'<div class="category-stats"><span>Weight {weights[category]:g}%</span>'
                f'<span>{html.escape(average_text)}</span></div>',
                unsafe_allow_html=True,
            )
            lines = sections.get(category, [])
            if lines:
                st.markdown("\n".join(f"- {line['message']}" for line in lines))
            else:
                st.caption("No rules applied yet.")

with st.container(border=True):
    st.subheader("Overall")
    for line in sections.get("overall", []):
        if line["rule"] == "formula":
            st.markdown(f'<div class="formula">{html.escape(line["message"])}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f"- {line['message']}")

# --------------------------------------------------
# 3. What each rule did, and attendance
# --------------------------------------------------
st.divider()
rules_col, attendance_col = st.columns([1.35, 1], gap="large")

with rules_col:
    st.subheader("What each rule did")
    st.caption("Your grade with each syllabus rule applied, compared with the same rule turned off.")
    rows = []
    for item in result["rule_impact"]:
        name = html.escape(item["name"][0].upper() + item["name"][1:])
        if not item["enabled"]:
            rows.append(f'<tr class="off"><td>{name}</td><td class="num" colspan="3">Not in this syllabus</td></tr>')
            continue
        change = item["change"]
        change_text = "No change" if abs(change) < 0.005 else f"{change:+.2f} points"
        rows.append(
            f'<tr><td>{name}</td><td class="num">{item["grade_without"]:.2f}%</td>'
            f'<td class="num">{item["grade_with"]:.2f}%</td><td class="num">{change_text}</td></tr>'
        )
    st.markdown(
        '<table class="rule-table"><thead><tr><th>Rule</th><th>Without rule</th>'
        '<th>With rule</th><th>Effect</th></tr></thead><tbody>'
        + "".join(rows) + "</tbody></table>",
        unsafe_allow_html=True,
    )

with attendance_col:
    st.subheader(names.get("attendance", "Attendance"))
    if weights.get("attendance", 0) > 0:
        record = st.columns(2)
        with record[0]:
            st.metric("Marks recorded", attendance["recorded"])
        with record[1]:
            st.metric("Absent or late", attendance["missed"])
    if attendance["warning"]:
        st.caption("See the warning at the top of the page.")
    else:
        st.write(attendance["message"])

st.divider()
back_to_setup("Edit course and grades")
st.caption("What you need on the final, the best grade you can still get, and other what-if results are on the What-If page.")
