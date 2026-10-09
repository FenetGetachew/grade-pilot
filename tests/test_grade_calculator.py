"""
Tests for the grading engine.

The expected numbers come from the sample scenario in the problem
statement, plus the "small changes" the judges say they will try.
Run with:  .venv/bin/python -m pytest
"""

import pytest

from copy import deepcopy

from logic.grade_calculator import (
    DEFAULT_POLICY,
    prepare_scores,
    validate_policy,
    calculate_attendance_average,
    calculate_best_possible_grade,
    calculate_final_targets,
    calculate_letter_outlook,
    calculate_worst_possible_grade,
    calculate_remaining_targets,
    compare_rules,
    complete_policy,
    count_remaining_work,
    evaluate,
    explain_grade,
    find_input_errors,
    fill_remaining_work,
    calculate_grade,
    calculate_homework_average,
    calculate_quiz_average,
    get_letter_grade,
)


def sample_scores():
    """The official sample scenario. None = not yet taken."""

    return {
        "quizzes": [80, 92, 70, None],
        "homework": [100, 90, 80, 50],
        "exams": [78, 88],
        "final": None,
        "attendance": [100] * 19 + [0],
    }


# --------------------------------------------------
# OFFICIAL SAMPLE SCENARIO
# --------------------------------------------------

def test_sample_quizzes():
    result = calculate_quiz_average(sample_scores()["quizzes"])

    assert result["average"] == pytest.approx(90)

    # The 92 (index 1) was raised to 100.
    assert [item["index"] for item in result["adjusted"]] == [1]
    assert result["adjusted"][0]["adjusted_score"] == 100

    # The 70 (index 2) was dropped, not the blank quiz.
    assert [item["index"] for item in result["dropped"]] == [2]


def test_sample_homework():
    result = calculate_homework_average(sample_scores()["homework"])

    assert result["average"] == pytest.approx(95)
    dropped_scores = sorted(
        item["adjusted_score"] for item in result["dropped"]
    )
    assert dropped_scores == [50, 80]


def test_sample_attendance():
    result = calculate_attendance_average(sample_scores()["attendance"])

    assert result["drop_count"] == 1
    assert result["dropped"][0]["score"] == 0
    assert result["average"] == pytest.approx(100)


def test_sample_current_grade():
    result = calculate_grade(sample_scores())

    # (90*15 + 95*15 + 83*40 + 100*5) / 75
    assert result["current_percentage"] == pytest.approx(6595 / 75)
    assert round(result["current_percentage"], 1) == 87.9
    assert result["letter_grade"] == "B"

    # The final has not been taken, so replacement cannot apply.
    assert result["replacement_used"] is False
    assert result["grade_with_replacement"] is None


# --------------------------------------------------
# JUDGES' SMALL CHANGES
# --------------------------------------------------

def test_quiz_of_exactly_90_is_not_raised():
    scores = sample_scores()
    scores["quizzes"] = [80, 90, 70, None]

    quizzes = calculate_quiz_average(scores["quizzes"])

    assert quizzes["adjusted"] == []
    assert quizzes["average"] == pytest.approx(85)

    result = calculate_grade(scores)
    assert result["current_percentage"] == pytest.approx(6520 / 75)


def test_only_two_homework_scores_drops_nothing():
    homework = calculate_homework_average([100, 50, None, None])

    assert homework["dropped"] == []
    assert homework["average"] == pytest.approx(75)


def test_final_that_helps_replaces_lowest_exam():
    scores = sample_scores()
    scores["final"] = 95

    result = calculate_grade(scores)

    # Without: exams 83.  With: exams (95 + 88) / 2 = 91.5
    assert result["grade_without_replacement"] == pytest.approx(89.70)
    assert result["grade_with_replacement"] == pytest.approx(93.10)
    assert result["replacement_used"] is True
    assert result["current_percentage"] == pytest.approx(93.10)
    assert result["letter_grade"] == "A"


