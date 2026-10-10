import copy
import math
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from data_models import DEFAULT_POLICY, DEFAULT_SCORES
from ui.pastel import apply_pastel_theme, eyebrow, intro

st.set_page_config(page_title="Grade Pilot | Course Setup", page_icon="🎓", layout="wide")

# Same look as the Grade Results page; see ui/pastel.py.
apply_pastel_theme()

st.sidebar.markdown("### 🎓 Grade Pilot")
st.sidebar.caption("Your course grade planner")
eyebrow("setup", "Course setup")
st.title("Grade Pilot")
intro("Set up your course and enter your grades in two easy steps.")

DEFAULT_CATEGORIES = [
    {"Category": "Quizzes", "Weight (%)": 15},
    {"Category": "Homework", "Weight (%)": 15},
    {"Category": "Exams", "Weight (%)": 40},
    {"Category": "Final Exam", "Weight (%)": 25},
    {"Category": "Attendance", "Weight (%)": 5},
]

STATUS_TO_LABEL = {
    "completed": "Completed", "not_taken": "Not Yet Taken",
    "missing": "Missing", "excused": "Excused",
}

DEFAULT_EDITOR_SCORES = {
    category: [
        {"Item": item["name"], "Score (%)": item["score"],
         "Status": STATUS_TO_LABEL.get(item["status"], "Not Yet Taken")}
        for item in items
    ]
    for category, items in DEFAULT_SCORES.items()
    if category != "Attendance"
}

