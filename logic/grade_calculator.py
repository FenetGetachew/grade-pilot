
"""
Syllabus What-If: Grading Engine

This file handles grade calculations independently of Streamlit.

Score format:
- quizzes: list of scores; use None for work not yet graded
- homework: list of scores; use None for work not yet graded
- exams: list of regular exam scores
- final: one score, or None if not taken
- attendance: list of marks, either names from the policy
  ("present", "late", "absent") or numbers; None = not recorded

All scores are percentages from 0 to 100.
A blank (None) is remaining work. A zero is a real score.
A quiz, homework, exam, or final may also be marked "missing" or
"excused" (excused-as-zero); both count as 0.
"""

from copy import deepcopy
from math import ceil, floor


# --------------------------------------------------
# 1. DEFAULT SYLLABUS POLICY
# --------------------------------------------------

CATEGORIES = ("quizzes", "homework", "exams", "final", "attendance")

# Categories that hold a list of items (the final is one score).
LIST_CATEGORIES = ("quizzes", "homework", "exams", "attendance")

DEFAULT_POLICY = {
    "category_names": {
        "quizzes": "Quizzes",
        "homework": "Homework",
        "exams": "Exams",
        "final": "Final Exam",
        "attendance": "Attendance",
    },
    "weights": {
        "quizzes": 15,
        "homework": 15,
        "exams": 40,
        "final": 25,
        "attendance": 5,
    },
    # How many items each category has. None = no fixed count.
    # Items not entered yet are treated as remaining work.
    "item_counts": {
        "quizzes": 4,
        "homework": 4,
        "exams": 2,
        "attendance": None,
    },
    # A quiz above the threshold is raised to the cap value.
    # Set the threshold to 100 to turn the bonus off.
    "quiz_cap_threshold": 90,
    "quiz_cap_value": 100,
    "quiz_drop_lowest": 1,
    "quiz_drop_min_completed": 2,
    "homework_drop_lowest": 2,
    "homework_drop_min_completed": 3,
    "attendance_values": {
        "present": 100,
        "late": 75,
        "absent": 0,
    },
    "attendance_drop_fraction": 0.05,
    # The final replaces the lowest exam only if that helps.
    "final_replaces_lowest_exam": True,
    "letter_cutoffs": {
        "A": 90,
        "B": 80,
        "C": 70,
        "D": 60,
    },
}


# Settings a policy may leave out. A missing rule is turned off,
# so a simple syllabus only has to list what it actually uses.
# A missing category weight counts as 0.
RULES_OFF_POLICY = {
    "category_names": dict(DEFAULT_POLICY["category_names"]),
    "weights": {},
    "item_counts": {category: None for category in LIST_CATEGORIES},
    "quiz_cap_threshold": 100,
    "quiz_cap_value": 100,
    "quiz_drop_lowest": 0,
    "quiz_drop_min_completed": 0,
    "homework_drop_lowest": 0,
    "homework_drop_min_completed": 0,
    "attendance_values": dict(DEFAULT_POLICY["attendance_values"]),
    "attendance_drop_fraction": 0,
    "final_replaces_lowest_exam": False,
    "letter_cutoffs": dict(DEFAULT_POLICY["letter_cutoffs"]),
}

# Settings that are dictionaries. A partial one is merged key by
# key with the values above. (Weights are not merged.)
MERGED_SETTINGS = (
    "category_names",
    "item_counts",
    "attendance_values",
    "letter_cutoffs",
)


# --------------------------------------------------
# 2. COMPLETE AND VALIDATE THE POLICY AND SCORES
# --------------------------------------------------

def complete_policy(policy=None):
    """
    Return a full policy.

    None gives the sample course policy. Otherwise, any setting
    the policy leaves out is filled in with its rule-off value.
    Running this more than once gives the same result.
    """

    if policy is None:
        return DEFAULT_POLICY

    if not isinstance(policy, dict):
        raise ValueError("The policy must be a dictionary.")

    completed = dict(RULES_OFF_POLICY)
    completed.update(policy)

    for setting in MERGED_SETTINGS:
        value = policy.get(setting)

        if isinstance(value, dict):
            completed[setting] = {**RULES_OFF_POLICY[setting], **value}

    return completed


def is_number(value):
    """True for an int or float, but not for True or False."""

    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_whole_number(value):
    """True for an int of 0 or more, but not for True or False."""

    return isinstance(value, int) and not isinstance(value, bool) \
        and value >= 0


def validate_score(score):
    """Check that a score is either None or between 0 and 100."""

    if score is None:
        return

    if not is_number(score):
        raise ValueError("Scores must be numbers or None.")

    if not 0 <= score <= 100:
        raise ValueError("Scores must be between 0 and 100.")


def find_drop_rule_errors(policy, category):
    """Check one drop rule, and that it always keeps a score."""

    drop = policy[f"{category}_drop_lowest"]
    minimum = policy[f"{category}_drop_min_completed"]

    if not is_whole_number(drop):
        return [
            f"The {category} drop count must be a whole number "
            "of 0 or more."
        ]

    if not is_whole_number(minimum):
        return [
            f"The {category} drop threshold must be a whole number "
            "of 0 or more."
        ]

    if drop > 0 and minimum <= drop:
        return [
            f"The {category} drop rule would drop every score: "
            f"dropping {drop} needs a threshold of at least "
            f"{drop + 1} scores."
        ]

    return []


