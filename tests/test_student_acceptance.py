"""
Student acceptance tests: one student's journey through the real pages.

Each test drives pages/course_setup.py the way a student would (editing
table cells, changing rule settings), then opens pages/grade_results.py
and checks what is displayed against hand-calculated values.

Test names start with the checklist section, e.g. test_s5_... for
"5. Final-Exam Replacement". Run with:  pytest -v tests/test_student_acceptance.py
"""

import re
from copy import deepcopy
from pathlib import Path

import pytest

from logic.grade_calculator import evaluate

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest

ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / "pages"


# --------------------------------------------------
# HELPERS: ACT LIKE A STUDENT
# --------------------------------------------------

def row(score=None, status="Completed"):
    """One edited score row, as the browser sends it."""

    return {"Score (%)": score, "Status": status}


def not_taken():
    return {"Score (%)": None, "Status": "Not Yet Taken"}


def open_setup(edits=None, settings=None, course="CS 101"):
    """
    Open the course setup page and make the student's changes.

    edits:    {editor key: {"edited": {row: {column: value}},
                            "added": [...], "deleted": [...]}}
    settings: {widget label: value} for number inputs and checkboxes
    """

    at = AppTest.from_file(str(PAGES / "course_setup.py"), default_timeout=30)

    for key, change in (edits or {}).items():
        at.session_state[key] = {
            "edited_rows": change.get("edited", {}),
            "added_rows": change.get("added", []),
            "deleted_rows": change.get("deleted", []),
        }

    at.run()
    at.text_input[0].set_value(course)

    for label, value in (settings or {}).items():
        widgets = [w for w in at.number_input if w.label == label]
        widgets += [w for w in at.checkbox if w.label == label]
        assert widgets, f"No setting called {label!r}"
        widgets[0].set_value(value)

    at.run()
    assert not at.exception, [e.value for e in at.exception]
    return at


def open_results(setup):
    """Open the results page with whatever the setup page saved."""

    at = AppTest.from_file(str(PAGES / "grade_results.py"), default_timeout=30)

    for key in ("course_policy", "course_scores", "course_name"):
        if key in setup.session_state:
            at.session_state[key] = setup.session_state[key]

    at.run()
    assert not at.exception, [e.value for e in at.exception]
    return at


def student(edits=None, settings=None):
    """Set up the course, then open the results page."""

    setup = open_setup(edits, settings)
    return setup, open_results(setup)


def metrics(page):
    """Displayed numbers. "Current grade" is read from the headline card."""

    shown = {m.label: (m.value, m.delta) for m in page.metric}
    hero = [m.value for m in page.markdown if 'class="grade-hero"' in m.value]

    if hero:
        percent = re.search(r'class="percent">([^<]+)<', hero[0]).group(1)
        letter = re.search(r'class="letter"[^>]*>([^<]+)<', hero[0]).group(1)
        shown["Current grade"] = (percent, letter)

    return shown


def shown_text(page):
    """Every text line the results page displays."""

    parts = [m.value for m in page.markdown]
    parts += [c.value for c in page.caption]
    for elements in (page.success, page.warning, page.error, page.info):
        parts += [element.value for element in elements]
    return "\n".join(parts)


def setup_errors(setup):
    return [m.value for m in setup.markdown if m.value.startswith("• ")]


def engine(page):
    return page.session_state["grade_results"]


def edit(category, rows):
    """Edits for one score table: {row index: row dict}."""

    return {f"scores_{category}": {"edited": rows}}


def merge(*edit_sets):
    combined = {}
    for edits in edit_sets:
        combined.update(edits)
    return combined


# --------------------------------------------------
# 1. UI-TO-ENGINE INTEGRATION
# --------------------------------------------------

def test_s1_app_and_pages_launch_without_errors():
    for page in ("app.py", "pages/course_setup.py", "pages/grade_results.py"):
        at = AppTest.from_file(str(ROOT / page), default_timeout=30).run()
        assert not at.exception, page


def test_s1_ui_calls_evaluate_and_scores_reach_engine():
    _, results = student()

    assert engine(results)["ok"] is True
    scores = results.session_state["engine_scores"]
    assert scores["quizzes"] == [80, 92, 70, None]
    assert scores["homework"] == [100, 90, 80, 50]
    assert scores["exams"] == [78, 88]
    assert scores["final"] is None
    assert scores["attendance"] == [100] * 19 + [0]