def test_final_that_does_not_help_is_not_used():
    scores = sample_scores()
    scores["final"] = 70

    result = calculate_grade(scores)

    # With replacement exams would be (70 + 88) / 2 = 79.
    assert result["grade_without_replacement"] == pytest.approx(83.45)
    assert result["grade_with_replacement"] == pytest.approx(81.85)
    assert result["replacement_used"] is False
    assert result["current_percentage"] == pytest.approx(83.45)


# --------------------------------------------------
# GENERAL RULES
# --------------------------------------------------

def test_blank_is_not_zero_but_zero_counts():
    blank = calculate_homework_average([90, None])
    zeroed = calculate_homework_average([90, 0])

    assert blank["average"] == pytest.approx(90)
    assert zeroed["average"] == pytest.approx(45)


def test_quiz_drop_needs_two_scores():
    result = calculate_quiz_average([60, None, None])

    assert result["dropped"] == []
    assert result["average"] == pytest.approx(60)


@pytest.mark.parametrize(
    "percentage, letter",
    [(90, "A"), (89.99, "B"), (80, "B"), (70, "C"), (60, "D"), (59.9, "F")],
)
def test_letter_cutoffs(percentage, letter):
    assert get_letter_grade(percentage) == letter


def test_custom_cutoffs():
    policy = dict(DEFAULT_POLICY)
    policy["letter_cutoffs"] = {"A": 93, "B": 85, "C": 75, "D": 65}

    assert get_letter_grade(90, policy) == "B"


# --------------------------------------------------
# FINAL SCORE NEEDED FOR EACH LETTER
# --------------------------------------------------

def test_remaining_quiz_assumes_current_average():
    filled = fill_remaining_work(sample_scores())

    assert filled["quizzes"] == [80, 92, 70, 90]
    assert filled["final"] is None


def test_category_with_no_scores_stays_blank():
    filled = fill_remaining_work({"quizzes": [None, None]})

    # Padded to the policy's 4 quizzes, all still blank.
    assert filled["quizzes"] == [None] * 4


def test_sample_final_targets():
    # Without replacement: (6595 + 25F) / 100 >= cutoff
    # With replacement (F > 78): (5035 + 45F) / 100 >= cutoff
    targets = calculate_final_targets(sample_scores())["targets"]

    expected = {
        "A": (("needed", 96.2), ("needed", 88.12)),
        "B": (("needed", 56.2), ("needed", 56.2)),
        "C": (("needed", 16.2), ("needed", 16.2)),
        "D": (("locked", 0.0), ("locked", 0.0)),
    }

    for letter, (without, with_) in expected.items():
        result = targets[letter]
        assert (
            result["without_replacement"]["status"],
            result["without_replacement"]["score"],
        ) == without, letter
        assert (
            result["with_replacement"]["status"],
            result["with_replacement"]["score"],
        ) == with_, letter


def test_replacement_never_needs_a_higher_final():
    targets = calculate_final_targets(sample_scores())["targets"]

    for result in targets.values():
        without = result["without_replacement"]["score"]
        with_ = result["with_replacement"]["score"]

        if without is not None and with_ is not None:
            assert with_ <= without


def test_unreachable_target():
    scores = sample_scores()
    scores["exams"] = [40, 50]

    targets = calculate_final_targets(scores)["targets"]

    assert targets["A"]["without_replacement"] == {
        "status": "unreachable",
        "score": None,
    }


def test_targets_skipped_when_final_taken():
    scores = sample_scores()
    scores["final"] = 80

    result = calculate_final_targets(scores)

    assert result["final_taken"] is True
    assert result["targets"] == {}


# --------------------------------------------------
# BEST GRADE STILL POSSIBLE
# --------------------------------------------------

