"""
Connects the course setup page (Task 1) to the grading engine (Task 2).

The setup page saves two things in st.session_state:

    course_policy = {
        "categories": {"Quizzes": {"weight": 15, "drop_lowest": 1, ...}, ...},
        "final_replacement": {"enabled": True, ...},
        "letter_cutoffs": {"A": 90, "B": 80, "C": 70, "D": 60},
    }
    course_scores = {
        "Quizzes": [{"name": "Quiz 1", "score": 80, "status": "completed"}, ...],
        ...
    }

convert_course_setup() turns those into the engine's policy and scores,
so evaluate() can be called. No grading math happens here.
"""

from logic.grade_calculator import DEFAULT_POLICY


# Category names the setup page may use for each engine category.
# Matching ignores case and extra spaces.
CATEGORY_ALIASES = {
    "quizzes": ("quizzes", "quiz"),
    "homework": ("homework", "homeworks", "hw"),
    "exams": ("exams", "exam", "midterms", "midterm"),
    "final": ("final exam", "final", "finals"),
    "attendance": ("attendance",),
}

ITEM_CATEGORIES = ("quizzes", "homework", "exams")


def find_engine_category(name):
    """Return the engine category for a setup-page name, or None."""

    key = " ".join(str(name).lower().split())

    for category, aliases in CATEGORY_ALIASES.items():
        if key in aliases:
            return category

    return None


def as_whole_number(value):
    """Turn 2.0 into 2 so the engine's whole-number checks pass."""

    if isinstance(value, float) and value.is_integer():
        return int(value)

    return value


def convert_item(item):
    """
    Convert one setup-page row into an engine score.

    Returns (score, excluded). Excused rows are excluded, matching
    the setup page's "Excused = excluded" label.
    """

    status = item.get("status")

    if status == "excused":
        return None, True
    if status == "missing":
        return "missing", False
    if status == "not_taken":
        return None, False

    return item.get("score"), False


def convert_course_setup(course_policy, course_scores):
    """
    Convert the setup page's policy and scores for the engine.

    Returns:
        ok      - True if the conversion worked
        errors  - problems that stop grading (unknown categories, ...)
        notes   - things the student should know (excused items, ...)
        policy  - engine policy (when ok)
        scores  - engine scores (when ok)
    """

    errors = []
    notes = []

    if not isinstance(course_policy, dict) or not isinstance(course_scores, dict):
        return {
            "ok": False,
            "errors": ["Set up your course and enter your grades first."],
            "notes": [],
        }

    categories = course_policy.get("categories", {})

    # Match each setup-page category to an engine category.
    names = {}

    for name in categories:
        category = find_engine_category(name)

        if category is None:
            errors.append(
                f"Grade Pilot cannot grade the category {name!r} yet. "
                "Use Quizzes, Homework, Exams, Final Exam, or Attendance."
            )
        elif category in names:
            errors.append(
                f"{names[category]!r} and {name!r} are the same kind of "
                "category. Combine them into one."
            )
        else:
            names[category] = name

    if errors:
        return {"ok": False, "errors": errors, "notes": notes}

    policy = {
        "category_names": dict(DEFAULT_POLICY["category_names"]),
        "weights": {},
        "item_counts": {"attendance": None},
        "final_replaces_lowest_exam": bool(
            course_policy.get("final_replacement", {}).get("enabled", False)
        ),
        "letter_cutoffs": dict(course_policy.get("letter_cutoffs", {})),
    }
    scores = {}

    for category, name in names.items():
        settings = categories[name]
        policy["category_names"][category] = name
        policy["weights"][category] = settings.get("weight")

        if category == "quizzes":
            threshold = settings.get("adjust_above")
            policy["quiz_cap_threshold"] = 100 if threshold is None else threshold
            policy["quiz_cap_value"] = settings.get("adjust_to", 100)

        if category in ("quizzes", "homework"):
            prefix = "quiz" if category == "quizzes" else "homework"
            policy[f"{prefix}_drop_lowest"] = as_whole_number(
                settings.get("drop_lowest", 0)
            )
            policy[f"{prefix}_drop_min_completed"] = as_whole_number(
                settings.get("drop_min_completed", 0)
            )

        if category == "attendance":
            drop_percent = settings.get("drop_percent", 0)

            if not 0 <= drop_percent < 100:
                errors.append(
                    "Attendance marks to drop must be at least 0% and "
                    "less than 100%, so at least one mark still counts."
                )

            policy["attendance_drop_fraction"] = drop_percent / 100
            policy["attendance_values"] = {
                mark: settings.get(mark, default)
                for mark, default in (
                    ("present", 100), ("late", 75), ("absent", 0)
                )
            }

    if errors:
        return {"ok": False, "errors": errors, "notes": notes}

    # Scores
    for category in ITEM_CATEGORIES:
        if category not in names:
            continue

        name = names[category]
        converted = []

        for item in course_scores.get(name, []):
            score, excluded = convert_item(item)

            if excluded:
                notes.append(
                    f"{item.get('name') or name} is excused and left out "
                    "of the grade."
                )
            else:
                converted.append(score)

        scores[category] = converted
        policy["item_counts"][category] = len(converted)

    if "final" in names:
        rows = course_scores.get(names["final"], [])

        if len(rows) > 1:
            errors.append(f"{names['final']} should have only one row.")
        elif rows:
            score, excluded = convert_item(rows[0])

            if excluded:
                policy["weights"]["final"] = 0
                notes.append(
                    f"{names['final']} is excused and left out of the grade."
                )
            else:
                scores["final"] = score

    if "attendance" in names:
        scores["attendance"] = [
            row.get("score") for row in course_scores.get(names["attendance"], [])
            if row.get("status") != "excused"
        ]

    if errors:
        return {"ok": False, "errors": errors, "notes": notes}

    return {
        "ok": True,
        "errors": [],
        "notes": notes,
        "policy": policy,
        "scores": scores,
    }