def test_s1_policy_reaches_engine():
    _, results = student(settings={
        "Quiz threshold (%)": 95.0,
        "Lowest homework scores to drop": 1,
        "B minimum": 85.0,
    })

    policy = results.session_state["engine_policy"]
    assert policy["weights"] == {
        "quizzes": 15, "homework": 15, "exams": 40, "final": 25,
        "attendance": 5,
    }
    assert policy["quiz_cap_threshold"] == 95
    assert policy["homework_drop_lowest"] == 1
    assert policy["homework_drop_min_completed"] == 2
    assert policy["letter_cutoffs"]["B"] == 85
    assert policy["attendance_drop_fraction"] == pytest.approx(0.05)
    assert policy["final_replaces_lowest_exam"] is True


def test_s1_displayed_results_match_engine():
    _, results = student()
    current = engine(results)["current"]

    assert metrics(results)["Current grade"] == (
        f"{current['current_percentage']:.2f}%", current["letter_grade"]
    )
    assert metrics(results)["Current grade"] == ("87.93%", "B")


def test_s1_changing_a_score_updates_results():
    _, before = student()
    _, after = student(edit("Quizzes", {1: row(90)}))

    assert metrics(before)["Current grade"][0] == "87.93%"
    assert metrics(after)["Current grade"][0] == "86.93%"


@pytest.mark.parametrize("bad", [-1, 101])
def test_s1_invalid_score_does_not_crash(bad):
    setup, results = student(edit("Quizzes", {0: row(bad)}))

    assert "• Quizzes - Quiz 1: Score must be between 0 and 100." in setup_errors(setup)
    assert results.info[0].value == "Set up your course and enter your grades first."


def test_s1_engine_error_is_shown_clearly():
    # The setup page allows 100%, but at least one mark must count.
    _, results = student(settings={"Attendance marks to drop (%)": 100.0})

    assert results.error[0].value == "Grade Pilot can't calculate this course yet:"
    assert (
        "• Attendance marks to drop must be at least 0% and less than "
        "100%, so at least one mark still counts."
    ) in shown_text(results)


def test_s1_unknown_category_is_shown_clearly():
    setup, results = student({
        "setup_categories": {
            "edited": {4: {"Category": "Labs"}},
        },
    })

    assert results.error[0].value == "Grade Pilot can't calculate this course yet:"
    assert "cannot grade the category 'Labs'" in shown_text(results)
    assert results.button[0].label == "← Back to course setup"


# --------------------------------------------------
# 2. SCORE INPUT AND VALIDATION
# --------------------------------------------------

@pytest.mark.parametrize("quiz2, grade", [
    (0, "84.93%"),       # quizzes [80, 0, 70] drop 0 -> 75
    (55.5, "84.93%"),    # quizzes [80, 55.5, 70] drop 55.5 -> 75
    (90, "86.93%"),      # exactly 90: no bonus -> 85
    (90.01, "87.93%"),   # just above 90: counts as 100 -> 90
    (100, "87.93%"),
])
def test_s2_valid_and_boundary_scores(quiz2, grade):
    _, results = student(edit("Quizzes", {1: row(quiz2)}))

    assert metrics(results)["Current grade"][0] == grade


def test_s2_blank_is_none_and_zero_is_real():
    _, results = student(edit("Exams", {0: row(0)}))

    scores = results.session_state["engine_scores"]
    assert scores["quizzes"][3] is None        # Quiz 4 not yet taken
    assert scores["exams"] == [0, 88]          # a real 0 is kept
    # exams 44 -> (1350 + 1425 + 1760 + 500) / 75 = 67.13
    assert metrics(results)["Current grade"] == ("67.13%", "D")


def test_s2_completed_without_score_is_rejected():
    setup, _ = student(edit("Quizzes", {3: row(None, "Completed")}))

    assert "• Quizzes - Quiz 4: Completed assignments must have a score." in setup_errors(setup)


@pytest.mark.xfail(
    strict=True,
    reason="Known issue I-1 (TEST_REPORT.md): the setup page ignores a "
    "score whose Status is left blank.",
)
def test_s2_score_typed_but_status_left_not_taken():
    # A student adds a new quiz row with a score but leaves the status
    # blank. The setup page treats a blank status as "Not Yet Taken".
    _, results = student({
        "scores_Quizzes": {"added": [{"Item": "Quiz 5", "Score (%)": 85.0}]},
    })

    assert results.session_state["engine_scores"]["quizzes"][4] == 85


