"""Visual styles only. No course logic or grade calculations."""
'''
from pathlib import Path
import streamlit as st

def apply_styles(page: str = "course") -> None:
    css_file = Path(__file__).with_name("home.css" if page == "home" else "course.css")
    st.markdown(f"<style>{css_file.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
'''
"""Visual styles only. No course logic or grade calculations."""
from pathlib import Path
import streamlit as st


def apply_styles(page: str = "course") -> None:
    css_file = Path(__file__).with_name(
        "home.css" if page == "home" else "course.css"
    )

    css = css_file.read_text(encoding="utf-8")

    st.markdown(
        f"""
        <style>
        {css}

        [data-testid="stSidebar"] {{
            background: #CDDFEF !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
st.markdown("""
<style>
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div {
    background: #CDDFEF !important;
}
</style>
""", unsafe_allow_html=True)