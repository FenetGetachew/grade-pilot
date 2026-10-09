# Grade Pilot: Student Acceptance Test Report

**Branch:** `integration/engine-ui` (course setup UI + grading engine)
**Date:** 2026-10-09
**Result:** 60 PASS · 1 FAIL · 4 BLOCKED (65 checks)

**Recommendation:** ready to merge so Task 3 can start. **No grading-engine
calculation failures were found.** The one remaining failure (I-1) is on
the course setup page (`pages/course_setup.py`, Task 1). I-2, E-1, and
E-2 have been fixed.
The four blocked checks need the Task 3 what-if page.

## How this was tested

Every check plays a student using the real pages:

1. Open `pages/course_setup.py` and change it the way a student would:
   edit table cells (scores, statuses, attendance, categories), add or
   delete rows, and change the rule and cutoff settings.
2. Open `pages/grade_results.py` with what the setup page saved.
3. Compare what the page **displays** (and the `evaluate()` result behind
   it) with values calculated by hand from the syllabus.

The app was also started with `streamlit run app.py`. The home, course
setup, and results pages all loaded (HTTP 200) with no errors in the
server log.

Re-run everything:

```
pytest                                   # 182 passed, 1 xfailed
pytest -v tests/test_student_acceptance.py   # this report's checks
```

| Test file | Tests | What it covers |
|---|---|---|
| `tests/test_grade_calculator.py` | 103 | Grading engine (Task 2) |
| `tests/test_ui_adapter.py` | 27 | Setup-page format → engine |
| `tests/test_student_acceptance.py` | 53 | This report: real pages, student actions |

## Results

### 1. UI-to-engine integration (8 PASS)

| # | Check | Result | Evidence |
|---|---|---|---|
| 1.1 | App launches without errors | PASS | Real server: 3 pages HTTP 200, clean log. No exceptions in any page run. |
| 1.2 | UI imports and calls `evaluate()` | PASS | Results page stores an `ok: True` result |
| 1.3 | Scores passed correctly | PASS | Engine received quizzes `[80, 92, 70, None]`, homework `[100, 90, 80, 50]`, exams `[78, 88]`, final `None`, attendance 19×100 + 0 |
| 1.4 | Policy passed correctly / defaults used | PASS | Changed quiz threshold 95, homework drop 1, B cutoff 85: all reached the engine. Untouched settings match the sample. |
| 1.5 | Returned results displayed correctly | PASS | Shows 87.93%, B = engine value |
| 1.6 | Changing a score updates results | PASS | Quiz 2: 92 → 90 changes 87.93% → 86.93% |
| 1.7 | Invalid inputs don't crash | PASS | Scores −1 and 101 are rejected on the setup page with "Score must be between 0 and 100." |
| 1.8 | Understandable messages when `ok: False` | PASS | Messages are shown with no crash, e.g. "Attendance marks to drop must be at least 0% and less than 100%…" (fixed, see **I-2**) |

### 2. Score input and validation (7 PASS, 1 FAIL)

| # | Check | Result | Evidence |
|---|---|---|---|
| 2.1 | Valid scores 0–100 | PASS | Quiz 2 = 55.5 → 84.93% |
| 2.2 | Boundary scores | PASS | Quiz 2 = 0 → 84.93%, 90 → 86.93% (no bonus), 90.01 → 87.93% (bonus), 100 → 87.93% |
| 2.3 | Blank / not taken is `None`, not 0 | PASS | Quiz 4 arrives as `None`; quiz average uses 2 kept scores |
| 2.4 | A real 0 is kept | PASS | Exam 1 = 0 → exams `[0, 88]`, 67.13% D |
| 2.5 | Invalid −1, 101, non-numeric | PASS | −1 and 101 rejected. Non-numeric text cannot be typed into a number column (Streamlit treats it as blank → "Completed assignments must have a score.") |
| 2.6 | Missing or incomplete score lists | **FAIL** | Deleting rows, adding a 5th quiz, and deleting all exams all work (warning shown: "Exams is worth 40% but has 0 items"). **But** a new row with a score and a blank Status is silently ignored. See **I-1**. |
| 2.7 | Present, late, absent | PASS | Day 1 = Late → 75 sent to engine → 87.85% |
| 2.8 | Invalid attendance status rejected | PASS | "Attendance row 1: Select Present, Late, or Absent." |

### 3. Category calculations (9 PASS)