def test_s2_incomplete_and_extra_score_lists():
    _, fewer = student({"scores_Quizzes": {"deleted": [3]}})
    _, more = student({
        "scores_Quizzes": {"added": [
            {"Item": "Quiz 5", "Score (%)": 60.0, "Status": "Completed"},
        ]},
    })
    _, none = student({"scores_Exams": {"deleted": [0, 1]}})

    assert fewer.session_state["engine_scores"]["quizzes"] == [80, 92, 70]
    assert engine(more)["current"]["category_results"]["quizzes"][
        "average"] == pytest.approx((80 + 100 + 70) / 3)
    assert "Exams is worth 40% but has 0 items" in shown_text(none)
    # No exams: (90*15 + 95*15 + 100*5) / 35 = 93.57
    assert metrics(none)["Current grade"] == ("93.57%", "A")


def test_s2_attendance_statuses():
    _, results = student({
        "attendance_editor": {"edited": {0: {"Attendance": "Late"}}},
    })

    marks = results.session_state["engine_scores"]["attendance"]
    assert marks[0] == 75 and marks[1] == 100 and marks[19] == 0
    # 0 dropped -> (75 + 18*100) / 19 = 98.68 -> 87.85
    assert metrics(results)["Current grade"][0] == "87.85%"


def test_s2_invalid_attendance_status_is_rejected():
    setup, results = student({
        "attendance_editor": {"edited": {0: {"Attendance": "Tardy"}}},
    })

    assert "• Attendance row 1: Select Present, Late, or Absent." in setup_errors(setup)
    assert not results.exception


# --------------------------------------------------
# 3. CATEGORY CALCULATIONS
# --------------------------------------------------

def test_s3_quiz_bonus_and_drop_explained():
    _, results = student()
    text = shown_text(results)

    assert "Quizzes item 2: 92 counted as 100 (above 90)." in text
    assert "Quizzes item 3: 70 dropped (lowest 1 of 3 scored)." in text
    assert "Quizzes average: (80 + 100) / 2 = 90." in text


def test_s3_quiz_drop_needs_two_scores():
    _, results = student(edit("Quizzes", {1: not_taken(), 2: not_taken()}))

    quizzes = engine(results)["current"]["category_results"]["quizzes"]
    assert quizzes["dropped"] == []
    assert quizzes["average"] == pytest.approx(80)
    assert "No quizzes dropped yet" in shown_text(results)


def test_s3_untaken_quiz_is_not_zero_or_dropped():
    _, results = student()
    quizzes = engine(results)["current"]["category_results"]["quizzes"]

    assert [item["index"] for item in quizzes["dropped"]] == [2]
    assert quizzes["completed_count"] == 3


@pytest.mark.parametrize("not_taken_rows, average, dropped", [
    ({2: not_taken(), 3: not_taken()}, 95, 0),   # 2 scores: below threshold
    ({3: not_taken()}, 100, 2),                   # 3 scores: at threshold
    ({}, 95, 2),                                  # 4 scores: above threshold
])
def test_s3_homework_drop_threshold(not_taken_rows, average, dropped):
    _, results = student(edit("Homework", not_taken_rows))

    homework = engine(results)["current"]["category_results"]["homework"]
    assert homework["average"] == pytest.approx(average)
    assert len(homework["dropped"]) == dropped


def test_s3_exam_average():
    _, results = student()

    assert "Exams average: (78 + 88) / 2 = 83." in shown_text(results)


def test_s3_attendance_drop_and_keep_one_safeguard():
    _, normal = student()
    _, extreme = student(settings={"Attendance marks to drop (%)": 99.0})

    assert engine(normal)["current"]["category_results"]["attendance"]["drop_count"] == 1
    # 99% of 20 = 19.8 -> 20, but at least one mark is kept -> 19
    attendance = engine(extreme)["current"]["category_results"]["attendance"]
    assert attendance["drop_count"] == 19
    assert len(attendance["kept"]) == 1


def test_s3_category_with_no_scores_is_left_out():
    _, results = student(edit("Quizzes", {i: not_taken() for i in range(3)}))

    # (95*15 + 83*40 + 100*5) / 60 = 87.42
    assert metrics(results)["Current grade"][0] == "87.42%"
    assert "No scores yet for Quizzes, Final Exam" in shown_text(results)


# --------------------------------------------------
# 4. OVERALL GRADE CALCULATION
# --------------------------------------------------

