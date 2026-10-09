# Grading Engine API (Task 2)

All grading logic lives in `logic/grade_calculator.py`. It has no
Streamlit code. The UI (Task 1) and the what-if views (Task 3) call
these functions and never re-implement a grading formula.

Run the tests with:

```
.venv/bin/python -m pytest
```

## Quick start

```python
from logic.grade_calculator import evaluate, DEFAULT_POLICY

result = evaluate(scores, policy)       # policy=None -> sample course

if not result["ok"]:
    for message in result["errors"]:
        ...                             # show each problem to the student
else:
    result["current"]["current_percentage"]   # 87.93...
    result["current"]["letter_grade"]         # "B"
    for line in result["explanation"]:
        line["message"]                       # "Quizzes item 2: 92 counted as 100 (above 90)."
```

## Input: `scores`

```python
scores = {
    "quizzes":    [80, 92, 70, None],
    "homework":   [100, 90, 80, 50],
    "exams":      [78, 88],
    "final":      None,
    "attendance": ["present"] * 19 + ["absent"],
}
```

- Scores are percentages from 0 to 100.
- `None` (blank) means **not taken yet**. It is remaining work, never a zero.
- `0` is a real zero. Use it for work the student marks missing or excused-as-zero.
- Attendance marks may be names from the policy (`"present"`, `"late"`,
  `"absent"`, any case) or numbers.
- Lists shorter than the policy's item count are padded with blanks.
  Any category can be left out.

## Input: `policy`

`None` uses `DEFAULT_POLICY` (the sample course). Use `DEFAULT_POLICY`
as the starting values for a policy form.

A policy may leave settings out. **A missing setting turns its rule off**,
and a missing weight counts as 0. For example, this is a complete policy:

```python
{
    "weights": {"homework": 30, "exams": 45, "final": 25},
    "item_counts": {"homework": 4, "exams": 3},
    "letter_cutoffs": {"A": 93, "B": 85, "C": 75, "D": 65},
}
```

| Setting | Sample value | Meaning |
|---|---|---|
| `category_names` | `{"quizzes": "Quizzes", ...}` | Names shown in messages |
| `weights` | `{"quizzes": 15, "homework": 15, "exams": 40, "final": 25, "attendance": 5}` | Category weights |
| `item_counts` | `{"quizzes": 4, "homework": 4, "exams": 2, "attendance": None}` | Items per category. `None` = no fixed count |
| `quiz_cap_threshold` / `quiz_cap_value` | `90` / `100` | A quiz **above** 90 counts as 100. Threshold 100 = off |
| `quiz_drop_lowest` / `quiz_drop_min_completed` | `1` / `2` | Drop the lowest 1 once 2 are scored. 0 = off |
| `homework_drop_lowest` / `homework_drop_min_completed` | `2` / `3` | Drop the lowest 2 once 3 are scored. 0 = off |
| `attendance_values` | `{"present": 100, "late": 75, "absent": 0}` | Score for each mark |
| `attendance_drop_fraction` | `0.05` | Drop this share of marks, rounded to the nearest whole mark |
| `final_replaces_lowest_exam` | `True` | The final replaces the lowest exam only if that raises the grade |
| `letter_cutoffs` | `{"A": 90, "B": 80, "C": 70, "D": 60}` | Below D is F |

The five category types (quizzes, homework, exams, final, attendance) are
fixed. Their names, weights, and rules can all change.

## Output of `evaluate(scores, policy)`

| Key | Contents |
|---|---|
| `ok` | `True` if the inputs were usable |
| `errors` | List of plain-language problems, e.g. `"Quizzes item 2: scores must be 0 to 100."` |
| `policy` | The completed policy that was used |
| `current` | `calculate_grade()` result (below) |
| `remaining` | `{"quizzes": 1, "homework": 0, "exams": 0, "final": 1}` |
| `final_targets` | `calculate_final_targets()` result (below) |
| `remaining_targets` | `calculate_remaining_targets()` result (below) |
| `best_possible` | `calculate_best_possible_grade()` result (below) |
| `explanation` | `explain_grade()` result (below) |
| `rule_impact` | `compare_rules()` result (below) |

When `ok` is `False`, only `ok` and `errors` are present.

### `current`

