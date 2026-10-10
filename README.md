# Grade Pilot

Grade Pilot is a Python and Streamlit web app built for the CCSC Midwest 2026 Hackathon. Students enter the grading rules from their syllabus and their scores so far. Grade Pilot then shows their current grade, explains how every syllabus rule affected it, and shows what they still need to reach each letter grade.

**Team Maverick 3**, Minnesota State University, Mankato

## Features

### Course setup and score entry

- Course name, grading categories, and category weights (the weights must total 100%).
- Grading rules you can change or turn off:
  - Quiz bonus: quizzes strictly above a threshold (90% by default) count as 100%.
  - Drop the lowest quizzes and the lowest homework scores, once enough are scored.
  - Drop a percentage of attendance marks (5% by default).
  - The final exam replaces the lowest exam, only when that raises the grade.
- Letter-grade cutoffs (A 90, B 80, C 70, D 60 by default).
- Score entry for quizzes, homework, exams, and the final, with a status for each item:
  - **Completed**: a graded score.
  - **Not Yet Taken**: future work. It is never counted as a zero.
  - **Missing**: counts as 0.
  - **Excused**: left out of the grade.
- Attendance marked Present (100%), Late (75%), or Absent (0%). A day without a mark is not counted yet.
- The page starts blank so students enter their own grades. **Load sample scores** fills in the hackathon sample course, and **Clear all scores** empties everything.
- Typing a score into a "Not Yet Taken" row marks it Completed.
- Entries are kept while moving between pages, and every entry is checked: problems are listed in plain language, and the results button stays disabled until they are fixed.

### Grade results

- The current grade with an animated progress ring and a letter badge.
- The grade with and without final-exam replacement, and which one is used.
- A card for each category with its weight, average, completion status, and the rules applied (bonuses, dropped scores, replacement).
- A detailed breakdown: each category's share of the grade, its contribution, the total scored weight, and the full weighted formula.
- How much each syllabus rule raised or lowered the grade.
- Attendance statistics, and a warning when the next absence will no longer be dropped.
- A "Looking ahead" summary: best and lowest possible grade, the final-exam score needed for each letter, and the same score needed on all remaining work.

### What-If Planner

- Best possible grade if all remaining work earns 100%.
- Final-exam score needed for each letter, with and without the replacement rule.
- One score needed on every remaining item for each letter.
- Which letters are secured, still possible, or no longer possible.
- "Try your own scores": enter assumed scores for remaining work to see the projected grade. The student's real grade never changes, and **Reset assumed scores** starts over.

### Design

- A pastel campus theme on every page, in both light and dark mode. The app follows the computer's light or dark setting, and the theme can be changed in the app menu (Settings > Theme).
- Animations respect the system "reduce motion" setting.

## How grades are calculated

All grading happens in `logic/grade_calculator.py`. The interface never calculates a grade itself.

- **Current grade:** each category is averaged after its rules are applied. Categories with no scores yet are left out, and the remaining weights are rescaled to 100%. For example, before the final is taken, the other categories' 75% of the weight counts as 100%.
- **Final replacement:** the grade is calculated both ways, and the higher one is kept.
- **Targets:** the score needed for each letter is found with a binary search over the same grading rules and is rounded up, so the score shown is always enough. A letter is only called unreachable when even perfect scores on all remaining work cannot reach it.
- **Attendance:** the number of marks dropped is rounded to the nearest whole mark (halves round up), and at least one mark is always kept.

`ENGINE_API.md` lists every function, the input and output formats, and all assumptions.

## Installation and running

Python 3 and pip are required.

1. Clone this repository and open its folder in a terminal.
2. Install the dependencies (Streamlit 1.65 or newer):

   ```
   python -m pip install -r requirements.txt --upgrade
   ```

3. Start the app:

   ```
   python -m streamlit run app.py
   ```

4. Open the local address shown in the terminal (by default http://localhost:8501).

## How to use

1. Click **Get started** on the home page.
2. Enter your course name, categories, and weights, and adjust the grading rules and letter cutoffs if your syllabus differs. To try the hackathon sample instead, click **Load sample scores**.
3. Enter your scores, and mark each item Completed, Not Yet Taken, Missing, or Excused. Record your attendance.
4. Click **View grade results** to see your current grade and how it was calculated.
5. Open the **What-If Planner** to see what you need on your remaining work and to try your own scores.

## Testing

```
python -m pytest
```

The suite has 211 automated tests:

- `tests/test_grade_calculator.py`: the grading engine, including the hackathon sample (87.93%, B), the judges' changes, a simpler syllabus, and edge cases.
- `tests/test_ui_adapter.py`: converting the setup page's entries for the grading engine.
- `tests/test_student_acceptance.py`: the real pages used like a student would, from score entry to results and the What-If Planner.

`TEST_REPORT.md` records the acceptance checks and their results.

## Project structure

| Path | Contents |
|---|---|
| `app.py` | Home page |
| `pages/course_setup.py` | Course setup and score entry |
| `pages/grade_results.py` | Current grade, explanations, and targets |
| `pages/what_if.py` | What-If Planner |
| `logic/grade_calculator.py` | Grading engine: validation, syllabus rules, grades, targets, explanations |
| `logic/ui_adapter.py` | Converts the setup page's entries into the grading engine's format |
| `data_models.py` | The hackathon sample course and scores |
| `ui/pastel.py` | Shared page styling |
| `.streamlit/config.toml` | Light and dark theme colors |
| `tests/` | Automated tests |
| `ENGINE_API.md` | Grading engine reference and assumptions |
| `TEST_REPORT.md` | Acceptance test report |

## Team

| Member | Role |
|---|---|
| Marwa Adem | Course setup and score entry |
| Ankinimbom Yuwenyoh | Grading engine, grade results, and integration |
| Fenet Getachew | What-If Planner |

Minnesota State University, Mankato

## References

Websites, documentation, and AI tools used during development are listed in `References.txt`.
