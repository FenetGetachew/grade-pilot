"""
Tests for the connection between the course setup page (Task 1) and
the grading engine (Task 2).
Run with:  pytest
"""

from copy import deepcopy
from pathlib import Path

import pytest

from data_models import DEFAULT_POLICY as UI_POLICY
from data_models import DEFAULT_SCORES as UI_SCORES
from logic.grade_calculator import evaluate
from logic.ui_adapter import convert_course_setup, find_engine_category


PAGES = Path(__file__).resolve().parent.parent / "pages"


def run(ui_policy=None, ui_scores=None):
    """Convert setup-page data and grade it. Returns (converted, result)."""

    converted = convert_course_setup(
        deepcopy(ui_policy or UI_POLICY), deepcopy(ui_scores or UI_SCORES)
    )

    if not converted["ok"]:
        return converted, None

    return converted, evaluate(converted["scores"], converted["policy"])


def ui_scores_with(category, changes):
    """Copy the sample scores, changing rows by position: {index: row}."""

    scores = deepcopy(UI_SCORES)
    for index, row in changes.items():
        scores[category][index] = row
    return scores


# --------------------------------------------------
# THE SAMPLE, ENTERED THROUGH THE SETUP PAGE FORMAT
# --------------------------------------------------

def test_sample_through_setup_page_format():
    converted, result = run()

    assert converted["errors"] == []
    assert result["ok"] is True
    assert result["warnings"] == []
    assert round(result["current"]["current_percentage"], 2) == 87.93
    assert result["current"]["letter_grade"] == "B"
    assert result["best_possible"]["percentage"] == pytest.approx(95.85)
    assert result["final_targets"]["targets"]["A"][
        "with_replacement"]["score"] == 88.12


def test_converted_policy_matches_the_sample_rules():
    converted, _ = run()
    policy = converted["policy"]

    assert policy["weights"] == {
        "quizzes": 15, "homework": 15, "exams": 40,
        "final": 25, "attendance": 5,
    }
    assert policy["item_counts"] == {
        "attendance": None, "quizzes": 4, "homework": 4, "exams": 2,
    }
    assert policy["quiz_cap_threshold"] == 90
    assert policy["quiz_drop_lowest"] == 1
    assert policy["homework_drop_lowest"] == 2
    assert policy["attendance_drop_fraction"] == pytest.approx(0.05)
    assert policy["final_replaces_lowest_exam"] is True
    assert converted["scores"]["quizzes"] == [80, 92, 70, None]
    assert converted["scores"]["final"] is None


# --------------------------------------------------
# THE JUDGES' CHANGES, THROUGH THE SETUP PAGE FORMAT
# --------------------------------------------------

def test_quiz_of_90_through_setup_page():
    scores = ui_scores_with("Quizzes", {
        1: {"name": "Quiz 2", "score": 90, "status": "completed"},
    })

    _, result = run(ui_scores=scores)

    assert result["current"]["current_percentage"] == pytest.approx(6520 / 75)


def test_only_two_homework_scores_through_setup_page():
    scores = ui_scores_with("Homework", {
        2: {"name": "Homework 3", "score": None, "status": "not_taken"},
        3: {"name": "Homework 4", "score": None, "status": "not_taken"},
    })

    _, result = run(ui_scores=scores)

    assert result["current"]["category_results"]["homework"]["dropped"] == []


@pytest.mark.parametrize("final, used, grade", [(95, True, 93.10), (70, False, 83.45)])
def test_final_through_setup_page(final, used, grade):
    scores = deepcopy(UI_SCORES)
    scores["Final Exam"] = [
        {"name": "Final Exam", "score": final, "status": "completed"}
    ]

    _, result = run(ui_scores=scores)

    assert result["current"]["replacement_used"] is used
    assert result["current"]["current_percentage"] == pytest.approx(grade)


# --------------------------------------------------
# STATUSES FROM THE SETUP PAGE
# --------------------------------------------------

def test_missing_counts_as_zero():
    scores = ui_scores_with("Homework", {
        2: {"name": "Homework 3", "score": 0, "status": "missing"},
    })

    converted, result = run(ui_scores=scores)

    assert converted["scores"]["homework"] == [100, 90, "missing", 50]
    messages = [line["message"] for line in result["explanation"]]
    assert "Homework item 3: marked missing, counted as 0." in messages


def test_excused_item_is_left_out():
    # Setup page: "Excused = excluded". Homework [100, 90, 50] with
    # 3 scores drops the lowest 2 -> 100.
    scores = ui_scores_with("Homework", {
        2: {"name": "Homework 3", "score": None, "status": "excused"},
    })

    converted, result = run(ui_scores=scores)

    assert converted["scores"]["homework"] == [100, 90, 50]
    assert converted["policy"]["item_counts"]["homework"] == 3
    assert converted["notes"] == [
        "Homework 3 is excused and left out of the grade."
    ]
    assert result["current"]["category_results"]["homework"][
        "average"] == pytest.approx(100)


