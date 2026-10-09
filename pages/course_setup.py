import math
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from data_models import DEFAULT_POLICY, DEFAULT_SCORES

st.set_page_config(page_title="Grade Pilot | Course Setup", page_icon="🎓", layout="wide")

st.markdown("""<style>
.block-container {max-width: 1450px; padding-top: 2.6rem;}
h1 {font-size: 3.4rem !important; letter-spacing: -.04em; line-height: 1.15 !important;}
h2 {font-size: 1.75rem !important;}
p, label, [data-testid="stMarkdownContainer"] {font-size: 1.08rem;}
.page-intro {font-size: 1.08rem !important;}
[data-testid="dataFrameContainer"] {background-color: var(--background-color) !important;}
.stDataEditor {background-color: var(--background-color) !important;}
[data-testid="metric-container"] {background-color: var(--background-color) !important; border: 1px solid var(--divider-color) !important; border-radius: 8px; padding: 16px;}
[data-testid="stExpander"] {background-color: var(--background-color) !important;}
</style>""", unsafe_allow_html=True)

st.sidebar.markdown("### 🎓 Grade Pilot")
st.sidebar.caption("Your course grade planner")

st.title("Grade Pilot")
st.markdown('<p class="page-intro">Set up your course and enter your grades in two easy steps.</p>', unsafe_allow_html=True)

DEFAULT_CATEGORIES = [
    {"Category": "Quizzes", "Weight (%)": 15},
    {"Category": "Homework", "Weight (%)": 15},
    {"Category": "Exams", "Weight (%)": 40},
    {"Category": "Final Exam", "Weight (%)": 25},
    {"Category": "Attendance", "Weight (%)": 5},
]
DEFAULT_EDITOR_SCORES = {
    category: [
        {"Item": item["name"], "Score (%)": item["score"],
         "Status": {"completed": "Completed", "not_taken": "Not Yet Taken", "missing": "Missing", "excused": "Excused"}.get(item["status"], "Not Yet Taken")}
        for item in items
    ]
    for category, items in DEFAULT_SCORES.items() if category != "Attendance"
}
DEFAULT_ATTENDANCE = [
    {"Day": item["name"], "Attendance": "Present" if item["score"] == 100 else "Late" if item["score"] == 75 else "Absent"}
    for item in DEFAULT_SCORES.get("Attendance", [])
]
ATTENDANCE_OPTIONS = {"Present": 100, "Late": 75, "Absent": 0}

def blank_score(value):
    if value is None:
        return True
    try:
        return bool(math.isnan(float(value)))
    except (TypeError, ValueError):
        return False

st.header("1. Set up your course")
left, right = st.columns([1.35, 1], gap="large")
with left:
    st.subheader("Course details")
    course_name = st.text_input("Course name", placeholder="e.g. Computer Science 101", key="setup_course_name")
    st.subheader("Grading categories")
    st.caption("Copy the category weights from your syllabus. They must total 100%.")
    categories = st.data_editor(
        DEFAULT_CATEGORIES, key="setup_categories", num_rows="dynamic", hide_index=True,
        width="stretch", column_config={
            "Category": st.column_config.TextColumn("Category", required=False),
            "Weight (%)": st.column_config.NumberColumn("Weight (%)", min_value=0, max_value=100, step=1, required=False),
        },
    )
    total_weight = sum(row.get("Weight (%)") or 0 for row in categories if not blank_score(row.get("Weight (%)")))
    if abs(total_weight - 100) < 0.001:
        st.success("Weights total 100% — ready to go.")
    else:
        st.warning(f"Weights total {total_weight:g}%. Adjust them to reach 100%.")