def test_sample_best_possible_grade():
    # Remaining quiz = 100 -> quizzes [80, 100, 70, 100], drop 70 -> 93.33
    # Final = 100 replaces the 78 -> exams (100 + 88) / 2 = 94
    # (93.33*15 + 95*15 + 94*40 + 100*25 + 100*5) / 100 = 95.85
    result = calculate_best_possible_grade(sample_scores())

    assert result["percentage"] == pytest.approx(95.85)
    assert result["letter_grade"] == "A"


def test_best_possible_keeps_a_final_already_taken():
    scores = sample_scores()
    scores["final"] = 60

    with_final_60 = calculate_best_possible_grade(scores)
    with_final_open = calculate_best_possible_grade(sample_scores())

    assert with_final_60["percentage"] < with_final_open["percentage"]
    assert with_final_60["final_assumed"] is False
    assert with_final_60["assumed_scores"]["final"] == 60


def test_best_possible_fills_blank_attendance_as_present():
    scores = sample_scores()
    scores["attendance"] = [100, 0, None, None]

    result = calculate_best_possible_grade(scores)

    assert result["assumed_scores"]["attendance"] == [100, 0, 100, 100]


def test_best_possible_with_no_scores_at_all():
    result = calculate_best_possible_grade({})

    assert result["percentage"] == pytest.approx(100)
    assert result["letter_grade"] == "A"


# --------------------------------------------------
# CONFIGURABLE POLICY
# --------------------------------------------------

def make_policy(**changes):
    policy = deepcopy(DEFAULT_POLICY)
    policy.update(changes)
    return policy


def test_attendance_names_match_numbers():
    by_name = calculate_grade(
        dict(sample_scores(), attendance=["present"] * 19 + ["absent"])
    )
    by_number = calculate_grade(sample_scores())

    assert by_name["current_percentage"] == pytest.approx(
        by_number["current_percentage"]
    )


def test_custom_attendance_values():
    policy = make_policy(
        attendance_values={"present": 100, "late": 50, "absent": 0},
        attendance_drop_fraction=0,
    )

    result = calculate_attendance_average(["present", "Late"], policy)

    assert result["average"] == pytest.approx(75)


def test_unknown_attendance_mark_is_rejected():
    with pytest.raises(ValueError, match="Unknown attendance mark"):
        calculate_attendance_average(["tardy"])


def test_attendance_always_keeps_one_mark():
    policy = make_policy(attendance_drop_fraction=0.9)

    result = calculate_attendance_average([0, 100], policy)

    assert result["drop_count"] == 1
    assert result["average"] == pytest.approx(100)


def test_item_counts_pad_with_remaining_work():
    prepared = prepare_scores({"quizzes": [80]}, DEFAULT_POLICY)

    assert prepared["quizzes"] == [80, None, None, None]
    assert prepared["exams"] == [None, None]
    assert prepared["final"] is None


def test_too_many_scores_is_rejected():
    with pytest.raises(ValueError, match="only 2"):
        calculate_grade({"exams": [80, 90, 70]})


def test_no_fixed_count_accepts_any_number():
    policy = make_policy(
        item_counts={"quizzes": None, "homework": None,
                     "exams": None, "attendance": None},
    )

    result = calculate_grade({"exams": [80, 90, 70]}, policy)

    assert result["current_percentage"] == pytest.approx(80)


def test_drop_rule_that_drops_everything_is_rejected():
    policy = make_policy(homework_drop_lowest=3)

    with pytest.raises(ValueError, match="drop every score"):
        validate_policy(policy)


def test_drops_can_be_turned_off():
    policy = make_policy(homework_drop_lowest=0)

    result = calculate_homework_average([100, 90, 80, 50], policy)

    assert result["dropped"] == []
    assert result["average"] == pytest.approx(80)


def test_quiz_bonus_can_be_turned_off():
    policy = make_policy(quiz_cap_threshold=100)

    result = calculate_quiz_average([80, 92, 70, None], policy)

    assert result["adjusted"] == []
    assert result["average"] == pytest.approx(86)