def test_s4_weights_and_renormalization_shown():
    _, results = student()
    text = shown_text(results)

    assert "(90 × 15 + 95 × 15 + 83 × 40 + 100 × 5) / 75 = 87.93% → B." in text
    assert "25% of the weight is left out and the other 75% is rescaled" in text


def test_s4_all_scores_present_uses_full_policy():
    _, results = student(merge(
        edit("Quizzes", {3: row(85)}),
        edit("Final Exam", {0: row(90)}),
    ))

    # quizzes 88.33, final 90 replaces 78 -> exams 89 -> 90.60
    assert metrics(results)["Current grade"] == ("90.60%", "A")
    assert "/ 100 = 90.6% → A." in shown_text(results)


@pytest.mark.parametrize("a_minimum, letter", [(87.93, "A"), (87.94, "B")])
def test_s4_letter_cutoff_boundary(a_minimum, letter):
    _, results = student(settings={"A minimum": a_minimum})

    assert metrics(results)["Current grade"][1] == letter


# --------------------------------------------------
# 5. FINAL-EXAM REPLACEMENT
# --------------------------------------------------

@pytest.mark.parametrize("final, used, grade, without, with_", [
    (95, True, ("93.10%", "A"), "89.70%", "93.10%"),
    (70, False, ("83.45%", "B"), "83.45%", "81.85%"),
    (78, False, ("85.45%", "B"), "85.45%", "85.45%"),   # equal to lowest exam
])
def test_s5_final_replacement(final, used, grade, without, with_):
    _, results = student(edit("Final Exam", {0: row(final)}))
    shown = metrics(results)

    assert engine(results)["current"]["replacement_used"] is used
    assert shown["Current grade"] == grade
    assert shown["Without final replacement"][0] == without
    assert shown["With final replacement"][0] == with_

    if used:
        assert "Your final exam replaced your lowest exam" in shown_text(results)
        assert "Final Exam (95) replaced Exams item 1 (78)" in shown_text(results)
    else:
        assert "did not replace an exam" in shown_text(results)


# --------------------------------------------------
# 6. GRADE TARGETS AND REMAINING WORK (engine results from the UI)
# --------------------------------------------------

def test_s6_final_and_remaining_targets():
    _, results = student()
    result = engine(results)
    final = result["final_targets"]["targets"]

    assert final["A"]["with_replacement"] == {"status": "needed", "score": 88.12}
    assert final["A"]["without_replacement"] == {"status": "needed", "score": 96.2}
    assert final["B"]["with_replacement"]["score"] == 56.2
    assert final["D"]["with_replacement"]["status"] == "locked"
    assert result["remaining"] == {
        "quizzes": 1, "homework": 0, "exams": 0, "final": 1,
    }
    assert result["remaining_targets"]["targets"]["A"]["score"] == 88.3


def test_s6_required_score_is_enough_after_rounding():
    _, results = student()
    scores = results.session_state["engine_scores"]
    policy = results.session_state["engine_policy"]

    def grade_with_final(final):
        hypothetical = deepcopy(scores)
        hypothetical["final"] = final
        return evaluate(hypothetical, policy)["current"]["current_percentage"]

    assert grade_with_final(88.12) >= 90
    assert grade_with_final(88.11) < 90


def test_s6_secured_possible_and_unreachable():
    _, sample = student()
    _, low_exams = student(edit("Exams", {0: row(40), 1: row(50)}))

    letters = engine(sample)["letter_outlook"]["letters"]
    assert letters["D"]["status"] == "secured"
    assert letters["A"]["status"] == "possible"

    low = engine(low_exams)
    assert low["letter_outlook"]["letters"]["A"]["status"] == "impossible"
    assert low["final_targets"]["targets"]["A"]["with_replacement"][
        "status"] == "unreachable"


def test_s6_best_possible_keeps_earned_final():
    _, open_final = student()
    _, taken_final = student(edit("Final Exam", {0: row(60)}))

    assert engine(open_final)["best_possible"]["percentage"] == pytest.approx(95.85)
    taken = engine(taken_final)["best_possible"]
    assert taken["assumed_scores"]["final"] == 60
    assert taken["percentage"] < 95.85


# --------------------------------------------------
# 7. EXPLANATIONS AND TRANSPARENCY
# --------------------------------------------------

def test_s7_explanation_displayed_and_consistent():
    _, results = student()
    text = shown_text(results)

    for line in engine(results)["explanation"]:
        assert line["message"] in text

    assert "Homework item 3: 80 dropped (lowest 2 of 4 scored)." in text
    assert "Homework item 4: 50 dropped (lowest 2 of 4 scored)." in text


