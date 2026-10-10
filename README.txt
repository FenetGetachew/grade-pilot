GRADE PILOT
CCSC Midwest 2026 Hackathon
Team: Maverick 3
Minnesota State University, Mankato

--------------------------------------------------
PROJECT DESCRIPTION
--------------------------------------------------

Grade Pilot is a student-friendly grade calculator and what-if planner built using Python and Streamlit for the CCSC Midwest 2026 Hackathon.

Students enter the grading rules from their syllabus, their assignment scores, and their attendance. Grade Pilot then calculates their current grade, explains how every syllabus rule affected it, and shows what they still need to reach each letter grade.

--------------------------------------------------
FEATURES
--------------------------------------------------

1. Course Setup and Score Entry
   - Enter a course name, grading categories, and category weights (the weights must total 100%).
   - Configure the grading rules, or turn them off:
       Quiz bonus: quizzes strictly above a threshold (90% by default) count as 100%.
       Drop the lowest quizzes and the lowest homework scores, once enough are scored.
       Drop a percentage of attendance marks (5% by default).
       The final exam replaces the lowest exam, only when that raises the grade.
   - Set the letter-grade cutoffs (A 90, B 80, C 70, D 60 by default).
   - Enter quiz, homework, exam, and final exam scores, and mark each item:
       Completed = a graded score
       Not Yet Taken = future work, never counted as a zero
       Missing = counts as 0
       Excused = left out of the grade
   - Record attendance as Present (100%), Late (75%), or Absent (0%). A day without a mark is not counted yet.
   - The page starts blank so students enter their own grades. "Load sample scores" fills in the hackathon sample course, and "Clear all scores" empties everything.
   - Typing a score into a "Not Yet Taken" row marks it Completed.
   - Entries are kept while moving between pages.
   - Every entry is checked. Problems are listed in plain language, and the results button stays disabled until they are fixed.

2. Grade Results
   - Show the current grade with an animated progress ring and a letter badge.
   - Show the grade with and without final-exam replacement, and which one is used.
   - Show a card for each category with its weight, average, completion status, and the rules applied (bonuses, dropped scores, replacement).
   - Show a detailed breakdown: each category's share of the grade, its contribution, the total scored weight, and the full weighted formula.
   - Show how much each syllabus rule raised or lowered the grade.
   - Show attendance statistics, and warn when the next absence will no longer be dropped.
   - Summarize what is still possible: best and lowest possible grade, the final-exam score needed for each letter, and the same score needed on all remaining work.

3. What-If Planner
   - Best possible grade if all remaining work earns 100%.
   - Final-exam score needed for each letter, with and without the replacement rule.
   - One score needed on every remaining item for each letter.
   - Which letters are secured, still possible, or no longer possible.
   - Enter assumed scores for remaining work to see the projected grade. The real grade never changes, and "Reset assumed scores" starts over.

4. Design
   - A pastel campus theme on every page, in both light and dark mode. The app follows the computer's light or dark setting, and the theme can be changed in the app menu (Settings > Theme).
   - Animations respect the system "reduce motion" setting.

--------------------------------------------------
HOW GRADES ARE CALCULATED
--------------------------------------------------

All grading happens in logic/grade_calculator.py. The interface never calculates a grade itself.

- Current grade: each category is averaged after its rules are applied. Categories with no scores yet are left out, and the remaining weights are rescaled to 100%. For example, before the final is taken, the other categories' 75% of the weight counts as 100%.
- Final replacement: the grade is calculated both ways, and the higher one is kept.
- Targets: the score needed for each letter is found with a binary search over the same grading rules and is rounded up, so the score shown is always enough. A letter is only called unreachable when even perfect scores on all remaining work cannot reach it.
- Attendance: the number of marks dropped is rounded to the nearest whole mark (halves round up), and at least one mark is always kept.

ENGINE_API.md lists every function, the input and output formats, and all assumptions.

--------------------------------------------------
TECHNOLOGIES USED
--------------------------------------------------

- Python: grading engine, validation, and what-if calculations.
- Streamlit: interactive web application.
- pytest: automated tests.
- Git and GitHub: version control and team collaboration.

--------------------------------------------------
INSTALLATION AND RUNNING
--------------------------------------------------

Requirements:
- Python 3
- pip

Steps:

1. Clone the GitHub repository and open the project folder.

2. Install the required dependencies (Streamlit 1.65 or newer):

   python -m pip install -r requirements.txt --upgrade

3. Run the application:

   python -m streamlit run app.py

4. Open the local URL displayed in the terminal.

   The default address is http://localhost:8501

--------------------------------------------------
HOW TO USE
--------------------------------------------------

1. Launch Grade Pilot and click "Get started".

2. Enter the course name, grading categories, and weights.

3. Adjust the grading rules and letter cutoffs to match your syllabus. To try the hackathon sample instead, click "Load sample scores".

4. Enter your scores and mark each item Completed, Not Yet Taken, Missing, or Excused. Record your attendance.

5. Click "View grade results" to see your current grade and how it was calculated.

6. Open the What-If Planner to see what you need on your remaining work and to try your own scores.

--------------------------------------------------
TESTING
--------------------------------------------------

Run all 211 automated tests with:

   python -m pytest

- tests/test_grade_calculator.py: the grading engine, including the hackathon sample (87.93%, B), the judges' changes, a simpler syllabus, and edge cases.
- tests/test_ui_adapter.py: converting the setup page's entries for the grading engine.
- tests/test_student_acceptance.py: the real pages used like a student would, from score entry to results and the What-If Planner.

TEST_REPORT.md records the acceptance checks and their results.

--------------------------------------------------
PROJECT STRUCTURE
--------------------------------------------------

app.py                      Home page
pages/course_setup.py       Course setup and score entry
pages/grade_results.py      Current grade, explanations, and targets
pages/what_if.py            What-If Planner
logic/grade_calculator.py   Grading engine: validation, syllabus rules, grades, targets, explanations
logic/ui_adapter.py         Converts the setup page's entries into the grading engine's format
data_models.py              The hackathon sample course and scores
ui/pastel.py                Shared page styling
.streamlit/config.toml      Light and dark theme colors
tests/                      Automated tests
ENGINE_API.md               Grading engine reference and assumptions
TEST_REPORT.md              Acceptance test report

--------------------------------------------------
TEAM MEMBERS
--------------------------------------------------

Team Name: Maverick 3

Marwa Adem
Course Setup and Score Entry
Developed the course setup interface, grading preferences, score-entry tables, and input validation.

Ankinimbom Yuwenyoh
Grade Calculation and Integration
Developed the grading engine, the Grade Results page, the connection between the pages and the engine, and the automated tests.

Fenet Getachew
What-If Analysis
Developed the What-If Planner to help students explore possible outcomes.

School:
Minnesota State University, Mankato

--------------------------------------------------
REFERENCES
--------------------------------------------------

Development references, documentation, and AI tools used during the project are listed in References.txt.