def test_replacement_rule_can_be_turned_off():
    scores = dict(sample_scores(), final=95)
    policy = make_policy(final_replaces_lowest_exam=False)

    result = calculate_grade(scores, policy)

    assert result["replacement_used"] is False
    assert result["current_percentage"] == pytest.approx(89.70)
    # The other way is still reported for comparison.
    assert result["grade_with_replacement"] == pytest.approx(93.10)


@pytest.mark.parametrize(
    "changes, message",
    [
        ({"weights": {"labs": 10}}, "Unknown categories"),
        ({"attendance_drop_fraction": 1}, "drop fraction"),
        ({"attendance_values": {"present": 120}}, "0 to 100"),
        ({"item_counts": {"quizzes": -1}}, "whole number"),
        ({"quiz_cap_value": 105}, "Quiz bonus"),
    ],
)
def test_invalid_policies_are_rejected(changes, message):
    with pytest.raises(ValueError, match=message):
        validate_policy(make_policy(**changes))


# --------------------------------------------------
# SCORE NEEDED ON ALL REMAINING WORK
# --------------------------------------------------

def test_sample_remaining_work():
    remaining = count_remaining_work(sample_scores())

    assert remaining == {
        "quizzes": 1, "homework": 0, "exams": 0, "final": 1,
    }


def test_sample_remaining_targets():
    # The last quiz and the final both get score x.
    # A (x in 78..90): quizzes (180 + x) / 3, exams (x + 88) / 2
    #     -> (4585 + 50x) / 100 >= 90  ->  x >= 88.3
    # B, C (x < 70): x is the dropped quiz, quizzes 83.33, no
    #     replacement -> (6495 + 25x) / 100  ->  60.2 and 20.2
    # D: 64.95 even with zeros -> locked
    targets = calculate_remaining_targets(sample_scores())["targets"]

    assert targets["A"] == {"status": "needed", "score": 88.3, "cutoff": 90}
    assert targets["B"]["score"] == 60.2
    assert targets["C"]["score"] == 20.2
    assert targets["D"]["status"] == "locked"


def test_no_remaining_work():
    scores = dict(sample_scores(), quizzes=[80, 92, 70, 85], final=90)

    result = calculate_remaining_targets(scores)

    assert result["targets"] == {}


def test_remaining_targets_include_unstarted_category():
    # No quizzes taken yet: they count once they are filled in,
    # instead of being left out.
    scores = dict(sample_scores(), quizzes=[])

    result = calculate_remaining_targets(scores)

    assert result["remaining"]["quizzes"] == 4
    assert result["targets"]["A"]["status"] == "needed"


# --------------------------------------------------
# A DIFFERENT, SIMPLER SYLLABUS
# --------------------------------------------------

def simple_policy():
    """
    Homework 30% (4), Exams 45% (3), Final 25%.
    No quizzes, no attendance, no drops, no bonus, no
    replacement, and stricter cutoffs.
    """

    return {
        "category_names": {
            "homework": "Problem Sets",
            "exams": "Midterms",
            "final": "Final Exam",
        },
        "weights": {"homework": 30, "exams": 45, "final": 25},
        "item_counts": {"homework": 4, "exams": 3},
        "quiz_cap_threshold": 100,
        "quiz_cap_value": 100,
        "quiz_drop_lowest": 0,
        "quiz_drop_min_completed": 0,
        "homework_drop_lowest": 0,
        "homework_drop_min_completed": 0,
        "attendance_values": {"present": 100, "late": 75, "absent": 0},
        "attendance_drop_fraction": 0,
        "final_replaces_lowest_exam": False,
        "letter_cutoffs": {"A": 93, "B": 85, "C": 75, "D": 65},
    }


def simple_scores():
    return {
        "homework": [90, 80],
        "exams": [70, 85],
        "final": None,
    }