def test_s7_explanation_updates_when_scores_change():
    _, results = student(edit("Quizzes", {1: row(90)}))
    text = shown_text(results)

    assert "counted as 100" not in text
    assert "Quizzes average: (80 + 90) / 2 = 85." in text


# --------------------------------------------------
# 8. REGRESSION AND EDGE CASES
# --------------------------------------------------

def test_s8_judges_two_homework_scores():
    _, results = student(edit("Homework", {2: not_taken(), 3: not_taken()}))

    assert "No homework dropped yet" in shown_text(results)


def test_s8_simpler_syllabus_with_rules_off():
    setup, results = student(
        {
            "setup_categories": {
                "edited": {1: {"Weight (%)": 30}, 2: {"Weight (%)": 45}},
                "deleted": [0, 4],
            },
            "scores_Homework": {"edited": {
                0: row(90), 1: row(80), 2: not_taken(), 3: not_taken(),
            }},
            "scores_Exams": {"edited": {0: row(70), 1: row(85)}},
        },
        settings={
            "Lowest homework scores to drop": 0,
            "Final exam may replace the lowest exam if it helps": False,
            "A minimum": 93.0, "B minimum": 85.0,
            "C minimum": 75.0, "D minimum": 65.0,
        },
    )

    assert setup_errors(setup) == []
    # Homework 85, exams 77.5 -> (85*30 + 77.5*45) / 75 = 80.5
    assert metrics(results)["Current grade"] == ("80.50%", "C")
    assert "This course has no final exam replacement rule." in shown_text(results)


def test_s8_no_scores_entered():
    _, results = student(merge(
        edit("Quizzes", {i: not_taken() for i in range(4)}),
        edit("Homework", {i: not_taken() for i in range(4)}),
        edit("Exams", {i: not_taken() for i in range(2)}),
        {"attendance_editor": {"deleted": list(range(20))}},
    ))

    assert results.info[0].value.startswith("No scores entered yet")


def test_s8_all_zeros():
    _, results = student(merge(
        edit("Quizzes", {i: row(0) for i in range(4)}),
        edit("Homework", {i: row(0) for i in range(4)}),
        edit("Exams", {i: row(0) for i in range(2)}),
        edit("Final Exam", {0: row(0)}),
        {"attendance_editor": {"edited": {
            i: {"Attendance": "Absent"} for i in range(20)
        }}},
    ))

    assert metrics(results)["Current grade"] == ("0.00%", "F")


def test_s8_invalid_policies_give_errors_not_crashes():
    weights, _ = student({
        "setup_categories": {"edited": {0: {"Weight (%)": 5}}},
    })
    cutoffs, _ = student(settings={"B minimum": 95.0})

    assert "• Grading category weights must total 100%." in setup_errors(weights)
    assert "• Letter cutoffs must follow A > B > C > D." in setup_errors(cutoffs)


# --------------------------------------------------
# 9. TASK 3 WHAT-IF (engine level; the what-if page is not built yet)
# --------------------------------------------------

@pytest.mark.parametrize("final, grade, letter", [
    (0, 65.95, "D"),
    (56.2, 80.00, "B"),     # B target: exactly reaches 80
    (88.12, 90.004, "A"),   # A target with replacement
    (90, 90.85, "A"),
    (100, 95.35, "A"),
])
def test_s9_hypothetical_final_scores(final, grade, letter):
    _, results = student()
    scores = results.session_state["engine_scores"]
    policy = results.session_state["engine_policy"]

    hypothetical = deepcopy(scores)
    hypothetical["final"] = final
    projected = evaluate(hypothetical, policy)["current"]

    assert projected["current_percentage"] == pytest.approx(grade)
    assert projected["letter_grade"] == letter

    # The student's real scores and grade are unchanged.
    assert results.session_state["engine_scores"]["final"] is None
    assert engine(results)["current"]["current_percentage"] == pytest.approx(6595 / 75)


def test_s9_what_if_follows_the_same_rules_as_the_main_page():
    _, results = student()
    _, entered = student(edit("Final Exam", {0: row(95)}))

    hypothetical = deepcopy(results.session_state["engine_scores"])
    hypothetical["final"] = 95
    projected = evaluate(hypothetical, results.session_state["engine_policy"])

    assert projected["current"] == engine(entered)["current"]
    assert projected["explanation"] == engine(entered)["explanation"]
