GRADE PILOT
CCSC Midwest 2026 Hackathon
Team: Maverick 3
Minnesota State University, Mankato

--------------------------------------------------
PROJECT DESCRIPTION
--------------------------------------------------

Grade Pilot is a student-friendly grade calculator and what-if planner built using Python and Streamlit for the CCSC Midwest 2026 Hackathon.

The application helps students understand their current course grades and explore how future assignment and exam scores could affect their final grades.

Students manually enter their course grading policies, assignment scores, and attendance records. Grade Pilot then applies the grading rules to calculate their current grade and allows them to explore different what-if scenarios.

--------------------------------------------------
FEATURES
--------------------------------------------------

1. Course Setup and Score Entry
   - Enter a course name and grading categories.
   - Customize category weights based on the syllabus.
   - Configure grading rules and letter grade cutoffs.
   - Enter quiz, homework, exam, and final exam scores.
   - Record attendance as Present, Late, or Absent.
   - Mark assignments as Completed, Not Yet Taken, Missing, or Excused.
   - Validate course weights and score entries.

2. Current Grade Calculation
   - Calculate the current course grade using category weights.
   - Apply grading policies such as dropping the lowest scores and adjusting quiz scores.
   - Exclude assignments that have not yet been taken.
   - Display the current grade and calculation breakdown.

3. What-If Grade Analysis
   - Enter hypothetical scores for upcoming assignments and exams.
   - Explore how future performance may affect the final grade.
   - Determine scores needed to reach a target letter grade.

--------------------------------------------------
TECHNOLOGIES USED
--------------------------------------------------

- Python: Grading logic and what-if calculations.
- Streamlit: Interactive web application.
- Git and GitHub: Version control and team collaboration.

--------------------------------------------------
INSTALLATION AND RUNNING
--------------------------------------------------

Requirements:
- Python 3
- pip

Steps:

1. Clone the GitHub repository and open the project folder.

2. Install the required dependencies:

   python -m pip install -r requirements.txt

3. Run the application:

   python -m streamlit run app.py

4. Open the local URL displayed in the terminal.

   The default address is http://localhost:8501

--------------------------------------------------
HOW TO USE
--------------------------------------------------

1. Launch Grade Pilot.

2. Enter the course name and grading categories.

3. Set the category weights and grading rules according to your syllabus.

4. Enter completed assignment scores and attendance records.

5. Mark future assignments as Not Yet Taken.

6. Review your current grade and calculation breakdown.

7. Use the What-If Analysis feature to explore possible future grades and target outcomes.

--------------------------------------------------
TEAM MEMBERS
--------------------------------------------------

Team Name: Maverick 3

Marwa Adem
Course Setup and Score Entry
Developed the course setup interface, grading preferences, score-entry tables, and input validation.

Ankinimbom Yuwenvoh
Grade Calculation
Implemented current-grade calculations based on course weights and grading rules.

Fenet Getachew
What-If Analysis
Developed grade predictions to help students explore possible outcomes.

School:
Minnesota State University, Mankato

--------------------------------------------------
REFERENCES
--------------------------------------------------

Development references, documentation, and AI tools used during the project are documented separately in References.txt.