def test_simple_syllabus_current_grade():
    # Homework 85, exams 77.5 -> (85*30 + 77.5*45) / 75 = 80.5
    result = calculate_grade(simple_scores(), simple_policy())

    assert result["current_percentage"] == pytest.approx(80.5)
    assert result["letter_grade"] == "C"

    homework = result["category_results"]["homework"]
    assert homework["dropped"] == []


def test_simple_syllabus_final_targets():
    # Remaining work at current averages (85, 77.5):
    # (6037.5 + 25F) / 100 >= cutoff
    result = calculate_final_targets(simple_scores(), simple_policy())
    targets = result["targets"]

    assert result["replacement_enabled"] is False
    assert targets["A"]["without_replacement"]["status"] == "unreachable"
    assert targets["B"]["without_replacement"]["score"] == 98.5
    assert targets["C"]["without_replacement"]["score"] == 58.5
    assert targets["D"]["without_replacement"]["score"] == 18.5
    assert targets["A"]["with_replacement"] is None


def test_simple_syllabus_best_possible():
    # Homework [90, 80, 100, 100] = 92.5, exams [70, 85, 100] = 85
    # (92.5*30 + 85*45 + 100*25) / 100 = 91.0
    result = calculate_best_possible_grade(simple_scores(), simple_policy())

    assert result["percentage"] == pytest.approx(91.0)
    assert result["letter_grade"] == "B"
    assert result["replacement_used"] is False


def test_simple_syllabus_remaining_targets():
    # x on 2 homework, 1 exam, and the final: (3600 + 55x) / 100
    result = calculate_remaining_targets(simple_scores(), simple_policy())
    targets = result["targets"]

    assert result["remaining"] == {
        "quizzes": 0, "homework": 2, "exams": 1, "final": 1,
    }
    assert targets["A"]["status"] == "unreachable"
    assert targets["B"]["score"] == 89.10
    assert targets["C"]["score"] == 70.91
    assert targets["D"]["score"] == 52.73


# --------------------------------------------------
# EDGE CASES
# --------------------------------------------------

def test_no_scores_at_all():
    result = calculate_grade({})

    assert result["current_percentage"] is None
    assert result["letter_grade"] is None


def test_final_with_no_exams():
    result = calculate_grade({"final": 80})

    assert result["current_percentage"] == pytest.approx(80)
    assert result["replacement_used"] is False
    assert result["grade_with_replacement"] is None


def test_all_zeros():
    scores = {
        "quizzes": [0] * 4,
        "homework": [0] * 4,
        "exams": [0, 0],
        "final": 0,
        "attendance": ["absent"] * 20,
    }

    result = calculate_grade(scores)

    assert result["current_percentage"] == 0
    assert result["letter_grade"] == "F"


@pytest.mark.parametrize("bad", [-1, 101, "90", True])
def test_bad_scores_are_rejected(bad):
    with pytest.raises(ValueError):
        calculate_grade({"exams": [bad]})


def test_inputs_are_not_changed():
    scores = sample_scores()
    before = deepcopy(scores)

    calculate_grade(scores)
    calculate_final_targets(scores)
    calculate_best_possible_grade(scores)
    calculate_remaining_targets(scores)

    assert scores == before


# --------------------------------------------------
# PARTIAL POLICIES, ERROR LISTS, AND evaluate()
# --------------------------------------------------

def test_partial_policy_turns_missing_rules_off():
    # Only the settings this syllabus uses.
    short_policy = {
        "weights": {"homework": 30, "exams": 45, "final": 25},
        "item_counts": {"homework": 4, "exams": 3},
        "letter_cutoffs": {"A": 93, "B": 85, "C": 75, "D": 65},
    }

    short = calculate_grade(simple_scores(), short_policy)
    full = calculate_grade(simple_scores(), simple_policy())

    assert short["current_percentage"] == pytest.approx(
        full["current_percentage"]
    )

    completed = complete_policy(short_policy)
    assert completed["homework_drop_lowest"] == 0
    assert completed["final_replaces_lowest_exam"] is False
    assert completed["attendance_values"]["late"] == 75