| # | Check | Result | Evidence |
|---|---|---|---|
| 3.1 | Quiz bonus above 90; exactly 90 gets none | PASS | "Quizzes item 2: 92 counted as 100 (above 90)."; 90 stays 90 |
| 3.2 | Quiz drop only when eligible | PASS | 1 quiz scored → no drop, average 80 |
| 3.3 | Untaken quiz is not zero / not dropped | PASS | Quiz 3 (70) dropped, not Quiz 4 |
| 3.4 | Configured homework drop | PASS | 80 and 50 dropped → 95 |
| 3.5 | Homework below / at / above threshold | PASS | 2 scores: no drop (95); 3: drop 2 (100); 4: drop 2 (95) |
| 3.6 | Exam average | PASS | "Exams average: (78 + 88) / 2 = 83." |
| 3.7 | Attendance values 100 / 75 / 0 | PASS | Engine received 100, 75, 0 |
| 3.8 | Attendance drop + keep-one safeguard | PASS | 5% of 20 → 1 dropped. 99% of 20 → 19 dropped, 1 kept. |
| 3.9 | Category with no completed scores | PASS | All quizzes not taken → left out, 87.42% |

### 4. Overall grade calculation (6 PASS)

| # | Check | Result | Evidence |
|---|---|---|---|
| 4.1 | Weights applied correctly | PASS | "(90 × 15 + 95 × 15 + 83 × 40 + 100 × 5) / 75 = 87.93% (B)." |
| 4.2 | Renormalized while final is open | PASS | "25% of the weight is left out and the other 75% is rescaled" |
| 4.3 | Unfinished final is not a zero | PASS | 87.93%, not 65.95% |
| 4.4 | Full policy when everything is scored | PASS | Quiz 4 = 85, final = 90 → 90.60% A, divided by 100 |
| 4.5 | Letter cutoffs at / below / above | PASS | A minimum 87.93 → A; 87.94 → B. Every boundary is also in the engine tests. |
| 4.6 | Displayed % and letter = engine values | PASS | Metric equals `evaluate()` result |

### 5. Final-exam replacement (5 PASS)

| # | Check | Result | Evidence |
|---|---|---|---|
| 5.1 | Replaces when it helps | PASS | Final 95 → 93.10% A, "Final Exam (95) replaced Exams item 1 (78)" |
| 5.2 | Does not replace when it would lower | PASS | Final 70 → 83.45% (with replacement would be 81.85%) |
| 5.3 | `replacement_used` correct | PASS | True for 95; False for 70 and 78 |
| 5.4 | Final equal to lowest exam (78) | PASS | 85.45% both ways, not used, as it does not *raise* the grade |
| 5.5 | UI shows each case | PASS | With/without metrics and the replaced / did-not-replace message |

### 6. Grade targets and remaining work (6 PASS, 1 BLOCKED)

These check the engine results produced from the student's UI input.
Displaying them is the Task 3 what-if page.

| # | Check | Result | Evidence |
|---|---|---|---|
| 6.1 | Final needed per letter | PASS | A 88.12 (with) / 96.2 (without); B 56.2; D locked |
| 6.2 | Remaining work includes quiz + final | PASS | Remaining: 1 quiz + final; 88.3 on both for an A |
| 6.3 | locked / needed / unreachable | PASS | D locked, A needed; exams 40 and 50 → A unreachable |
| 6.4 | Required score is enough (rounding) | PASS | Final 88.12 → 90.004% (A); 88.11 → 89.9995% (B) |
| 6.5 | Secured / achievable / unreachable | PASS | D secured, A possible; low exams → A impossible |
| 6.6 | Best possible: 100 on open work, earned final kept | PASS | 95.85%; with final 60 taken, 60 is kept |
| 6.7 | Remaining assignments shown in the UI | BLOCKED | Not displayed yet. The data is ready in `grade_results["remaining"]` for the what-if page. |

### 7. Explanations and transparency (6 PASS)

| # | Check | Result | Evidence |
|---|---|---|---|
| 7.1 | UI displays explanation messages | PASS | Every engine explanation line appears on the page |
| 7.2 | Quiz bonus identified | PASS | "Quizzes item 2: 92 counted as 100 (above 90)." |
| 7.3 | Dropped scores identified | PASS | Quiz 3 (70), Homework 3 (80), Homework 4 (50), attendance day 20 |
| 7.4 | Final replacement described | PASS | "Final Exam (95) replaced Exams item 1 (78): 93.1% with replacement vs 89.7% without…" |
| 7.5 | Displayed formula matches the result | PASS | Formula total = metric = engine value |
| 7.6 | Explanation updates with scores | PASS | Quiz 2 → 90: bonus line gone, "Quizzes average: (80 + 90) / 2 = 85." |

### 8. Regression and edge cases (8 PASS)