def find_policy_errors(policy=None):
    """
    Check every policy setting.

    Returns a list of plain-language problems. An empty list
    means the policy is usable.
    """

    try:
        policy = complete_policy(policy)
    except ValueError as error:
        return [str(error)]

    errors = []

    unknown = set(policy) - set(RULES_OFF_POLICY)
    if unknown:
        errors.append(f"Unknown policy settings: {sorted(unknown)}.")

    shape_errors = [
        f"The {setting} setting must be a dictionary."
        for setting in MERGED_SETTINGS + ("weights",)
        if not isinstance(policy[setting], dict)
    ]

    # The checks below need these settings to be dictionaries.
    if shape_errors:
        return errors + shape_errors

    # Weights
    weights = policy["weights"]

    unknown = set(weights) - set(CATEGORIES)
    if unknown:
        errors.append(f"Unknown categories in weights: {sorted(unknown)}.")

    if not all(is_number(weight) for weight in weights.values()):
        errors.append("Category weights must be numbers.")
    elif any(weight < 0 for weight in weights.values()):
        errors.append("Category weights cannot be negative.")
    elif sum(weights.values()) <= 0:
        errors.append("The total category weight must be positive.")

    # Item counts
    unknown = set(policy["item_counts"]) - set(LIST_CATEGORIES)
    if unknown:
        errors.append(f"Unknown categories in item counts: {sorted(unknown)}.")

    for category, count in policy["item_counts"].items():
        if count is not None and not is_whole_number(count):
            errors.append(
                f"The number of {category} must be a whole number "
                "of 0 or more."
            )

    # Quiz bonus and drop rules
    errors += find_drop_rule_errors(policy, "quiz")
    errors += find_drop_rule_errors(policy, "homework")

    for setting in ("quiz_cap_threshold", "quiz_cap_value"):
        value = policy[setting]

        if not is_number(value) or not 0 <= value <= 100:
            errors.append("Quiz bonus values must be 0 to 100.")
            break

    # Attendance
    fraction = policy["attendance_drop_fraction"]

    if not is_number(fraction) or not 0 <= fraction < 1:
        errors.append(
            "The attendance drop fraction must be at least 0 "
            "and less than 1."
        )

    for name, value in policy["attendance_values"].items():
        if not is_number(value) or not 0 <= value <= 100:
            errors.append(
                f"Attendance value for {name!r} must be 0 to 100."
            )

    # Final replacement
    if not isinstance(policy["final_replaces_lowest_exam"], bool):
        errors.append("The final-replacement rule must be True or False.")

    # Letter cutoffs
    cutoffs = policy["letter_cutoffs"]
    letters = ("A", "B", "C", "D")

    if not all(is_number(cutoffs.get(letter)) for letter in letters):
        errors.append("Cutoffs for A, B, C, and D must be numbers.")
    elif not all(0 <= cutoffs[letter] <= 100 for letter in letters):
        errors.append("Grade cutoffs must be between 0 and 100.")
    elif not (
        cutoffs["A"] >= cutoffs["B"]
        >= cutoffs["C"] >= cutoffs["D"]
    ):
        errors.append("Letter-grade cutoffs must be descending.")

    return errors


def validate_policy(policy):
    """Raise a ValueError listing every problem with the policy."""

    errors = find_policy_errors(policy)

    if errors:
        raise ValueError(" ".join(errors))


def find_score_errors(scores, policy=None):
    """
    Check the student's scores against a valid policy.

    Returns a list of plain-language problems that name the item,
    such as "Quizzes item 3: scores must be 0 to 100."
    """

    policy = complete_policy(policy)
    names = policy["category_names"]

    if not isinstance(scores, dict):
        return ["The scores must be a dictionary."]

    errors = []

    unknown = set(scores) - set(CATEGORIES)
    if unknown:
        errors.append(f"Unknown score categories: {sorted(unknown)}.")

    for category in LIST_CATEGORIES:
        entries = scores.get(category, [])
        name = names.get(category, category)

        if not isinstance(entries, (list, tuple)):
            errors.append(f"{name} must be a list of scores.")
            continue

        count = policy["item_counts"].get(category)

        if count is not None and len(entries) > count:
            errors.append(
                f"{name}: {len(entries)} scores were entered, "
                f"but the policy has only {count}."
            )

        for position, entry in enumerate(entries, start=1):
            if category == "attendance" and isinstance(entry, str):
                key = entry.strip().lower()

                if key not in policy["attendance_values"]:
                    errors.append(
                        f"{name} item {position}: unknown mark "
                        f"{entry!r}. Use one of: "
                        f"{', '.join(policy['attendance_values'])}."
                    )
                continue

            if entry is None:
                continue

            if category in SCORED_CATEGORIES and zero_mark_name(entry):
                continue

            if not is_number(entry):
                errors.append(
                    f"{name} item {position}: scores must be numbers, "
                    "blank, 'missing', or 'excused'."
                )
            elif not 0 <= entry <= 100:
                errors.append(
                    f"{name} item {position}: scores must be 0 to 100."
                )

    final = scores.get("final")
    name = names.get("final", "final")

    if final is not None and not zero_mark_name(final):
        if not is_number(final):
            errors.append(
                f"{name}: the score must be a number, blank, "
                "'missing', or 'excused'."
            )
        elif not 0 <= final <= 100:
            errors.append(f"{name}: the score must be 0 to 100.")

    return errors


def find_input_errors(scores, policy=None):
    """
    Check the policy and the scores together.

    Returns every problem as a list; an empty list means the
    inputs are ready to calculate. Scores are only checked once
    the policy is valid, because item counts and attendance
    names come from the policy.
    """

    errors = find_policy_errors(policy)

    if errors:
        return errors

    return find_score_errors(scores, policy)