def test_no_policy_means_sample_course():
    assert complete_policy(None) == DEFAULT_POLICY


def test_all_policy_problems_are_reported_together():
    policy = make_policy(
        weights={"quizzes": -5},
        letter_cutoffs={"A": 70, "B": 80, "C": 70, "D": 60},
        homework_drop_lowest=3,
        quiz_drop=1,
    )

    errors = find_input_errors(sample_scores(), policy)

    assert len(errors) == 4
    assert any("Unknown policy settings" in e for e in errors)
    assert any("negative" in e for e in errors)
    assert any("drop every score" in e for e in errors)
    assert any("descending" in e for e in errors)


def test_score_problems_name_the_item():
    scores = {
        "quizzes": [80, 105, "ninety"],
        "exams": [70, 80, 90],
        "attendance": ["present", "tardy"],
        "final": -1,
    }

    errors = find_input_errors(scores)

    assert errors == [
        "Quizzes item 2: scores must be 0 to 100.",
        "Quizzes item 3: scores must be numbers or blank.",
        "Exams: 3 scores were entered, but the policy has only 2.",
        "Attendance item 2: unknown mark 'tardy'. "
        "Use one of: present, late, absent.",
        "Final Exam: the score must be 0 to 100.",
    ]


def test_evaluate_sample():
    result = evaluate(sample_scores())

    assert result["ok"] is True
    assert result["errors"] == []
    assert round(result["current"]["current_percentage"], 1) == 87.9
    assert result["current"]["letter_grade"] == "B"
    assert result["remaining"]["final"] == 1
    assert result["best_possible"]["percentage"] == pytest.approx(95.85)
    assert result["final_targets"]["targets"]["A"][
        "with_replacement"]["score"] == 88.12
    assert result["remaining_targets"]["targets"]["A"]["score"] == 88.3


def test_evaluate_reports_errors_instead_of_raising():
    result = evaluate({"exams": [150]})

    assert result == {
        "ok": False,
        "errors": ["Exams item 1: scores must be 0 to 100."],
    }


# --------------------------------------------------
# EXPLANATIONS: WHICH RULES FIRED
# --------------------------------------------------

def messages(scores, policy=None, rule=None):
    return [
        line["message"] for line in explain_grade(scores, policy)
        if rule is None or line["rule"] == rule
    ]


def test_sample_explanation():
    assert messages(sample_scores()) == [
        "Quizzes item 2: 92 counted as 100 (above 90).",
        "Quizzes item 3: 70 dropped (lowest 1 of 3 scored).",
        "Quizzes average: (80 + 100) / 2 = 90.",
        "Homework item 3: 80 dropped (lowest 2 of 4 scored).",
        "Homework item 4: 50 dropped (lowest 2 of 4 scored).",
        "Homework average: (100 + 90) / 2 = 95.",
        "Attendance item 20: absent (0) dropped (lowest 1 of 20 marks).",
        "Attendance average: 100 over 19 marks kept.",
        "Final Exam not taken yet, so it cannot replace an exam yet.",
        "Exams average: (78 + 88) / 2 = 83.",
        "No scores yet for Final Exam, so 25% of the weight is left "
        "out and the other 75% is rescaled to 100%.",
        "(90 × 15 + 95 × 15 + 83 × 40 + 100 × 5) / 75 = 87.93% → B.",
    ]


def test_explains_final_that_helps():
    scores = dict(sample_scores(), final=95)

    assert messages(scores, rule="replacement") == [
        "Final Exam (95) replaced Exams item 1 (78): 93.1% with "
        "replacement vs 89.7% without, so the higher one is used.",
    ]


