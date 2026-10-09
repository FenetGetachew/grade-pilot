import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from logic.grade_calculator import evaluate
from logic.ui_adapter import convert_course_setup

st.set_page_config(page_title="Grade Pilot | Results", page_icon="🎓", layout="wide")

from ui.styles import apply_styles
apply_styles("course")

st.sidebar.markdown("### 🎓 Grade Pilot")
st.sidebar.caption("Your course grade planner")
st.title("Your current grade")

course_policy = st.session_state.get("course_policy")
course_scores = st.session_state.get("course_scores")

if course_policy is None or course_scores is None:
    st.info("Set up your course and enter your grades first.")
    if st.button("Go to course setup →", type="primary"):
        st.switch_page("pages/course_setup.py")
    st.stop()

converted = convert_course_setup(course_policy, course_scores)

if not converted["ok"]:
    st.error("Grade Pilot can't calculate this course yet:")
    for error in converted["errors"]:
        st.write(f"• {error}")
    st.stop()

result = evaluate(converted["scores"], converted["policy"])

if not result["ok"]:
    st.error("Please fix these entries on the course setup page:")
    for error in result["errors"]:
        st.write(f"• {error}")
    st.stop()

# Shared with the what-if page (Task 3).
st.session_state["engine_policy"] = converted["policy"]
st.session_state["engine_scores"] = converted["scores"]
st.session_state["grade_results"] = result

course_name = st.session_state.get("course_name")
if course_name:
    st.markdown(f'<p class="page-intro">{course_name}</p>', unsafe_allow_html=True)

for message in result["warnings"] + converted["notes"]:
    st.warning(message)

current = result["current"]

if current["current_percentage"] is None:
    st.info("No scores entered yet. Add some grades to see your current grade.")
    st.stop()

# Headline numbers
grade_col, without_col, with_col = st.columns(3)
with grade_col:
    st.metric(
        "Current grade",
        f"{current['current_percentage']:.2f}%",
        current["letter_grade"],
        delta_color="off",
    )
with without_col:
    st.metric(
        "Without final replacement",
        f"{current['grade_without_replacement']:.2f}%",
    )
with with_col:
    with_replacement = current["grade_with_replacement"]
    st.metric(
        "With final replacement",
        "—" if with_replacement is None else f"{with_replacement:.2f}%",
    )

if current["replacement_used"]:
    st.success("The final exam replaced your lowest exam because it raised your grade.")
elif with_replacement is not None:
    st.caption("The final exam did not replace an exam, because that would not raise your grade.")

attendance = result["attendance_status"]
if attendance["warning"]:
    st.warning(attendance["message"], icon="📅")

st.divider()

# Why this grade?
left, right = st.columns([1.35, 1], gap="large")

with left:
    st.subheader("How your grade was calculated")
    names = result["policy"]["category_names"]
    sections = {}
    for line in result["explanation"]:
        sections.setdefault(line["category"], []).append(line["message"])

    for category, lines in sections.items():
        title = "Overall" if category == "overall" else names.get(category, category)
        with st.container(border=True):
            st.markdown(f"**{title}**")
            for message in lines:
                st.write(message)

with right:
    st.subheader("What each rule did")
    for item in result["rule_impact"]:
        if not item["enabled"]:
            st.caption(item["message"])
        elif item["change"] and abs(item["change"]) >= 0.005:
            st.write(f"✅ {item['message']}")
        else:
            st.write(f"➖ {item['message']}")

    st.subheader("Attendance")
    st.write(attendance["message"])

st.divider()
st.caption("What you need on the final, the best grade you can still get, and other what-if results are on the What-If page.")