# Words a student may type instead of a score. Each counts as 0.
ZERO_MARKS = ("missing", "excused")

# Categories (besides the final) where those words are allowed.
SCORED_CATEGORIES = ("quizzes", "homework", "exams")


def zero_mark_name(score):
    """Return "missing" or "excused" if the score is one, else None."""

    if isinstance(score, str) and score.strip().lower() in ZERO_MARKS:
        return score.strip().lower()

    return None


def convert_score_mark(score):
    """Turn "missing" or "excused" into 0. Anything else passes through."""

    return 0 if zero_mark_name(score) else score


def convert_attendance_mark(mark, policy):
    """Turn a mark like "late" into its score. Numbers pass through."""

    if not isinstance(mark, str):
        return mark

    values = policy["attendance_values"]
    key = mark.strip().lower()

    if key not in values:
        raise ValueError(
            f"Unknown attendance mark {mark!r}. "
            f"Use one of: {', '.join(values)}."
        )

    return values[key]


def prepare_scores(scores, policy):
    """
    Return a copy of the scores ready for calculation.

    - Attendance names are converted to numbers.
    - "missing" and "excused" scores are converted to 0.
    - Each list is padded with blanks (remaining work) up to the
      policy's item count. Too many entries is an error.

    Running this more than once gives the same result.
    """

    prepared = deepcopy(scores)

    prepared["attendance"] = [
        convert_attendance_mark(mark, policy)
        for mark in prepared.get("attendance", [])
    ]

    for category in SCORED_CATEGORIES:
        prepared[category] = [
            convert_score_mark(score)
            for score in prepared.get(category, [])
        ]

    prepared["final"] = convert_score_mark(prepared.get("final"))

    for category in LIST_CATEGORIES:
        category_scores = list(prepared.get(category, []))
        count = policy.get("item_counts", {}).get(category)

        if count is not None:
            if len(category_scores) > count:
                raise ValueError(
                    f"{len(category_scores)} {category} scores were "
                    f"entered, but the policy has only {count}."
                )

            category_scores += [None] * (count - len(category_scores))

        prepared[category] = category_scores

    prepared.setdefault("final", None)

    return prepared


# --------------------------------------------------
# 3. LETTER GRADES
# --------------------------------------------------

def get_letter_grade(percentage, policy=None):
    """Convert a percentage to A, B, C, D, or F."""

    policy = complete_policy(policy)
    cutoffs = policy["letter_cutoffs"]

    if percentage >= cutoffs["A"]:
        return "A"
    if percentage >= cutoffs["B"]:
        return "B"
    if percentage >= cutoffs["C"]:
        return "C"
    if percentage >= cutoffs["D"]:
        return "D"

    return "F"


# --------------------------------------------------
# 4. CALCULATE QUIZ AND HOMEWORK AVERAGES
# --------------------------------------------------

def calculate_dropped_average(
    scores,
    drop_count=0,
    min_completed=1,
    transform=None,
):
    """
    Calculate an average after applying score adjustments and drops.

    None means the work has no score yet.
    A numeric zero is a real score and is included.
    """

    completed = []

    for index, score in enumerate(scores):
        validate_score(score)

        if score is None:
            continue

        adjusted_score = score

        if transform is not None:
            adjusted_score = transform(score)

        completed.append({
            "index": index,
            "original_score": score,
            "adjusted_score": adjusted_score,
        })

    adjusted = [
        item for item in completed
        if item["original_score"] != item["adjusted_score"]
    ]

    dropped = []

    if len(completed) >= min_completed and drop_count > 0:
        # Sort by adjusted score, lowest first.
        lowest_first = sorted(
            completed,
            key=lambda item: item["adjusted_score"],
        )

        dropped = lowest_first[:drop_count]

    dropped_indices = {item["index"] for item in dropped}

    kept = [
        item for item in completed
        if item["index"] not in dropped_indices
    ]

    average = None

    if kept:
        average = sum(
            item["adjusted_score"] for item in kept
        ) / len(kept)

    return {
        "average": average,
        "completed_count": len(completed),
        "adjusted": adjusted,
        "dropped": dropped,
        "kept": kept,
    }


def calculate_quiz_average(scores, policy=None):
    """Apply the quiz cap, then drop the lowest eligible quiz."""

    policy = complete_policy(policy)

    def cap_quiz(score):
        if score > policy["quiz_cap_threshold"]:
            return policy["quiz_cap_value"]
        return score

    return calculate_dropped_average(
        scores=scores,
        drop_count=policy["quiz_drop_lowest"],
        min_completed=policy["quiz_drop_min_completed"],
        transform=cap_quiz,
    )


def calculate_homework_average(scores, policy=None):
    """Drop the lowest completed homework scores when eligible."""

    policy = complete_policy(policy)

    return calculate_dropped_average(
        scores=scores,
        drop_count=policy["homework_drop_lowest"],
        min_completed=policy["homework_drop_min_completed"],
    )


# --------------------------------------------------
# 5. CALCULATE EXAM AVERAGE
# --------------------------------------------------

def calculate_exam_average(exams):
    """Calculate the regular exam average, ignoring blank scores."""

    completed = []

    for score in exams:
        validate_score(score)

        if score is not None:
            completed.append(score)

    if not completed:
        return None

    return sum(completed) / len(completed)


def replace_lowest_exam(exams, final_score):
    """Return a copy of the exam scores with the lowest replaced."""

    completed = list(exams)

    for score in completed:
        validate_score(score)

    validate_score(final_score)

    if final_score is None:
        return completed

    if not completed or all(score is None for score in completed):
        return completed

    # Preserve the positions of blank exams.
    valid_indices = [
        index for index, score in enumerate(completed)
        if score is not None
    ]

    lowest_index = min(
        valid_indices,
        key=lambda index: completed[index],
    )

    completed[lowest_index] = final_score

    return completed