def test_explains_final_that_does_not_help():
    scores = dict(sample_scores(), final=70)

    assert messages(scores, rule="replacement") == [
        "Final Exam (70) did not replace an exam: 81.85% with "
        "replacement vs 83.45% without, so the higher one is used.",
    ]


def test_explains_why_nothing_was_dropped():
    scores = dict(sample_scores(), homework=[100, 50])

    assert messages(scores, rule="no_drop") == [
        "No homework dropped yet: the drop starts at 3 scores, "
        "and 2 are entered.",
    ]


def test_explanation_uses_custom_names():
    lines = messages(simple_scores(), simple_policy())

    assert "Problem Sets average: (90 + 80) / 2 = 85." in lines
    assert lines[-1] == "(85 × 30 + 77.5 × 45) / 75 = 80.5% → C."


def test_explanation_with_no_scores():
    assert messages({}, rule="formula") == ["No scores entered yet."]


def test_evaluate_includes_explanation():
    result = evaluate(sample_scores())

    assert result["explanation"] == explain_grade(sample_scores())


# --------------------------------------------------
# HOW MUCH EACH RULE CHANGED THE GRADE
# --------------------------------------------------

def impact(scores, policy=None):
    return {item["rule"]: item for item in compare_rules(scores, policy)}


def test_sample_rule_impact():
    # Each rule off, worked out by hand (weights sum to 75):
    #   no quiz bonus:   quizzes (80+92)/2 = 86     -> 6535/75 = 87.13
    #   no quiz drop:    quizzes (80+100+70)/3      -> 6495/75 = 86.60
    #   no homework drop: homework 320/4 = 80       -> 6370/75 = 84.93
    #   no attendance drop: attendance 1900/20 = 95 -> 6570/75 = 87.60
    result = impact(sample_scores())

    assert result["quiz_bonus"]["change"] == pytest.approx(0.80)
    assert result["quiz_drop"]["change"] == pytest.approx(4 / 3)
    assert result["homework_drop"]["change"] == pytest.approx(3.00)
    assert result["attendance_drop"]["change"] == pytest.approx(1 / 3)
    assert result["final_replacement"]["change"] == pytest.approx(0)

    assert result["homework_drop"]["message"] == (
        "The drop rule for homework raised your grade by 3.00 points "
        "(84.93% → 87.93%)."
    )
    assert result["final_replacement"]["message"] == (
        "The final exam replacement rule did not change your grade "
        "(87.93%)."
    )


def test_rule_impact_mentions_letter_change():
    result = impact(dict(sample_scores(), final=95))

    assert result["final_replacement"]["message"] == (
        "The final exam replacement rule raised your grade by 3.40 "
        "points (89.70% → 93.10%) and changed your letter from B to A."
    )


def test_rule_impact_for_rules_the_course_does_not_have():
    result = impact(simple_scores(), simple_policy())

    assert all(not item["enabled"] for item in result.values())
    assert result["homework_drop"]["message"] == (
        "This course has no drop rule for problem sets."
    )


def test_rule_impact_with_no_scores():
    assert compare_rules({}) == []


def test_evaluate_includes_rule_impact():
    result = evaluate(sample_scores())

    assert result["rule_impact"] == compare_rules(sample_scores())


# --------------------------------------------------
# CAN I STILL GET AN A? (LETTER OUTLOOK)
# --------------------------------------------------

def early_semester_scores():
    """Low early scores, but most of the semester is still ahead."""

    return {
        "quizzes": [40, None, None, None],
        "homework": [60, None, None, None],
        "exams": [85, None],
        "final": None,
        "attendance": ["present"] * 5,
    }


def test_sample_worst_possible_grade():
    # Last quiz 0 (it gets dropped): quizzes (80+100+70)/3 = 83.33
    # Final 0 does not replace an exam.
    # (83.33*15 + 95*15 + 83*40 + 0*25 + 100*5) / 100 = 64.95
    result = calculate_worst_possible_grade(sample_scores())

    assert result["percentage"] == pytest.approx(64.95)
    assert result["letter_grade"] == "D"


