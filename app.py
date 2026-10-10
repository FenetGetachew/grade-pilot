import streamlit as st

from ui.pastel import apply_pastel_theme, eyebrow, icon

st.set_page_config(page_title="Grade Pilot | Home", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")

apply_pastel_theme()

# Home page layout, in the same style as the Grade Results page.
st.markdown("""<style>
.gp-home-hero {position: relative; overflow: hidden; padding: 2.4rem 2.6rem; border-radius: 26px;
  border: 1px solid var(--gp-border); background: linear-gradient(130deg, var(--gp-blue), var(--gp-lavender));
  box-shadow: 0 10px 28px var(--gp-shadow); margin: .2rem 0 2rem;}
.gp-home-hero::after {content: ""; position: absolute; right: -60px; top: -60px; width: 240px; height: 240px;
  border-radius: 50%; background: radial-gradient(circle, var(--gp-glow), transparent 70%); pointer-events: none;}
.gp-home-hero .title {font-size: 3rem; font-weight: 800; letter-spacing: -.035em; color: var(--gp-ink);
  line-height: 1.1; margin-bottom: .8rem;}
.gp-home-hero .lead {font-size: 1.2rem; line-height: 1.55; color: var(--gp-text); max-width: 720px;
  position: relative; z-index: 1;}
.gp-steps-title {font-size: 1.55rem; font-weight: 750; color: var(--gp-ink); margin: 0 0 1rem;}
.gp-steps {display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 1rem; margin-bottom: 1.6rem;}
.gp-step {border-top: 5px solid var(--accent);}
.gp-step .tile {width: 2.6rem; height: 2.6rem; border-radius: 14px; display: flex; align-items: center;
  justify-content: center; margin-bottom: .8rem;}
.gp-step .name {font-size: 1.15rem; font-weight: 750; color: var(--gp-ink); margin-bottom: .35rem;}
.gp-step .body {font-size: 1rem; line-height: 1.5; color: var(--gp-text);}
</style>""", unsafe_allow_html=True)


st.sidebar.markdown("### 🎓 Grade Pilot")
st.sidebar.caption("Your course grade planner")

eyebrow("final", "Your course grade planner")
st.markdown(
    '<div class="gp-home-hero"><div class="title">Grade Pilot</div>'
    '<div class="lead">A simpler way to organize your syllabus and track your coursework. '
    "Start by setting up your course and entering your grades.</div></div>",
    unsafe_allow_html=True,
)

STEPS = [
    ("setup", "blue", "1. Set up your course", "Add your course name, grading categories, and syllabus rules."),
    ("edit", "mint", "2. Enter your grades", "Record assignments and attendance, and mark work that is still to come."),
    ("chart", "lavender", "3. See your current grade", "Get your grade, letter, and a step-by-step explanation of every rule."),
    ("compass", "yellow", "4. Plan ahead", "Use the What-If Planner to see what you need on the work that is left."),
]
st.markdown(
    '<div class="gp-steps-title">Get started</div><div class="gp-steps">'
    + "".join(
        f'<div class="gp-card gp-step" style="--accent: var(--gp-{accent}-ink)">'
        f'<div class="tile acc-{accent}">{icon(icon_name)}</div>'
        f'<div class="name">{name}</div><div class="body">{body}</div></div>'
        for icon_name, accent, name, body in STEPS
    )
    + "</div>",
    unsafe_allow_html=True,
)

if st.button("Get started", type="primary"):
    st.switch_page("pages/course_setup.py")
st.caption("Then see your current grade on the Grade Results page, and plan ahead with the What-If Planner.")