def test_excused_final_is_left_out():
    scores = deepcopy(UI_SCORES)
    scores["Final Exam"] = [
        {"name": "Final Exam", "score": None, "status": "excused"}
    ]

    converted, result = run(ui_scores=scores)

    assert converted["policy"]["weights"]["final"] == 0
    assert converted["policy"]["final_replaces_lowest_exam"] is False
    # An excused final is not remaining work and has no targets.
    assert result["remaining"]["final"] == 0
    assert result["final_targets"]["final_counts"] is False
    assert result["final_targets"]["targets"] == {}


def test_rules_turned_off_on_setup_page():
    policy = deepcopy(UI_POLICY)
    policy["categories"]["Quizzes"]["adjust_above"] = None
    policy["categories"]["Homework"]["drop_lowest"] = 0
    policy["final_replacement"]["enabled"] = False

    converted, result = run(ui_policy=policy)

    assert converted["policy"]["quiz_cap_threshold"] == 100
    impact = {item["rule"]: item for item in result["rule_impact"]}
    assert impact["quiz_bonus"]["enabled"] is False
    assert impact["homework_drop"]["enabled"] is False
    assert impact["final_replacement"]["enabled"] is False


# --------------------------------------------------
# CATEGORY NAMES
# --------------------------------------------------

@pytest.mark.parametrize("name, category", [
    ("Quizzes", "quizzes"), (" quiz ", "quizzes"), ("HW", "homework"),
    ("Midterms", "exams"), ("Final Exam", "final"), ("final", "final"),
    ("Attendance", "attendance"), ("Labs", None),
])
def test_category_names(name, category):
    assert find_engine_category(name) == category


def test_simpler_syllabus_from_setup_page():
    policy = {
        "categories": {
            "Homework": {"weight": 30, "drop_lowest": 0, "drop_min_completed": 1},
            "Midterms": {"weight": 45},
            "Final Exam": {"weight": 25},
        },
        "final_replacement": {"enabled": False},
        "letter_cutoffs": {"A": 93, "B": 85, "C": 75, "D": 65},
    }
    scores = {
        "Homework": [
            {"name": "HW 1", "score": 90, "status": "completed"},
            {"name": "HW 2", "score": 80, "status": "completed"},
            {"name": "HW 3", "score": None, "status": "not_taken"},
        ],
        "Midterms": [
            {"name": "Midterm 1", "score": 70, "status": "completed"},
            {"name": "Midterm 2", "score": 85, "status": "completed"},
        ],
        "Final Exam": [
            {"name": "Final Exam", "score": None, "status": "not_taken"},
        ],
    }

    converted, result = run(policy, scores)

    # Homework 85, Midterms 77.5 -> (85*30 + 77.5*45) / 75 = 80.5
    assert result["current"]["current_percentage"] == pytest.approx(80.5)
    assert result["current"]["letter_grade"] == "C"
    assert converted["policy"]["category_names"]["exams"] == "Midterms"


def test_unknown_category_is_explained():
    policy = deepcopy(UI_POLICY)
    policy["categories"]["Labs"] = {"weight": 10}

    converted, result = run(ui_policy=policy)

    assert result is None
    assert converted["errors"] == [
        "Grade Pilot cannot grade the category 'Labs' yet. "
        "Use Quizzes, Homework, Exams, Final Exam, or Attendance."
    ]


def test_two_categories_of_the_same_kind():
    policy = deepcopy(UI_POLICY)
    policy["categories"]["Quiz"] = {"weight": 5}

    converted, _ = run(ui_policy=policy)

    assert "same kind of category" in converted["errors"][0]


def test_nothing_set_up_yet():
    assert convert_course_setup(None, None)["errors"] == [
        "Set up your course and enter your grades first."
    ]


# --------------------------------------------------
# BOTH REAL PAGES, RUN TOGETHER
# --------------------------------------------------

def test_setup_page_then_results_page():
    AppTest = pytest.importorskip("streamlit.testing.v1").AppTest

    setup = AppTest.from_file(str(PAGES / "course_setup.py"), default_timeout=30).run()
    assert not setup.exception

    results = AppTest.from_file(str(PAGES / "grade_results.py"), default_timeout=30)
    for key in ("course_policy", "course_scores", "course_name"):
        results.session_state[key] = setup.session_state[key]
    results.run()

    assert not results.exception
    hero = [m.value for m in results.markdown if 'class="grade-hero"' in m.value]
    assert '<div class="percent">87.93%</div>' in hero[0]
    assert ">B</div>" in hero[0]
    assert results.session_state["grade_results"]["ok"] is True
    assert any(
        "next absence will count" in warning.value
        for warning in results.warning
    )


def test_results_page_before_setup():
    AppTest = pytest.importorskip("streamlit.testing.v1").AppTest

    results = AppTest.from_file(str(PAGES / "grade_results.py"), default_timeout=30).run()

    assert not results.exception
    assert results.info[0].value == "Set up your course and enter your grades first."


@pytest.mark.parametrize("percent", [100, 150, -5])
def test_attendance_drop_percent_out_of_range(percent):
    policy = deepcopy(UI_POLICY)
    policy["categories"]["Attendance"]["drop_percent"] = percent

    converted, result = run(ui_policy=policy)

    assert result is None
    assert converted["errors"] == [
        "Attendance marks to drop must be at least 0% and less than "
        "100%, so at least one mark still counts."
    ]