# --------------------------------------------------
# 6. CALCULATE ATTENDANCE
# --------------------------------------------------

def calculate_attendance_average(marks, policy=None):
    """
    Drop the lowest fraction of recorded attendance marks.

    Marks may be names from the policy ("present", "late",
    "absent") or numbers. None means not recorded yet.

    The number dropped is rounded to the nearest whole mark,
    and at least one mark is always kept.
    """

    policy = complete_policy(policy)

    completed = []

    for index, mark in enumerate(marks):
        mark = convert_attendance_mark(mark, policy)
        validate_score(mark)

        if mark is not None:
            completed.append({
                "index": index,
                "score": mark,
            })

    if not completed:
        return {
            "average": None,
            "completed_count": 0,
            "drop_count": 0,
            "dropped": [],
            "kept": [],
        }

    drop_fraction = policy["attendance_drop_fraction"]

    # Round to the nearest whole number, with halves rounded up.
    drop_count = floor(
        len(completed) * drop_fraction + 0.5
    )

    drop_count = min(drop_count, len(completed) - 1)

    lowest_first = sorted(
        completed,
        key=lambda item: item["score"],
    )

    dropped = lowest_first[:drop_count]
    dropped_indices = {item["index"] for item in dropped}

    kept = [
        item for item in completed
        if item["index"] not in dropped_indices
    ]

    average = None

    if kept:
        average = sum(
            item["score"] for item in kept
        ) / len(kept)

    return {
        "average": average,
        "completed_count": len(completed),
        "drop_count": drop_count,
        "dropped": dropped,
        "kept": kept,
    }


# --------------------------------------------------
# 7. CALCULATE CATEGORY RESULTS
# --------------------------------------------------

def calculate_category_results(scores, policy=None):
    """Calculate every category average and its rule details."""

    policy = complete_policy(policy)
    validate_policy(policy)

    scores = prepare_scores(scores, policy)

    quizzes = calculate_quiz_average(
        scores.get("quizzes", []), policy
    )

    homework = calculate_homework_average(
        scores.get("homework", []), policy
    )

    exams = scores.get("exams", [])
    exam_average = calculate_exam_average(exams)

    final_score = scores.get("final")
    validate_score(final_score)

    attendance = calculate_attendance_average(
        scores.get("attendance", []), policy
    )

    return {
        "quizzes": quizzes,
        "homework": homework,
        "exams": {
            "average": exam_average,
            "completed_count": sum(
                score is not None for score in exams
            ),
            "scores": exams,
        },
        "final": {
            "average": final_score,
            "completed_count": int(final_score is not None),
        },
        "attendance": attendance,
    }


# --------------------------------------------------
# 8. CALCULATE WEIGHTED COURSE GRADE
# --------------------------------------------------

def calculate_weighted_grade(category_averages, policy=None):
    """
    Calculate a weighted course grade.

    Categories without scores are excluded.
    The remaining weights are automatically renormalized.
    """

    policy = complete_policy(policy)
    validate_policy(policy)

    weighted_total = 0
    counted_weight = 0

    for category, average in category_averages.items():
        weight = policy["weights"].get(category, 0)

        if average is None or weight == 0:
            continue

        weighted_total += average * weight
        counted_weight += weight

    if counted_weight == 0:
        return None

    return weighted_total / counted_weight


# --------------------------------------------------
# 9. CALCULATE THE CURRENT GRADE
# --------------------------------------------------

def calculate_grade(scores, policy=None, replacement_mode=None):
    """
    Calculate the grade with and without final-exam replacement.

    replacement_mode:
        None     = follow the policy (auto if the rule is on,
                   otherwise never)
        "auto"   = keep whichever grade is higher
        "never"  = do not replace an exam
        "always" = use the replacement calculation when possible
    """

    policy = complete_policy(policy)
    validate_policy(policy)

    if replacement_mode is None:
        replacement_mode = (
            "auto"
            if policy.get("final_replaces_lowest_exam", True)
            else "never"
        )

    if replacement_mode not in ("auto", "never", "always"):
        raise ValueError(
            "replacement_mode must be auto, never, or always."
        )

    scores = prepare_scores(scores, policy)

    results = calculate_category_results(scores, policy)

    base_averages = {
        category: result["average"]
        for category, result in results.items()
    }

    grade_without_replacement = calculate_weighted_grade(
        base_averages, policy
    )

    final_score = scores.get("final")
    exams = scores.get("exams", [])

    can_replace = (
        final_score is not None
        and any(score is not None for score in exams)
    )

    replacement_exams = replace_lowest_exam(exams, final_score)

    replacement_exam_average = calculate_exam_average(
        replacement_exams
    )

    replacement_averages = dict(base_averages)
    replacement_averages["exams"] = replacement_exam_average

    grade_with_replacement = None

    if can_replace:
        grade_with_replacement = calculate_weighted_grade(
            replacement_averages, policy
        )

    if replacement_mode == "never":
        current_grade = grade_without_replacement
        replacement_used = False

    elif replacement_mode == "always" and can_replace:
        current_grade = grade_with_replacement
        replacement_used = True

    elif (
        replacement_mode == "auto"
        and can_replace
        and grade_with_replacement > grade_without_replacement
    ):
        current_grade = grade_with_replacement
        replacement_used = True

    else:
        current_grade = grade_without_replacement
        replacement_used = False

    return {
        "current_percentage": current_grade,
        "letter_grade": (
            get_letter_grade(current_grade, policy)
            if current_grade is not None else None
        ),
        "grade_without_replacement": grade_without_replacement,
        "grade_with_replacement": grade_with_replacement,
        "replacement_used": replacement_used,
        "replacement_exam_scores": replacement_exams,
        "category_results": results,
        "category_averages_used": (
            replacement_averages
            if replacement_used else base_averages
        ),
    }


