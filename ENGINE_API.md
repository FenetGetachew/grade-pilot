# Grading Engine API (Task 2)

All grading logic lives in `logic/grade_calculator.py`. It has no
Streamlit code. The UI (Task 1) and the what-if views (Task 3) call
these functions and never re-implement a grading formula.

Install and run:

```
pip install -r requirements.txt
streamlit run app.py
pytest
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

## How the app is connected

```
pages/course_setup.py  (Task 1)  saves course_policy, course_scores
        |
        v
logic/ui_adapter.py    convert_course_setup() -> engine policy + scores
        |
        v
logic/grade_calculator.py (Task 2)  evaluate()
        |
        v
pages/grade_results.py (Task 2)  current grade, explanation, rule impact
pages/what_if.py       (Task 3)  targets, best possible, letter outlook
```

The adapter maps setup-page category names to engine categories
(`"Quizzes"`/`"Quiz"`, `"Homework"`/`"HW"`, `"Exams"`/`"Midterms"`,
`"Final Exam"`/`"Final"`, `"Attendance"`). Rows with status
`"missing"` count as 0; `"excused"` rows are left out of the grade, as
the setup page says. Any other category name is reported as an error.

## For Task 3: building the what-if page

After the student opens the Results page, `st.session_state` holds:

| Key | Contents |
|---|---|
| `grade_results` | The full `evaluate()` result for the student's real scores |
| `engine_policy` | The engine policy (already converted) |
| `engine_scores` | The engine scores (already converted) |

To be safe if the student goes straight to the what-if page, rebuild
them the same way the Results page does:

```python
from logic.grade_calculator import evaluate
from logic.ui_adapter import convert_course_setup

converted = convert_course_setup(st.session_state.get("course_policy"),
                                 st.session_state.get("course_scores"))
if converted["ok"]:
    result = evaluate(converted["scores"], converted["policy"])
```

**Already calculated for you** (in `result`): `final_targets`,
`remaining_targets`, `best_possible`, `letter_outlook`, `rule_impact`,
and `current["grade_with_replacement"]` / `["grade_without_replacement"]`.

**Asking "what if?"**: change a copy of the engine scores or policy and
call `evaluate()` again. Never re-implement a formula.

```python
from copy import deepcopy

# What if I get 90 on the final?
what_if = deepcopy(converted["scores"])
what_if["final"] = 90
evaluate(what_if, converted["policy"])["current"]