DEFAULT_ATTENDANCE = [
    {"Day": item["name"], "Attendance": (
        "Present" if item["score"] == 100 else
        "Late" if item["score"] == 75 else "Absent"
    )}
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


def persist_value(widget_key, saved_key):
    """Store a non-widget copy so page navigation cannot clear the value."""
    st.session_state[saved_key] = copy.deepcopy(st.session_state[widget_key])


def persistent_input(widget_function, label, widget_key, default, **kwargs):
    """Restore scalar widget values from non-widget state on page re-entry."""
    saved_key = f"saved_{widget_key}"
    if saved_key not in st.session_state:
        st.session_state[saved_key] = default
    if widget_key not in st.session_state:
        st.session_state[widget_key] = st.session_state[saved_key]
    return widget_function(
        label, key=widget_key, on_change=persist_value,
        args=(widget_key, saved_key), **kwargs
    )


def edit_table(initial_rows, editor_key, saved_key, column_config):
    """Save the full table, not st.data_editor's internal edit-delta state."""
    base_key = f"{saved_key}__base"
    if saved_key not in st.session_state:
        st.session_state[saved_key] = copy.deepcopy(initial_rows)
    # st.data_editor replays the student's edits (including added and deleted
    # rows) on top of the rows it is given, on every rerun. So the editor must
    # keep the same starting rows while it is open; otherwise a deleted row is
    # deleted again on each rerun. It starts from the saved rows only when it
    # opens fresh: on the first visit, or when coming back from another page.
    if editor_key not in st.session_state or base_key not in st.session_state:
        st.session_state[base_key] = copy.deepcopy(st.session_state[saved_key])
    edited = st.data_editor(
        st.session_state[base_key],
        key=editor_key, num_rows="dynamic", hide_index=True,
        width="stretch", column_config=column_config,
    )
    # This is a complete list of rows; it survives widget cleanup on page switch.
    st.session_state[saved_key] = copy.deepcopy(edited)
    return edited



def score_input_table(initial_rows, category_name):
    """Inline score inputs avoid st.data_editor's floating numeric cell popup."""
    saved_key = f"saved_scores_{category_name}"
    if saved_key not in st.session_state:
        st.session_state[saved_key] = copy.deepcopy(initial_rows)
    rows = st.session_state[saved_key]
    header = st.columns([1.8, 0.9, 2.1, 0.55], gap="small")
    for column, heading in zip(header, ["Assignment", "Score (%)", "Status", ""]):
        column.caption(heading)

    for index, row in enumerate(rows):
        columns = st.columns([1.8, 0.9, 2.1, 0.55], gap="small", vertical_alignment="center")
        # Save each edit immediately to the non-widget state that survives navigation.
        def save_cell(i, field, key):
            value = st.session_state[key]
            row_state = st.session_state[saved_key][i]
            row_state[field] = value
            # Typing a score into a "Not Yet Taken" row means it has been graded.
            if field == "Score (%)" and str(value).strip() and row_state.get("Status") == "Not Yet Taken":
                row_state["Status"] = "Completed"
                st.session_state[f"inline_{category_name}_{i}_status"] = "Completed"

        name_key = f"inline_{category_name}_{index}_name"
        score_key = f"inline_{category_name}_{index}_score"
        status_key = f"inline_{category_name}_{index}_status"
        if name_key not in st.session_state:
            st.session_state[name_key] = str(row.get("Item") or "")
        if score_key not in st.session_state:
            value = row.get("Score (%)")
            st.session_state[score_key] = "" if blank_score(value) else str(value)
        if status_key not in st.session_state:
            st.session_state[status_key] = row.get("Status") or "Not Yet Taken"

        with columns[0]:
            st.text_input("Assignment", key=name_key, label_visibility="collapsed",
                          on_change=save_cell, args=(index, "Item", name_key))
        with columns[1]:
            # Text input looks like a regular table cell, and has no floating number editor.
            st.text_input("Score (%)", key=score_key, label_visibility="collapsed",
                          placeholder="—", on_change=save_cell,
                          args=(index, "Score (%)", score_key))
        with columns[2]:
            st.selectbox("Status", ["Completed", "Not Yet Taken", "Missing", "Excused"],
                         key=status_key, label_visibility="collapsed",
                         on_change=save_cell, args=(index, "Status", status_key))
        with columns[3]:
            if st.button("", icon=":material/close:", key=f"remove_{category_name}_{index}", help="Remove assignment"):
                rows.pop(index)
                # Rebuild row widgets from the new rows after deleting a row.
                for key in list(st.session_state.keys()):
                    if key.startswith(f"inline_{category_name}_"):
                        del st.session_state[key]
                st.rerun()

    if st.button("+ Add row", key=f"add_{category_name}"):
        rows.append({"Item": f"{category_name} {len(rows) + 1}",
                     "Score (%)": None, "Status": "Not Yet Taken"})
        st.rerun()
    return rows

st.header("1. Set up your course")
left, right = st.columns([1.35, 1], gap="large")

with left:
    st.subheader("Course details")
    course_name = persistent_input(
        st.text_input, "Course name", "setup_course_name", "",
        placeholder="e.g. Computer Science 101"
    )

    st.subheader("Grading categories")
    st.caption("Copy the category weights from your syllabus. They must total 100%.")
    categories = edit_table(
        DEFAULT_CATEGORIES, "setup_categories", "saved_setup_categories",
        {
            "Category": st.column_config.TextColumn("Category", required=False),
            "Weight (%)": st.column_config.NumberColumn(
                "Weight (%)", min_value=0, max_value=100, step=1, required=False
            ),
        },
    )
    total_weight = sum(
        row.get("Weight (%)") or 0
        for row in categories if not blank_score(row.get("Weight (%)"))
    )
    if abs(total_weight - 100) < 0.001:
        st.success("Weights total 100% — ready to go.")
    else:
        st.warning(f"Weights total {total_weight:g}%. Adjust them to reach 100%.")

with right:
    st.subheader("Grading preferences")
    st.caption("The defaults match the sample syllabus. Customize them only if needed.")
    with st.expander("Advanced grading rules", expanded=False):
        st.markdown("**Quizzes**")
        quiz_adjustment = persistent_input(
            st.checkbox, "Change quiz scores strictly above the threshold to 100%",
            "setup_quiz_adjustment", True
        )
        quiz_threshold = persistent_input(
            st.number_input, "Quiz threshold (%)", "setup_quiz_threshold", 90.0,
            min_value=0.0, max_value=100.0, disabled=not quiz_adjustment
        )
        quiz_drop = persistent_input(
            st.number_input, "Lowest quizzes to drop", "setup_quiz_drop", 1,
            min_value=0, step=1
        )
        st.markdown("**Homework**")
        homework_drop = persistent_input(
            st.number_input, "Lowest homework scores to drop", "setup_homework_drop", 2,
            min_value=0, step=1
        )
        st.markdown("**Attendance**")
        attendance_drop = persistent_input(
            st.number_input, "Attendance marks to drop (%)", "setup_attendance_drop", 5.0,
            min_value=0.0, max_value=100.0, step=1.0
        )
        st.markdown("**Final exam**")
        final_replacement = persistent_input(
            st.checkbox, "Final exam may replace the lowest exam if it helps",
            "setup_final_replacement", True
        )

    with st.expander("Letter grade cutoffs", expanded=False):
        st.caption("Minimum score for each letter grade.")
        col_a, col_b = st.columns(2)
        col_c, col_d = st.columns(2)
        with col_a:
            a_cutoff = persistent_input(st.number_input, "A minimum", "setup_a", 90.0, min_value=0.0, max_value=100.0)
        with col_b:
            b_cutoff = persistent_input(st.number_input, "B minimum", "setup_b", 80.0, min_value=0.0, max_value=100.0)
        with col_c:
            c_cutoff = persistent_input(st.number_input, "C minimum", "setup_c", 70.0, min_value=0.0, max_value=100.0)
        with col_d:
            d_cutoff = persistent_input(st.number_input, "D minimum", "setup_d", 60.0, min_value=0.0, max_value=100.0)

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
            with st.container(border=True, key=f"gp-card-scores-{index}"):
                st.subheader(category_name)
                initial = DEFAULT_EDITOR_SCORES.get(
                    category_name,
                    [{"Item": f"{category_name} 1", "Score (%)": None, "Status": "Not Yet Taken"}]
                )
                entered_scores[category_name] = score_input_table(initial, category_name)

attendance_records = []
if "Attendance" in category_names_for_scores:
    with st.expander("Attendance — Present, Late, Absent", expanded=True):
        st.caption("Present = 100% · Late = 75% · Absent = 0%. Add rows for more class days.")
        attendance_records = edit_table(
            DEFAULT_ATTENDANCE, "attendance_editor", "saved_attendance_editor",
            {
                "Day": st.column_config.TextColumn("Class day", required=False),
                "Attendance": st.column_config.SelectboxColumn(
                    "Attendance", options=list(ATTENDANCE_OPTIONS), required=False
                ),
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

# Preserve the existing data contract used by the grade and what-if pages.
policy = {
    "categories": {},
    "final_replacement": {
        "enabled": final_replacement, "target_category": "Exams", "only_if_better": True
    },
    "letter_cutoffs": {"A": a_cutoff, "B": b_cutoff, "C": c_cutoff, "D": d_cutoff},
}
for category in categories:
    name = str(category.get("Category") or "").strip()
    if not name:
        continue
    settings = DEFAULT_POLICY["categories"].get(name, {}).copy()
    settings["weight"] = category.get("Weight (%)")
    if name == "Quizzes":
        settings.update({
            "drop_lowest": quiz_drop, "drop_min_completed": quiz_drop + 1,
            "adjust_above": quiz_threshold if quiz_adjustment else None, "adjust_to": 100
        })
    elif name == "Homework":
        settings.update({"drop_lowest": homework_drop, "drop_min_completed": homework_drop + 1})
    elif name == "Attendance":
        settings["drop_percent"] = attendance_drop
    policy["categories"][name] = settings

scores = {}
errors_from_scores = []
invalid_scores = set()
for category_name, assignments in entered_scores.items():
    scores[category_name] = []
    for position, assignment in enumerate(assignments, start=1):
        status = assignment.get("Status") or "Not Yet Taken"
        raw_score = assignment.get("Score (%)")
        item_name = assignment.get("Item") or "assignment"
        try:
            score = None if blank_score(raw_score) or str(raw_score).strip() == "" else float(raw_score)
        except (TypeError, ValueError):
            score = None
            invalid_scores.add((category_name, position))
            errors_from_scores.append(f"{category_name} - {item_name}: Enter a valid number for the score.")
        if status == "Missing":
            normalized_status, score = "missing", 0
        elif status == "Excused":
            normalized_status, score = "excused", None
        elif status == "Completed":
            normalized_status = "completed"
        else:
            if score is not None:
                # Never drop a typed score silently.
                errors_from_scores.append(
                    f"{category_name} - {item_name}: Has a score but is marked Not Yet Taken. "
                    "Change the status to Completed, or clear the score."
                )
            normalized_status, score = "not_taken", None
        scores[category_name].append({
            "name": assignment.get("Item"), "score": score, "status": normalized_status
        })

if "Attendance" in category_names_for_scores:
    scores["Attendance"] = [
        {"name": row.get("Day"), "score": ATTENDANCE_OPTIONS[row["Attendance"]], "status": "completed"}
        for row in attendance_records if row.get("Attendance") in ATTENDANCE_OPTIONS
    ]

errors = list(errors_from_scores)
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
        if status == "completed" and score is None and (category_name, index) not in invalid_scores:
            errors.append(f"{category_name} - {name or index}: Completed assignments must have a score.")
        if score is not None and not (0 <= score <= 100):
            errors.append(f"{category_name} - {name or index}: Score must be between 0 and 100.")

for index, row in enumerate(attendance_records, start=1):
    if not isinstance(row.get("Day"), str) or not row["Day"].strip():
        errors.append(f"Attendance row {index}: Class day is required.")
    if row.get("Attendance") not in ATTENDANCE_OPTIONS:
        errors.append(f"Attendance row {index}: Select Present, Late, or Absent.")

if errors:
    st.error("Please fix these entries before continuing:")
    for error in errors:
        st.write(f"• {error}")
    for key in ("course_policy", "course_scores", "course_name"):
        st.session_state.pop(key, None)
else:
    st.session_state["course_policy"] = policy
    st.session_state["course_scores"] = scores
    st.session_state["course_name"] = course_name

st.divider()
if st.button("View grade results", type="primary", width="stretch", disabled=bool(errors)):
    st.switch_page("pages/grade_results.py")