# --------------------------------------------------
# 10. FIND THE FINAL SCORE NEEDED FOR EACH LETTER
# --------------------------------------------------

def fill_remaining_work(
    scores,
    policy=None,
    assume="average",
    categories=LIST_CATEGORIES,
):
    """
    Return a copy of the scores with blank items filled in.
    The final is left alone.

    assume:
        "average" = each blank gets the current category average
        "perfect" = each blank gets 100
        a number  = each blank gets that score

    With "average", a category with no scores yet stays blank,
    because there is no average to assume. It is left out and
    renormalized.
    """

    policy = complete_policy(policy)

    is_number = (
        isinstance(assume, (int, float))
        and not isinstance(assume, bool)
    )

    if is_number:
        validate_score(assume)
    elif assume not in ("average", "perfect"):
        raise ValueError("assume must be average, perfect, or a score.")

    filled = prepare_scores(scores, policy)
    results = calculate_category_results(filled, policy)

    for category in categories:
        category_scores = filled.get(category, [])

        if is_number:
            fill_value = assume
        elif assume == "perfect":
            fill_value = 100
        else:
            fill_value = results[category]["average"]

        if fill_value is None:
            continue

        filled[category] = [
            fill_value if score is None else score
            for score in category_scores
        ]

    return filled


def find_minimum_score(grade_at, cutoff):
    """
    Find the lowest score (0 to 100) where grade_at(score)
    reaches the cutoff.

    grade_at must never go down as the score goes up. Every rule
    in this engine keeps that true: raising a score never lowers
    an average, a drop, or the better of two replacement options.

    Returns a dict with a status:
        "locked"      = the cutoff is reached even with a 0
        "needed"      = "score" holds the minimum score needed
        "unreachable" = not reached even with a 100
    """

    if grade_at(0) >= cutoff:
        return {"status": "locked", "score": 0.0}

    if grade_at(100) < cutoff:
        return {"status": "unreachable", "score": None}

    low = 0.0
    high = 100.0

    # Because the grade never goes down as the score goes up,
    # a binary search finds the minimum qualifying score.
    for _ in range(50):
        middle = (low + high) / 2

        if grade_at(middle) >= cutoff:
            high = middle
        else:
            low = middle

    # Round up to the hundredth so the shown score is enough.
    needed = ceil(round(high * 100, 6)) / 100

    return {"status": "needed", "score": needed}


def find_required_final(scores, policy, cutoff, replacement_mode):
    """Find the lowest final score that reaches the cutoff."""

    def grade_at(final_score):
        hypothetical_scores = deepcopy(scores)
        hypothetical_scores["final"] = final_score

        return calculate_grade(
            hypothetical_scores,
            policy,
            replacement_mode=replacement_mode,
        )["current_percentage"]

    return find_minimum_score(grade_at, cutoff)


def calculate_final_targets(scores, policy=None, assume="average"):
    """
    Find the final score needed for each letter grade, both
    without and with the final-replacement rule.

    Other remaining work (quizzes, homework, exams) is filled in
    using the chosen assumption before searching.

    "With replacement" follows the syllabus rule: the final only
    replaces the lowest exam when that raises the grade. If the
    policy has no replacement rule, it is None.

    A target is "unreachable" only if even perfect scores on all
    remaining work miss it. If better scores on other work would
    reach it, it is "needs_other_work" instead.
    """

    policy = complete_policy(policy)
    validate_policy(policy)

    if scores.get("final") is not None:
        return {
            "final_taken": True,
            "assumption": assume,
            "assumed_scores": None,
            "targets": {},
        }

    assumed_scores = fill_remaining_work(scores, policy, assume)
    replacement_enabled = policy.get("final_replaces_lowest_exam", True)

    best_case = fill_every_blank(scores, policy, 100)
    best_without = calculate_grade(
        best_case, policy, "never"
    )["current_percentage"]
    best_with = calculate_grade(
        best_case, policy, "auto"
    )["current_percentage"]

    targets = {}

    for letter, cutoff in policy["letter_cutoffs"].items():
        without = mark_other_work_needed(
            find_required_final(assumed_scores, policy, cutoff, "never"),
            best_without,
            cutoff,
        )

        with_ = None
        if replacement_enabled:
            with_ = mark_other_work_needed(
                find_required_final(assumed_scores, policy, cutoff, "auto"),
                best_with,
                cutoff,
            )

        targets[letter] = {
            "cutoff": cutoff,
            "without_replacement": without,
            "with_replacement": with_,
        }

    return {
        "final_taken": False,
        "replacement_enabled": replacement_enabled,
        "assumption": assume,
        "assumed_scores": assumed_scores,
        "targets": targets,
    }


# --------------------------------------------------
# 11. BEST AND WORST POSSIBLE GRADES, AND THE LETTER OUTLOOK
# --------------------------------------------------

def fill_every_blank(scores, policy, value):
    """
    Return a copy of the scores with every blank, including an
    untaken final, set to the same value (100 = best case,
    0 = worst case). Scores already entered are kept.
    """

    filled = fill_remaining_work(scores, policy, assume=value)

    if filled["final"] is None:
        filled["final"] = value

    return filled