| # | Check | Result | Evidence |
|---|---|---|---|
| 8.1 | Task 2 suite runs | PASS | `pytest`: 182 passed, 1 xfailed (the known I-1 issue) |
| 8.2 | All earlier tests pass after integration | PASS | 130 / 130 engine + adapter tests pass |
| 8.3 | Official sample | PASS | 90 / 95 / 83 / 100 → 87.93% B; best 95.85% |
| 8.4 | Judges' modified scenarios | PASS | Quiz of 90, two homework scores, final that helps (95) and doesn't (70) |
| 8.5 | Simpler syllabus, rules off | PASS | Entered through the UI: Homework 30, Exams 45, Final 25, no drops, no replacement, A 93 → 80.50% C |
| 8.6 | No scores / all zeros / partial | PASS | "No scores entered yet…"; all zeros → 0.00% F; sample is partial |
| 8.7 | Invalid policies give useful errors | PASS | Weights ≠ 100, cutoffs out of order, unknown category "Labs", attendance drop 100% |
| 8.8 | No crashes during normal use | PASS | 0 exceptions across every page run; clean server log |

### 9. Task 3 what-if integration (5 PASS, 3 BLOCKED)

The what-if page does not exist yet, so these were tested at the engine
level using the exact data the Results page hands to Task 3
(`engine_scores`, `engine_policy`).

| # | Check | Result | Evidence |
|---|---|---|---|
| 9.1 | Task 3 can reuse `evaluate()` | PASS | Hypothetical final with the session's converted scores and policy; no formula copied |
| 9.2 | Hypothetical final changes the projection | PASS | 0 → 65.95%, 90 → 90.85%, 100 → 95.35% |
| 9.3 | Original scores not overwritten | PASS | `engine_scores["final"]` stays `None`; real grade stays 87.93% |
| 9.4 | Changing the hypothetical updates the page | BLOCKED | Needs the what-if page |
| 9.5 | Same rules as the main grade | PASS | Hypothetical final 95 = entering 95 on the setup page (same grade and explanation) |
| 9.6 | Hypotheticals at 0, 90, 100, cutoffs | PASS | 56.2 → exactly 80.00% B; 88.12 → 90.004% A |
| 9.7 | What-if page shows projections | BLOCKED | Needs the what-if page |
| 9.8 | Original grade restored when cleared | BLOCKED | Engine never changes the originals (9.3); the "clear" control needs the what-if page |

## Failures

### Integration issues (UI ↔ engine)

**I-1 · Medium · A typed score is ignored when Status is left blank** (check 2.6)

- **Steps:**
  1. Open Course Setup → Quizzes table → add a row "Quiz 5".
  2. Type 85 in Score and leave Status empty.
  3. Open the results page.
- **Expected:** the 85 counts as a completed quiz, or the page asks the student to pick a status.
- **Actual:** the row is treated as Not Yet Taken. The engine receives `None`, the 85 is ignored, and no message is shown.
- **Error message:** none.
- **Where to fix:** `pages/course_setup.py` (Task 1). A blank status defaults to `"Not Yet Taken"` even when a score is typed. Either treat a row that has a score as Completed, or show an error. The grading rules are correct as they are.
- **Test:** `test_s2_score_typed_but_status_left_not_taken` (marked xfail; it will pass once fixed).

**I-2 · Low · Attendance-drop error uses different units from the UI** (check 1.8) · **FIXED**

- **Steps:**
  1. Open Course Setup → Advanced grading rules.
  2. Set "Attendance marks to drop (%)" to 100.
  3. Open the results page.
- **Expected:** a message in the student's terms, e.g. "Attendance marks to drop must be less than 100%."
- **Actual:** "The attendance drop fraction must be at least 0 and less than 1." The UI allows 100 but the engine needs less than 100%.
- **Fix:** the adapter (`logic/ui_adapter.py`) now checks this setting
  and shows "Attendance marks to drop must be at least 0% and less than
  100%, so at least one mark still counts." The setup page was not changed.

### Grading-engine issues

**No calculation failures.** Two wording slips in explanation text (they did
not affect any number), both **FIXED**:

- E-1 · Low: "No quizzes dropped yet: … and **1 are** entered." now says "1 is".
- E-2 · Low: "Attendance average: 100 over **1 marks** kept." now says "1 mark".

## Blocked: waiting for Task 3

6.7, 9.4, 9.7, and 9.8 need `pages/what_if.py`. Everything it needs is
ready (see "For Task 3" in `ENGINE_API.md`). The engine side of each was
tested and passes.

## Open team decisions (not failures)

- **"Excused" meaning:** the setup page says "Excused = excluded", while
  the problem statement says "excused-as-zero". The current behavior
  follows the page. Changing it is one line in `logic/ui_adapter.py`.
- **Custom categories (e.g. "Labs"):** the page allows them, but the
  engine supports five category types. A student gets a clear error, not
  a crash.