`current_percentage`, `letter_grade`, `grade_without_replacement`,
`grade_with_replacement` (None if the final isn't taken),
`replacement_used`, `replacement_exam_scores`,
`category_averages_used`, and `category_results`.

`category_results[category]` holds `average`, `completed_count`, and for
quizzes, homework, and attendance: `adjusted`, `dropped`, `kept` (each item
has an `index` counting from 0).

### Target results

Every letter target is `{"status": ..., "score": ..., "cutoff": ...}`:

| status | Meaning | score |
|---|---|---|
| `"locked"` | Reached even with a 0 | `0.0` |
| `"needed"` | Reachable | Minimum needed, rounded up to 0.01 |
| `"unreachable"` | Not reached even with a 100 | `None` |

- `final_targets["targets"][letter]["without_replacement"]` and
  `["with_replacement"]`. `with_replacement` is `None` when the course
  has no replacement rule. Other remaining work is assumed to match the
  student's current average in that category. If the final is already
  taken, `final_taken` is `True` and `targets` is empty.
- `remaining_targets["targets"][letter]`: one score needed on **every**
  remaining quiz, homework, exam, and the final. Empty if nothing remains.

### `best_possible`

`percentage`, `letter_grade`, `replacement_used`, `final_assumed`, and
`assumed_scores`. All blanks are treated as 100. A final that was
already taken keeps its real score.

### `explanation`

A list of `{"category", "rule", "message"}` in reading order. `rule` is
one of: `bonus`, `drop`, `no_drop`, `average`, `replacement`,
`left_out`, `formula`.

### `rule_impact`

One item per rule (`quiz_bonus`, `quiz_drop`, `homework_drop`,
`attendance_drop`, `final_replacement`) with `name`, `enabled`,
`grade_with`, `grade_without`, `change` (points), and `message`, e.g.
`"The drop rule for homework raised your grade by 3.00 points (84.93% → 87.93%)."`
Rules the course does not have come back with `enabled: False`.
Empty when no scores are entered.

## Function reference

### Main functions (Tasks 1 and 3 should only need these)

| Function | Purpose |
|---|---|
| `evaluate(scores, policy)` | **Main entry point.** Checks the inputs and returns every result. Never raises for bad input. |
| `find_input_errors(scores, policy)` | All problems with the policy and scores, as a list |
| `calculate_grade(scores, policy)` | Current percentage and letter, with and without final replacement |
| `explain_grade(scores, policy)` | Plain-language lines: which rules fired and the weighted formula |
| `compare_rules(scores, policy)` | How much each rule raised or lowered the grade (rule on vs off) |
| `calculate_final_targets(scores, policy)` | Final score needed per letter, with and without replacement |
| `calculate_remaining_targets(scores, policy)` | One score needed on all remaining work per letter |
| `calculate_best_possible_grade(scores, policy)` | Best grade still reachable |
| `count_remaining_work(scores, policy)` | Items not yet taken in each category |
| `get_letter_grade(percentage, policy)` | Percentage to A, B, C, D, or F |
| `complete_policy(policy)` | The full policy with missing settings filled in |
| `DEFAULT_POLICY` | The sample course policy |

### Helpers (used inside the engine)

| Function | Purpose |
|---|---|
| `find_policy_errors(policy)` | Problems with the policy only |
| `find_score_errors(scores, policy)` | Problems with the scores only |
| `validate_policy(policy)` | Raises `ValueError` listing every policy problem |
| `validate_score(score)` | Raises `ValueError` unless the score is blank or 0 to 100 |
| `find_drop_rule_errors(policy, category)` | Checks a drop rule always keeps a score |
| `is_number(value)` / `is_whole_number(value)` | Type checks (`True`/`False` are not numbers) |
| `prepare_scores(scores, policy)` | Converts attendance names and pads lists with blanks |
| `convert_attendance_mark(mark, policy)` | `"late"` to its number |
| `calculate_quiz_average(scores, policy)` | Quiz bonus, then drop the lowest |
| `calculate_homework_average(scores, policy)` | Drop the lowest homework once enough are scored |
| `calculate_dropped_average(...)` | Shared "adjust, then drop the lowest" logic |
| `calculate_exam_average(exams)` | Exam average, ignoring blanks |
| `replace_lowest_exam(exams, final)` | Copy of the exams with the lowest replaced |
| `calculate_attendance_average(marks, policy)` | Drop the lowest share of attendance marks |
| `calculate_category_results(scores, policy)` | Every category average with rule details |
| `calculate_weighted_grade(averages, policy)` | Weighted grade; empty categories are left out and weights rescaled |
| `fill_remaining_work(scores, policy, assume)` | Fill blanks with the current average, 100, or a given score |
| `find_minimum_score(grade_at, cutoff)` | Shared binary search behind every "score needed" |
| `find_required_final(scores, policy, cutoff, mode)` | Final needed for one letter |
| `explain_dropped_category(...)` | Explanation lines for quizzes or homework |
| `format_number(value)` | Shows 90, 87.93, or 91.5 |
| `is_rule_enabled(policy, rule)` | True if the policy has that rule turned on |

## Adding a new rule option

1. Add the setting to `DEFAULT_POLICY` and its "off" value to `RULES_OFF_POLICY`.
2. Add a check to `find_policy_errors`.
3. Apply the rule in the function for its category.
4. Add it to `RULE_SWITCHES` so `compare_rules` can turn it off.
5. Add an explanation line in `explain_grade` and a test in
   `tests/test_grade_calculator.py`.