def calculate_best_possible_grade(scores, policy=None):
    """
    Calculate the best grade still reachable.

    Every blank quiz, homework, exam, and attendance score is
    treated as 100. A final that has not been taken is treated
    as 100; a final that was already taken keeps its real score.
    The final replaces the lowest exam only when that helps,
    and only if the policy has the replacement rule turned on.
    """

    policy = complete_policy(policy)
    validate_policy(policy)

    final_assumed = scores.get("final") is None
    future_scores = fill_every_blank(scores, policy, 100)

    result = calculate_grade(future_scores, policy)

    return {
        "percentage": result["current_percentage"],
        "letter_grade": result["letter_grade"],
        "replacement_used": result["replacement_used"],
        "final_assumed": final_assumed,
        "assumed_scores": future_scores,
        "details": result,
    }


def calculate_worst_possible_grade(scores, policy=None):
    """
    Calculate the lowest grade still possible: every blank item
    (and an untaken final) scores 0, and every blank attendance
    mark is 0. Drop rules still apply, so a 0 may be dropped.
    """

    policy = complete_policy(policy)
    validate_policy(policy)

    future_scores = fill_every_blank(scores, policy, 0)
    result = calculate_grade(future_scores, policy)

    return {
        "percentage": result["current_percentage"],
        "letter_grade": result["letter_grade"],
        "assumed_scores": future_scores,
    }


def calculate_letter_outlook(scores, policy=None):
    """
    Answer "Can I still get an A?" for every letter.

    Each letter gets a status:
        "secured"    = reached even with zeros on all remaining work
        "possible"   = reachable with good enough remaining work
        "impossible" = not reached even with perfect remaining work

    These are exact answers, with no assumption about how the
    student will do. Returns best and worst percentages too.
    """

    policy = complete_policy(policy)
    validate_policy(policy)

    best = calculate_best_possible_grade(scores, policy)["percentage"]
    worst = calculate_worst_possible_grade(scores, policy)["percentage"]

    if best is None:
        return {"best": None, "worst": None, "letters": {}}

    nothing_left = abs(best - worst) < 1e-9

    letters = {}

    for letter, cutoff in policy["letter_cutoffs"].items():
        if worst >= cutoff:
            status = "secured"
            message = (
                f"{letter}: secured. Your grade is {worst:.2f}%."
                if nothing_left else
                f"{letter}: already secured. Even zeros on all "
                f"remaining work give {worst:.2f}%."
            )
        elif best >= cutoff:
            status = "possible"
            message = (
                f"{letter}: still possible. Perfect scores on all "
                f"remaining work give {best:.2f}%."
            )
        else:
            status = "impossible"
            message = (
                f"{letter}: not reached. Your grade is {best:.2f}%."
                if nothing_left else
                f"{letter}: no longer possible. Even perfect scores on "
                f"all remaining work give only {best:.2f}%."
            )

        letters[letter] = {
            "cutoff": cutoff,
            "status": status,
            "can_still_reach": status != "impossible",
            "message": message,
        }

    return {"best": best, "worst": worst, "letters": letters}


def mark_other_work_needed(target, best_percentage, cutoff):
    """
    Relabel an "unreachable" target as "needs_other_work" when the
    letter is still possible with better scores on other work.
    Only a truly impossible letter stays "unreachable".
    """

    if (
        target["status"] == "unreachable"
        and best_percentage is not None
        and best_percentage >= cutoff
    ):
        return {"status": "needs_other_work", "score": None}

    return target


# --------------------------------------------------
# 12. FIND THE SCORE NEEDED ON ALL REMAINING WORK
# --------------------------------------------------

# Attendance is not graded work a student can score higher on,
# so blank attendance marks are left out of this what-if.
GRADED_WORK = ("quizzes", "homework", "exams")


def count_remaining_work(scores, policy=None):
    """Count the blank items in each graded category."""

    policy = complete_policy(policy)
    prepared = prepare_scores(scores, policy)

    remaining = {
        category: sum(score is None for score in prepared[category])
        for category in GRADED_WORK
    }
    remaining["final"] = int(prepared["final"] is None)

    return remaining


def calculate_remaining_targets(scores, policy=None):
    """
    Find the score needed on every remaining item, including the
    final if it has not been taken, to reach each letter grade.

    The same score is assumed on every remaining item, and the
    policy's rules (bonus, drops, replacement) are applied to it.
    Blank attendance marks are not part of this score; if they
    alone decide a letter, it is "needs_other_work".
    """

    policy = complete_policy(policy)
    validate_policy(policy)

    remaining = count_remaining_work(scores, policy)

    if sum(remaining.values()) == 0:
        return {"remaining": remaining, "targets": {}}

    def grade_at(score):
        hypothetical_scores = fill_remaining_work(
            scores, policy, assume=score, categories=GRADED_WORK
        )

        if hypothetical_scores["final"] is None:
            hypothetical_scores["final"] = score

        return calculate_grade(
            hypothetical_scores, policy
        )["current_percentage"]

    best = calculate_best_possible_grade(scores, policy)["percentage"]

    targets = {
        letter: dict(
            mark_other_work_needed(
                find_minimum_score(grade_at, cutoff), best, cutoff
            ),
            cutoff=cutoff,
        )
        for letter, cutoff in policy["letter_cutoffs"].items()
    }

    return {"remaining": remaining, "targets": targets}


# --------------------------------------------------
# 13. EXPLAIN WHICH RULES FIRED
# --------------------------------------------------

