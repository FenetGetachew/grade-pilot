import streamlit as st

st.set_page_config(page_title="Grade Pilot | Home", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")

st.markdown("""<style>
.block-container {max-width: 1450px; padding-top: 2.6rem;}
h1 {font-size: 3.4rem !important; letter-spacing: -.04em; line-height: 1.15 !important;}
h2 {font-size: 1.75rem !important;}
p, label, [data-testid="stMarkdownContainer"] {font-size: 1.08rem;}
.hero {background: var(--background-color); padding: 2.5rem; border-radius: 22px; border: 1px solid var(--divider-color);}
.hero h1 {color: var(--text-color); margin: 0 0 1rem;}
.hero p {font-size: 1.25rem; color: var(--text-color); max-width: 700px;}
.info-card {background: var(--background-color); border: 1px solid var(--divider-color); border-radius: 16px; padding: 1.3rem; min-height: 145px;}
.info-card h3 {font-size: 1.35rem; margin: .1rem 0 .5rem; color: var(--text-color);}
.info-card p {font-size: 1.02rem; color: var(--text-color);}
</style>""", unsafe_allow_html=True)


st.sidebar.markdown("### 🎓 Grade Pilot")
st.sidebar.caption("Your course grade planner")

st.markdown('''<div class="hero"><h1>Grade Pilot</h1><p>A simpler way to organize your syllabus and track your coursework. Start by setting up your course and entering your grades.</p></div>''', unsafe_allow_html=True)
st.write("")
st.write("")
st.subheader("Get started")
left, right = st.columns(2, gap="large")
with left:
    st.markdown('''<div class="info-card"><h3>1. Set up your course</h3><p>Add your course name, grading categories, and syllabus rules.</p></div>''', unsafe_allow_html=True)
with right:
    st.markdown('''<div class="info-card"><h3>2. Enter your grades</h3><p>Record assignments and attendance in organized tabs.</p></div>''', unsafe_allow_html=True)
st.write("")
if st.button("Get started →", type="primary", use_container_width=False):
    st.switch_page("pages/course_setup.py")
st.caption("Grade calculations and what-if results will be added by the other team members.")