with right:
    st.subheader("Grading preferences")
    st.caption("The defaults match the sample syllabus. Customize them only if needed.")
    with st.expander("Advanced grading rules", expanded=False):
        st.markdown("**Quizzes**")
        quiz_adjustment = st.checkbox("Change quiz scores strictly above the threshold to 100%", value=True)
        quiz_threshold = st.number_input("Quiz threshold (%)", min_value=0.0, max_value=100.0, value=90.0, disabled=not quiz_adjustment)
        quiz_drop = st.number_input("Lowest quizzes to drop", min_value=0, value=1, step=1)
        st.markdown("**Homework**")
        homework_drop = st.number_input("Lowest homework scores to drop", min_value=0, value=2, step=1)
        st.markdown("**Attendance**")
        attendance_drop = st.number_input("Attendance marks to drop (%)", min_value=0.0, max_value=100.0, value=5.0, step=1.0)
        st.markdown("**Final exam**")
        final_replacement = st.checkbox("Final exam may replace the lowest exam if it helps", value=True)
    with st.expander("Letter grade cutoffs", expanded=False):
        st.caption("Minimum score for each letter grade.")
        col_a, col_b = st.columns(2)
        col_c, col_d = st.columns(2)
        with col_a:
            a_cutoff = st.number_input("A minimum", min_value=0.0, max_value=100.0, value=90.0)
        with col_b:
            b_cutoff = st.number_input("B minimum", min_value=0.0, max_value=100.0, value=80.0)
        with col_c:
            c_cutoff = st.number_input("C minimum", min_value=0.0, max_value=100.0, value=70.0)
        with col_d:
            d_cutoff = st.number_input("D minimum", min_value=0.0, max_value=100.0, value=60.0)

st.divider()
st.header("2. Enter your grades")
st.caption("Completed = graded work · Not Yet Taken = future work · Missing = zero · Excused = excluded")
entered_scores = {}
category_names_for_scores = [str(row.get("Category") or "").strip() for row in categories]
score_categories = list(dict.fromkeys(name for name in category_names_for_scores if name and name != "Attendance"))
if not score_categories:
    st.info("Add a grading category above to enter assignments.")
else:
    grade_columns = st.columns(2, gap="large")
    for index, category_name in enumerate(score_categories):
        with grade_columns[index % 2]:
            with st.container(border=True):
                st.subheader(category_name)
                initial = DEFAULT_EDITOR_SCORES.get(category_name, [{"Item": f"{category_name} 1", "Score (%)": None, "Status": "Not Yet Taken"}])
                entered_scores[category_name] = st.data_editor(
                    initial, num_rows="dynamic", hide_index=True, width="stretch",
                    key=f"scores_{category_name}",
                    column_config={
                        "Item": st.column_config.TextColumn("Assignment", required=False),
                        "Score (%)": st.column_config.NumberColumn("Score (%)", min_value=0.0, max_value=100.0, required=False),
                        "Status": st.column_config.SelectboxColumn("Status", options=["Completed", "Not Yet Taken", "Missing", "Excused"], required=False),
                    },
                )

attendance_records = []
if "Attendance" in category_names_for_scores:
    with st.expander("Attendance — Present, Late, Absent", expanded=True):
        st.caption("Present = 100% · Late = 75% · Absent = 0%. Add rows for more class days.")
        attendance_records = st.data_editor(
            DEFAULT_ATTENDANCE, num_rows="dynamic", hide_index=True, width="stretch", key="attendance_editor",
            column_config={
                "Day": st.column_config.TextColumn("Class day", required=False),
                "Attendance": st.column_config.SelectboxColumn("Attendance", options=list(ATTENDANCE_OPTIONS), required=False),
            },
        )
        valid_attendance = [row for row in attendance_records if row.get("Attendance") in ATTENDANCE_OPTIONS]
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Present", sum(row["Attendance"] == "Present" for row in valid_attendance))
        with m2:
            st.metric("Late", sum(row["Attendance"] == "Late" for row in valid_attendance))
        with m3:
            st.metric("Absent", sum(row["Attendance"] == "Absent" for row in valid_attendance))
        st.caption(f"{len(valid_attendance)} attendance records entered")