def format_number(value):
    """Show a score like 90, 87.93, or 91.5 (at most 2 decimals)."""

    return f"{value:.2f}".rstrip("0").rstrip(".")


def explain_dropped_category(category, result, policy, drop_count,
                             min_completed):
    """Explain the bonus, drops, and average for quizzes or homework."""

    name = policy["category_names"].get(category, category)
    lines = []

    def add(rule, message):
        lines.append({"category": category, "rule": rule, "message": message})

    for item in result["adjusted"]:
        add(
            "bonus",
            f"{name} item {item['index'] + 1}: "
            f"{format_number(item['original_score'])} counted as "
            f"{format_number(item['adjusted_score'])} (above "
            f"{format_number(policy['quiz_cap_threshold'])}).",
        )

    for item in sorted(result["dropped"], key=lambda item: item["index"]):
        add(
            "drop",
            f"{name} item {item['index'] + 1}: "
            f"{format_number(item['adjusted_score'])} dropped "
            f"(lowest {drop_count} of {result['completed_count']} "
            "scored).",
        )

    if drop_count > 0 and not result["dropped"] and result["kept"]:
        add(
            "no_drop",
            f"No {name.lower()} dropped yet: the drop starts at "
            f"{min_completed} scores, and {result['completed_count']} "
            "are entered.",
        )

    if result["kept"]:
        kept = [format_number(item["adjusted_score"]) for item in result["kept"]]
        add(
            "average",
            f"{name} average: ({' + '.join(kept)}) / {len(kept)} = "
            f"{format_number(result['average'])}.",
        )

    return lines


def explain_grade(scores, policy=None):
    """
    Explain the current grade in plain language.

    Returns a list of {"category", "rule", "message"} items, in
    the order a student would read them. Rules include:
    marked_zero, bonus, drop, no_drop, average, replacement,
    left_out, formula.
    """

    policy = complete_policy(policy)
    result = calculate_grade(scores, policy)
    prepared = prepare_scores(scores, policy)
    names = policy["category_names"]
    categories = result["category_results"]
    lines = []

    def add(category, rule, message):
        lines.append({"category": category, "rule": rule, "message": message})

    # Items marked missing or excused
    for category in SCORED_CATEGORIES:
        for position, score in enumerate(scores.get(category, []), start=1):
            mark = zero_mark_name(score)

            if mark:
                add(category, "marked_zero",
                    f"{names[category]} item {position}: marked {mark}, "
                    "counted as 0.")

    mark = zero_mark_name(scores.get("final"))
    if mark:
        add("final", "marked_zero",
            f"{names['final']}: marked {mark}, counted as 0.")

    # Quizzes and homework
    lines += explain_dropped_category(
        "quizzes", categories["quizzes"], policy,
        policy["quiz_drop_lowest"], policy["quiz_drop_min_completed"],
    )
    lines += explain_dropped_category(
        "homework", categories["homework"], policy,
        policy["homework_drop_lowest"], policy["homework_drop_min_completed"],
    )

    # Attendance
    attendance = categories["attendance"]
    mark_names = {
        value: mark for mark, value in policy["attendance_values"].items()
    }

    for item in sorted(attendance["dropped"], key=lambda item: item["index"]):
        mark = mark_names.get(item["score"])
        shown = format_number(item["score"])
        if mark:
            shown = f"{mark} ({shown})"

        add(
            "attendance",
            "drop",
            f"{names['attendance']} item {item['index'] + 1}: {shown} "
            f"dropped (lowest {attendance['drop_count']} of "
            f"{attendance['completed_count']} marks).",
        )

    if attendance["average"] is not None:
        add(
            "attendance",
            "average",
            f"{names['attendance']} average: "
            f"{format_number(attendance['average'])} over "
            f"{len(attendance['kept'])} marks kept.",
        )

    # Exams and final replacement
    final = prepared["final"]
    exams = prepared["exams"]
    has_exams = any(score is not None for score in exams)

    if not policy["final_replaces_lowest_exam"]:
        add("final", "replacement",
            f"This course has no rule for the {names['final'].lower()} "
            "replacing an exam.")
    elif final is None:
        add("final", "replacement",
            f"{names['final']} not taken yet, so it cannot replace an "
            "exam yet.")
    elif not has_exams:
        add("final", "replacement",
            f"No {names['exams'].lower()} scored, so the "
            f"{names['final'].lower()} has nothing to replace.")
    else:
        replaced = next(
            index for index, (old, new) in enumerate(
                zip(exams, result["replacement_exam_scores"])
            )
            if old != new
        ) if exams != result["replacement_exam_scores"] else None

        with_text = format_number(result["grade_with_replacement"])
        without_text = format_number(result["grade_without_replacement"])

        if result["replacement_used"]:
            add("final", "replacement",
                f"{names['final']} ({format_number(final)}) replaced "
                f"{names['exams']} item {replaced + 1} "
                f"({format_number(exams[replaced])}): {with_text}% with "
                f"replacement vs {without_text}% without, so the higher "
                "one is used.")
        else:
            add("final", "replacement",
                f"{names['final']} ({format_number(final)}) did not "
                f"replace an exam: {with_text}% with replacement vs "
                f"{without_text}% without, so the higher one is used.")

    exam_scores = [
        score for score in (
            result["replacement_exam_scores"]
            if result["replacement_used"] else exams
        )
        if score is not None
    ]

    if exam_scores:
        shown = [format_number(score) for score in exam_scores]
        add("exams", "average",
            f"{names['exams']} average: ({' + '.join(shown)}) / "
            f"{len(shown)} = "
            f"{format_number(result['category_averages_used']['exams'])}.")

    # Weighted formula
    averages = result["category_averages_used"]
    weights = policy["weights"]
    used = [
        category for category in CATEGORIES
        if weights.get(category, 0) > 0 and averages.get(category) is not None
    ]
    left_out = [
        category for category in CATEGORIES
        if weights.get(category, 0) > 0 and averages.get(category) is None
    ]

    if left_out and used:
        counted = sum(weights[category] for category in used)
        total = sum(weights.get(category, 0) for category in CATEGORIES)
        add("overall", "left_out",
            f"No scores yet for "
            f"{', '.join(names[category] for category in left_out)}, "
            f"so {format_number(total - counted)}% of the weight is left "
            f"out and the other {format_number(counted)}% is rescaled "
            "to 100%.")

    if used:
        terms = " + ".join(
            f"{format_number(averages[category])} × "
            f"{format_number(weights[category])}"
            for category in used
        )
        counted = sum(weights[category] for category in used)
        add("overall", "formula",
            f"({terms}) / {format_number(counted)} = "
            f"{format_number(result['current_percentage'])}% → "
            f"{result['letter_grade']}.")
    else:
        add("overall", "formula", "No scores entered yet.")

    return lines