# What if the homework drop rule were off?
no_drop = {**converted["policy"], "homework_drop_lowest": 0}
evaluate(converted["scores"], no_drop)["current"]
```

Ideas from the problem statement still open for the UI: save/reload a
policy and a set of scores (they are plain dicts, so `json.dumps` and
`json.loads` work), and a side-by-side with/without replacement view.

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
- `0` is a real zero.
- A quiz, homework, exam, or the final may be marked `"missing"` or
  `"excused"` (any case). Both count as 0, are not remaining work, and
  get an explanation line ("Homework item 3: marked missing, counted as 0.").
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
| `warnings` | Likely mistakes that did **not** stop the calculation, e.g. weights adding up to 99. Show them, but still show the results. |
| `policy` | The completed policy that was used |
| `current` | `calculate_grade()` result (below) |
| `remaining` | `{"quizzes": 1, "homework": 0, "exams": 0, "final": 1}` |
| `final_targets` | `calculate_final_targets()` result (below) |
| `remaining_targets` | `calculate_remaining_targets()` result (below) |
| `best_possible` | `calculate_best_possible_grade()` result (below) |
| `explanation` | `explain_grade()` result (below) |
| `rule_impact` | `compare_rules()` result (below) |
| `letter_outlook` | `calculate_letter_outlook()` result (below) |
| `attendance_status` | `calculate_attendance_status()` result (below) |

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
| `"needs_other_work"` | Not reachable this way at the assumed scores, but still possible with better scores on other remaining work | `None` |
| `"unreachable"` | Truly impossible: even perfect scores on all remaining work miss it | `None` |

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
one of: `marked_zero`, `bonus`, `drop`, `no_drop`, `average`,
`replacement`, `left_out`, `formula`.

### `letter_outlook`: "Can I still get an A?"

`{"best": 95.85, "worst": 64.95, "letters": {...}}`. Each letter has
`cutoff`, `status`, `can_still_reach` (True/False), and `message`:

| status | Meaning |
|---|---|
| `"secured"` | Reached even with zeros on all remaining work |
| `"possible"` | Reachable with good enough remaining work |
| `"impossible"` | Not reached even with perfect remaining work |

These are exact answers with no assumption about future scores, so use
them for "is it still possible?". The target statuses always agree
with them.

### `attendance_status`: "Will my next absence be dropped?"

`recorded`, `missed` (absent or late), `drops_now`,
`next_absence_covered`, `warning` (True when the next absence will
count), and `message`. If the policy sets `item_counts["attendance"]`
to the number of class days, it also gives `semester_drops` and
`absences_left` for the whole semester. Sample message:
`"Warning: your next absence will count against your grade. With 21 marks, only 1 would be dropped, and you already have 1 absent or late."`

### `rule_impact`

One item per rule (`quiz_bonus`, `quiz_drop`, `homework_drop`,
`attendance_drop`, `final_replacement`) with `name`, `enabled`,
`grade_with`, `grade_without`, `change` (points), and `message`, e.g.
`"The drop rule for homework raised your grade by 3.00 points (84.93% → 87.93%)."`
Rules the course does not have come back with `enabled: False`.
Empty when no scores are entered.

## Assumptions and interpretations

Where the problem statement leaves room for interpretation, the engine
makes these choices. Each one is covered by a test.

**Scores**
- Scores are percentages from 0 to 100. Extra credit above 100 is
  rejected; a UI that asks for points (e.g. 18/20) must convert first.
- A blank is remaining work, never a zero. `0`, `"missing"`, and
  `"excused"` are real zeros.

**Quizzes and homework**
- "Above 90%" means strictly above: a 90 stays 90, a 90.5 becomes 100.
- The quiz bonus is applied first, and drops compare the adjusted
  scores.
- Only scored items can be dropped. If two scores tie for lowest, the
  earlier one is dropped (the average is the same either way).
- A drop rule must always keep at least one score; a policy that would
  drop everything is rejected.

**Attendance**
- "Rounded to the nearest whole mark" rounds halves up: 10 marks x 5%
  = 0.5 -> 1 dropped; 30 marks -> 1.5 -> 2 dropped.
- The drop is based on marks recorded so far, and at least one mark
  is always kept.
- A late counts as a missed mark for the absence warning, since it
  scores below present.

**Final exam**
- When the final replaces the lowest exam, it still also counts in its
  own Final category. The final takes the lowest exam's place inside
  the Exams average.
- It replaces one exam (the lowest), and only if that raises the course
  percentage. Both percentages are always reported.

**Weights**
- Categories with no scores yet are left out, and the other weights are
  rescaled (e.g. divided by 75 instead of 100 before the final).
- Weights that do not add up to 100 are allowed (rescaled) but produce
  a warning.

**What is still possible**
- Final-only targets assume the student's other remaining work matches
  their current average in that category.
- Remaining-work targets assume the same score on every remaining item,
  including the final.
- Best possible = 100 on everything remaining; worst possible = 0. The
  letter outlook (secured / possible / impossible) uses only these, so
  it makes no guess about future performance.
- A required score is rounded **up** to the hundredth, so the number
  shown is always enough.

**Letters and categories**
- Letters are A, B, C, D, and F (no plus/minus).
- The five category types are fixed (quizzes, homework, exams, final,
  attendance); names, weights, counts, and rules are all configurable.
  A course without a category sets its weight to 0 or leaves it out.

## Function reference

### Main functions (Tasks 1 and 3 should only need these)

| Function | Purpose |
|---|---|
| `evaluate(scores, policy)` | **Main entry point.** Checks the inputs and returns every result. Never raises for bad input. |
| `find_input_errors(scores, policy)` | All problems with the policy and scores, as a list |
| `find_input_warnings(scores, policy)` | Likely mistakes that don't block: weights not adding to 100, a weighted category with 0 items, scores in a 0% category |
| `calculate_grade(scores, policy)` | Current percentage and letter, with and without final replacement |
| `explain_grade(scores, policy)` | Plain-language lines: which rules fired and the weighted formula |
| `compare_rules(scores, policy)` | How much each rule raised or lowered the grade (rule on vs off) |
| `calculate_final_targets(scores, policy)` | Final score needed per letter, with and without replacement |
| `calculate_remaining_targets(scores, policy)` | One score needed on all remaining work per letter |
| `calculate_best_possible_grade(scores, policy)` | Best grade still reachable |
| `calculate_worst_possible_grade(scores, policy)` | Lowest grade still possible (zeros on all remaining work) |
| `calculate_letter_outlook(scores, policy)` | Per letter: secured, possible, or impossible |
| `calculate_attendance_status(scores, policy)` | Whether the next absence is still covered by dropped marks |
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
| `convert_score_mark(score)` / `zero_mark_name(score)` | `"missing"` / `"excused"` to 0, and which word was used |
| `calculate_quiz_average(scores, policy)` | Quiz bonus, then drop the lowest |
| `calculate_homework_average(scores, policy)` | Drop the lowest homework once enough are scored |
| `calculate_dropped_average(...)` | Shared "adjust, then drop the lowest" logic |
| `calculate_exam_average(exams)` | Exam average, ignoring blanks |
| `replace_lowest_exam(exams, final)` | Copy of the exams with the lowest replaced |
| `calculate_attendance_average(marks, policy)` | Drop the lowest share of attendance marks |
| `count_attendance_drops(mark_count, policy)` | How many marks are dropped (nearest whole mark, keeps at least one) |
| `calculate_category_results(scores, policy)` | Every category average with rule details |
| `calculate_weighted_grade(averages, policy)` | Weighted grade; empty categories are left out and weights rescaled |
| `fill_remaining_work(scores, policy, assume)` | Fill blanks with the current average, 100, or a given score |
| `find_minimum_score(grade_at, cutoff)` | Shared binary search behind every "score needed" |
| `find_required_final(scores, policy, cutoff, mode)` | Final needed for one letter |
| `fill_every_blank(scores, policy, value)` | Every blank (and an untaken final) set to one value |
| `mark_other_work_needed(target, best, cutoff)` | Turns a not-truly-impossible "unreachable" into "needs_other_work" |
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