# Preserve the shared data contract for teammates.
policy = {
    "categories": {},
    "final_replacement": {"enabled": final_replacement, "target_category": "Exams", "only_if_better": True},
    "letter_cutoffs": {"A": a_cutoff, "B": b_cutoff, "C": c_cutoff, "D": d_cutoff},
}
for category in categories:
    name = str(category.get("Category") or "").strip()
    if not name:
        continue
    settings = DEFAULT_POLICY["categories"].get(name, {}).copy()
    settings["weight"] = category.get("Weight (%)")
    if name == "Quizzes":
        settings.update({"drop_lowest": quiz_drop, "drop_min_completed": quiz_drop + 1,
                         "adjust_above": quiz_threshold if quiz_adjustment else None, "adjust_to": 100})
    elif name == "Homework":
        settings.update({"drop_lowest": homework_drop, "drop_min_completed": homework_drop + 1})
    elif name == "Attendance":
        settings["drop_percent"] = attendance_drop
    policy["categories"][name] = settings

scores = {}
for category_name, assignments in entered_scores.items():
    scores[category_name] = []
    for assignment in assignments:
        status = assignment.get("Status") or "Not Yet Taken"
        raw_score = assignment.get("Score (%)")
        score = None if blank_score(raw_score) else float(raw_score)
        if status == "Missing":
            normalized_status, score = "missing", 0
        elif status == "Excused":
            normalized_status, score = "excused", None
        elif status == "Completed":
            normalized_status = "completed"
        else:
            normalized_status, score = "not_taken", None
        scores[category_name].append({"name": assignment.get("Item"), "score": score, "status": normalized_status})
        

if "Attendance" in category_names_for_scores:
    scores["Attendance"] = [
        {"name": row.get("Day"), "score": ATTENDANCE_OPTIONS[row["Attendance"]], "status": "completed"}
        for row in attendance_records if row.get("Attendance") in ATTENDANCE_OPTIONS
    ]

errors = []
names = [str(row.get("Category") or "").strip() for row in categories]
if any(not name for name in names):
    errors.append("Every grading category needs a name.")
if len(names) != len(set(names)):
    errors.append("Grading category names must be unique.")
if any(blank_score(row.get("Weight (%)")) for row in categories):
    errors.append("Every grading category needs a weight.")
if abs(total_weight - 100) > 0.001:
    errors.append("Grading category weights must total 100%.")
if not (a_cutoff > b_cutoff > c_cutoff > d_cutoff):
    errors.append("Letter cutoffs must follow A > B > C > D.")
for category_name, assignments in scores.items():
    if category_name == "Attendance":
        continue
    for index, assignment in enumerate(assignments, start=1):
        name, status, score = assignment["name"], assignment["status"], assignment["score"]
        if not isinstance(name, str) or not name.strip():
            errors.append(f"{category_name} row {index}: Enter an assignment name.")
        if status == "completed" and score is None:
            errors.append(f"{category_name} - {name or index}: Completed assignments must have a score.")
        if score is not None and not (0 <= score <= 100):
            errors.append(f"{category_name} - {name or index}: Score must be between 0 and 100.")
for index, row in enumerate(attendance_records, start=1):
    if not isinstance(row.get("Day"), str) or not row["Day"].strip():
        errors.append(f"Attendance row {index}: Class day is required.")
    if row.get("Attendance") not in ATTENDANCE_OPTIONS:
        errors.append(f"Attendance row {index}: Select Present, Late, or Absent.")

# Show errors only when something needs to be fixed.
if errors:
    st.error("Please fix these entries before continuing:")

    for error in errors:
        st.write(f"• {error}")

    for key in ("course_policy", "course_scores", "course_name"):
        st.session_state.pop(key, None)

else:
    # Save valid course data for the other pages.
    st.session_state["course_policy"] = policy
    st.session_state["course_scores"] = scores
    st.session_state["course_name"] = course_name


st.divider()

if st.button("View Grade Results →", type="primary", use_container_width=True):
    st.switch_page("pages/grade_results.py")