# --------------------------------------------------
# 14. HOW MUCH DID EACH RULE CHANGE THE GRADE?
# --------------------------------------------------

# Each rule: its category, how to name it, and the policy change
# that turns it off.
RULE_SWITCHES = {
    "quiz_bonus": (
        "quizzes", "bonus for {}", {"quiz_cap_threshold": 100}
    ),
    "quiz_drop": (
        "quizzes", "drop rule for {}", {"quiz_drop_lowest": 0}
    ),
    "homework_drop": (
        "homework", "drop rule for {}", {"homework_drop_lowest": 0}
    ),
    "attendance_drop": (
        "attendance", "drop rule for {}", {"attendance_drop_fraction": 0}
    ),
    "final_replacement": (
        "final", "{} replacement rule",
        {"final_replaces_lowest_exam": False},
    ),
}


def is_rule_enabled(policy, rule):
    """True if the policy has this rule turned on."""

    _, _, rule_off = RULE_SWITCHES[rule]

    return any(policy[setting] != value for setting, value in rule_off.items())


def compare_rules(scores, policy=None):
    """
    Show how much each syllabus rule changed the current grade.

    For every rule, the grade is calculated with the rule on and
    with it turned off. Returns a list of dicts with: rule, name,
    enabled, grade_with, grade_without, change (points), and a
    plain-language message.

    Returns an empty list when no scores are entered yet.
    """

    policy = complete_policy(policy)
    names = policy["category_names"]

    current = calculate_grade(scores, policy)
    grade_with = current["current_percentage"]

    if grade_with is None:
        return []

    comparisons = []

    for rule, (category, label, rule_off) in RULE_SWITCHES.items():
        name = label.format(names.get(category, category)).lower()

        if not is_rule_enabled(policy, rule):
            comparisons.append({
                "rule": rule,
                "name": name,
                "enabled": False,
                "grade_with": None,
                "grade_without": None,
                "change": None,
                "message": f"This course has no {name}.",
            })
            continue

        without = calculate_grade(scores, {**policy, **rule_off})
        grade_without = without["current_percentage"]
        change = grade_with - grade_without

        before = f"{grade_without:.2f}%"
        after = f"{grade_with:.2f}%"

        if abs(change) < 0.005:
            message = f"The {name} did not change your grade ({after})."
        else:
            direction = "raised" if change > 0 else "lowered"
            message = (
                f"The {name} {direction} your grade by "
                f"{abs(change):.2f} points ({before} → {after})"
            )

            letter_without = without["letter_grade"]
            if letter_without != current["letter_grade"]:
                message += (
                    f" and changed your letter from {letter_without} "
                    f"to {current['letter_grade']}"
                )

            message += "."

        comparisons.append({
            "rule": rule,
            "name": name,
            "enabled": True,
            "grade_with": grade_with,
            "grade_without": grade_without,
            "change": change,
            "message": message,
        })

    return comparisons


# --------------------------------------------------
# 15. ONE CALL FOR EVERYTHING
# --------------------------------------------------

def evaluate(scores, policy=None):
    """
    Check the inputs and calculate every result in one call.

    This is the main entry point for the interface. It never
    raises for bad input; problems come back in "errors".

    Returns:
        ok                - True if the inputs were usable
        errors            - list of plain-language problems
        policy            - the completed policy that was used
        current           - calculate_grade() result
        remaining         - count_remaining_work() result
        final_targets     - calculate_final_targets() result
        remaining_targets - calculate_remaining_targets() result
        best_possible     - calculate_best_possible_grade() result
        explanation       - explain_grade() result
        rule_impact       - compare_rules() result
        letter_outlook    - calculate_letter_outlook() result
    """

    errors = find_input_errors(scores, policy)

    if errors:
        return {"ok": False, "errors": errors}

    policy = complete_policy(policy)

    return {
        "ok": True,
        "errors": [],
        "policy": policy,
        "current": calculate_grade(scores, policy),
        "remaining": count_remaining_work(scores, policy),
        "final_targets": calculate_final_targets(scores, policy),
        "remaining_targets": calculate_remaining_targets(scores, policy),
        "best_possible": calculate_best_possible_grade(scores, policy),
        "explanation": explain_grade(scores, policy),
        "rule_impact": compare_rules(scores, policy),
        "letter_outlook": calculate_letter_outlook(scores, policy),
    }
