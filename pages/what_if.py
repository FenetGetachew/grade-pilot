from copy import deepcopy
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from logic.grade_calculator import evaluate
from logic.ui_adapter import convert_course_setup
from ui.styles import apply_styles


st.set_page_config(
    page_title="Grade Pilot | What-If",
    page_icon="🎓",
    layout="wide",
)

apply_styles("course")

st.sidebar.markdown("### 🎓 Grade Pilot")
st.sidebar.caption("Your course grade planner")

st.title("What-If Planner")
st.write("Explore what you need to reach your target grade.")


# Read the actual course information.
course_policy = st.session_state.get("course_policy")
course_scores = st.session_state.get("course_scores")

if course_policy is None or course_scores is None:
    st.info("Set up your course and enter your scores first.")

    if st.button("Go to course setup"):
        st.switch_page("pages/course_setup.py")

    st.stop()


# Convert the setup data into the grading engine's format.
converted = convert_course_setup(course_policy, course_scores)

if not converted["ok"]:
    for message in converted["errors"]:
        st.error(message)

    st.stop()


# Recalculate so this page uses the latest course information.
result = evaluate(converted["scores"], converted["policy"])

if not result["ok"]:
    for message in result["errors"]:
        st.error(message)

    st.stop()


for message in result.get("warnings", []) + converted.get("notes", []):
    st.warning(message)


def target_text(target):
    """Turn an engine target result into student-friendly text."""
    if target is None:
        return "Rule not enabled"

    status = target["status"]

    if status == "locked":
        return "0% — target secured under these assumptions"
    elif status == "needed":
        return f"{target['score']:.2f}%"
    elif status == "needs_other_work":
        return "Requires better scores on other remaining work"
    elif status == "unreachable":
        return "Not reachable"

    return "Unavailable"


# 1. Best possible grade
st.header("Your highest possible grade")

best = result["best_possible"]
current = result["current"]

left, right = st.columns(2)

with left:
    percentage = current["current_percentage"]

    if percentage is None:
        st.metric("Current grade", "No scores yet")
    else:
        st.metric(
            "Current grade",
            f"{percentage:.2f}%",
            current["letter_grade"],
            delta_color="off",
        )

with right:
    if best["percentage"] is None:
        st.metric("Best possible grade", "Unavailable")
    else:
        st.metric(
            "Best possible grade",
            f"{best['percentage']:.2f}%",
            best["letter_grade"],
            delta_color="off",
        )

st.caption(
    "The best possible result assumes 100% on all remaining work. "
    "Completed scores stay unchanged, and helpful syllabus rules apply."
)


# 2. Required final scores
st.divider()
st.header("What do you need on the final?")

st.info(
    "These targets assume your other remaining work earns your current "
    "average in its category. They are conditional predictions."
)

final_targets = result["final_targets"]

if final_targets.get("final_taken"):
    st.write("Your final already has a score.")
else:
    rows = []

    for letter, targets in final_targets.get("targets", {}).items():
        rows.append({
            "Target grade": letter,
            "Without replacement": target_text(
                targets["without_replacement"]
            ),
            "With replacement": target_text(
                targets["with_replacement"]
            ),
        })

    if rows:
        st.dataframe(rows, hide_index=True, use_container_width=True)
    else:
        st.info("No final-score targets are available for this course.")


# 3. Required scores across all remaining work
st.divider()
st.header("What if you aim for the same score on everything?")

st.caption(
    "The score below is needed on every remaining quiz, homework, "
    "exam, and final—not just the final."
)

rows = []

for letter, target in result["remaining_targets"].get("targets", {}).items():
    rows.append({
        "Target grade": letter,
        "Score on every remaining item": target_text(target),
    })

if rows:
    st.dataframe(rows, hide_index=True, use_container_width=True)
else:
    st.info("No remaining-work targets are available.")


# 4. Overall letter-grade possibilities
st.divider()
st.header("Which grades are still possible?")

st.caption(
    "Secured means you reach the cutoff even with zeros on all remaining "
    "work. Possible means sufficient future scores can reach it."
)

rows = []

for letter, outlook in result["letter_outlook"]["letters"].items():
    rows.append({
        "Target grade": letter,
        "Outlook": outlook["status"].capitalize(),
        "Explanation": outlook["message"],
    })

st.dataframe(rows, hide_index=True, use_container_width=True)


st.divider()

if st.button("Edit course and scores"):
    st.switch_page("pages/course_setup.py")
# 5. Interactive hypothetical scores
st.divider()
st.header("Try your own scores")
st.caption(
    "Enter hypothetical scores for remaining work. "
    "Your actual grades will stay unchanged."
)

scenario_scores = deepcopy(converted["scores"])
policy = result["policy"]
names = policy["category_names"]

has_remaining = False

for category in ["quizzes", "homework", "exams", "attendance"]:
    # Include items the engine knows about but that aren't in the list yet.
    values = list(scenario_scores.get(category, []))
    count = policy.get("item_counts", {}).get(category)

    if count is not None and count > len(values):
        values.extend([None] * (count - len(values)))

    scenario_scores[category] = values

    if policy["weights"].get(category, 0) <= 0:
        continue

    for index, score in enumerate(values):
        if score is None:
            has_remaining = True
            category_name = names.get(category, category.title())

            values[index] = st.number_input(
                f"{category_name} — item {index + 1} assumed score (%)",
                min_value=0.0,
                max_value=100.0,
                value=80.0,
                step=1.0,
                key=f"what_if_{category}_{index}",
            )

# Include the final if it contributes directly or through replacement.
uses_final = (
    policy["weights"].get("final", 0) > 0
    or policy.get("final_replaces_lowest_exam", False)
)

if uses_final and scenario_scores.get("final") is None:
    has_remaining = True

    scenario_scores["final"] = st.number_input(
        "Assumed final exam score (%)",
        min_value=0.0,
        max_value=100.0,
        value=80.0,
        step=1.0,
        key="what_if_final",
    )

if not has_remaining:
    st.info("There is no remaining work to simulate.")
else:
    projected = evaluate(scenario_scores, converted["policy"])

    if not projected["ok"]:
        for message in projected["errors"]:
            st.error(message)
    else:
        grade = projected["current"]

        st.subheader("Your projected course grade")

        percentage = grade["current_percentage"]

        if percentage is None:
            st.info("Not enough information to calculate a projection.")
        else:
            st.metric(
                "Projected grade",
                f"{percentage:.2f}% — {grade['letter_grade']}",
            )

            left, right = st.columns(2)

            with left:
                without = grade["grade_without_replacement"]
                st.metric(
                    "Without final replacement",
                    f"{without:.2f}%",
                )

            with right:
                with_replacement = grade["grade_with_replacement"]

                if not policy.get("final_replaces_lowest_exam", False):
                    st.metric("With final replacement", "Rule disabled")
                elif with_replacement is None:
                    st.metric("With final replacement", "Unavailable")
                else:
                    st.metric(
                        "With final replacement",
                        f"{with_replacement:.2f}%",
                    )

            if grade["replacement_used"]:
                st.success(
                    "The final replaced your lowest exam because "
                    "it improved your projected grade."
                )
            else:
                st.info(
                    "This projection uses the grade without replacement."
                )

            with st.expander("See the projected calculation"):
                for line in projected["explanation"]:
                    st.write(line["message"])