def test_sample_letter_outlook():
    outlook = calculate_letter_outlook(sample_scores())
    letters = outlook["letters"]

    assert outlook["best"] == pytest.approx(95.85)
    assert outlook["worst"] == pytest.approx(64.95)
    assert [letters[letter]["status"] for letter in "ABCD"] == [
        "possible", "possible", "possible", "secured",
    ]
    assert letters["A"]["can_still_reach"] is True
    assert letters["A"]["message"] == (
        "A: still possible. Perfect scores on all remaining work "
        "give 95.85%."
    )
    assert letters["D"]["message"] == (
        "D: already secured. Even zeros on all remaining work "
        "give 64.95%."
    )


def test_letter_that_is_truly_impossible():
    # Best case: final 100 replaces the 40 -> exams (100+50)/2 = 75
    # (93.33*15 + 95*15 + 75*40 + 100*25 + 100*5) / 100 = 88.25
    scores = dict(sample_scores(), exams=[40, 50])

    letters = calculate_letter_outlook(scores)["letters"]
    targets = calculate_final_targets(scores)["targets"]

    assert letters["A"]["status"] == "impossible"
    assert letters["A"]["can_still_reach"] is False
    assert letters["A"]["message"] == (
        "A: no longer possible. Even perfect scores on all remaining "
        "work give only 88.25%."
    )
    assert targets["A"]["with_replacement"]["status"] == "unreachable"


def test_early_semester_a_is_not_called_impossible():
    # At current averages (quizzes 40, homework 60) the final alone
    # cannot reach an A, but perfect remaining work gives 100%.
    scores = early_semester_scores()

    targets = calculate_final_targets(scores)["targets"]
    letters = calculate_letter_outlook(scores)["letters"]

    assert targets["A"]["with_replacement"] == {
        "status": "needs_other_work",
        "score": None,
    }
    assert targets["A"]["without_replacement"]["status"] == "needs_other_work"
    assert letters["A"]["status"] == "possible"


def test_unreachable_always_agrees_with_outlook():
    for scores in (
        sample_scores(),
        early_semester_scores(),
        dict(sample_scores(), exams=[40, 50]),
    ):
        letters = calculate_letter_outlook(scores)["letters"]
        final_targets = calculate_final_targets(scores)["targets"]
        remaining_targets = calculate_remaining_targets(scores)["targets"]

        for letter, outlook in letters.items():
            final_target = final_targets[letter]["with_replacement"]
            remaining_target = remaining_targets[letter]

            if outlook["can_still_reach"]:
                assert final_target["status"] != "unreachable"
                assert remaining_target["status"] != "unreachable"
            else:
                assert final_target["status"] == "unreachable"
                assert remaining_target["status"] == "unreachable"


def test_outlook_when_nothing_is_left():
    # quizzes [80,100,70,85] drop 70 -> 88.33; final 90 replaces 78
    # -> exams 89; (88.33*15 + 95*15 + 89*40 + 90*25 + 100*5) / 100
    scores = dict(sample_scores(), quizzes=[80, 92, 70, 85], final=90)

    outlook = calculate_letter_outlook(scores)

    assert outlook["best"] == pytest.approx(90.60)
    assert outlook["worst"] == pytest.approx(90.60)
    assert outlook["letters"]["A"]["message"] == (
        "A: secured. Your grade is 90.60%."
    )


def test_outlook_with_no_graded_categories():
    policy = {"weights": {"quizzes": 100}, "item_counts": {"quizzes": 0}}

    assert calculate_letter_outlook({}, policy)["letters"] == {}


def test_evaluate_includes_letter_outlook():
    result = evaluate(sample_scores())

    assert result["letter_outlook"] == calculate_letter_outlook(
        sample_scores()
    )
