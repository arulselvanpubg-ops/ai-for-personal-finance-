from datetime import datetime, timedelta

import streamlit as st

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from core.db import get_db_status
from utils.helpers import get_session_timeout_minutes
from utils.monitoring import log_event


def init_session_state():
    defaults = {
        "logged_in": False,
        "user_id": None,
        "user_email": None,
        "user_name": None,
        "last_activity": datetime.utcnow(),
        "session_notice": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_login_state():
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_email = None
    st.session_state.user_name = None


init_session_state()

st.set_page_config(
    page_title="FinSight AI",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .main-header {
        color: #0F4C5C;
        font-size: 2.5rem;
        font-weight: bold;
    }
    .sidebar .sidebar-content {
        background-color: #F4F9F9;
    }
    .stButton>button {
        background-color: #0F4C5C;
        color: white;
    }
</style>
""",
    unsafe_allow_html=True,
)

db_status = get_db_status()
if not db_status["ok"]:
    st.error(db_status["message"])
    st.stop()

from ui.budget import show_budget
from ui.chat_ui import show_chat
from ui.dashboard import show_dashboard
from ui.expenses import show_expenses
from ui.goals import show_goals
from ui.investments import show_investments
from ui.login import show_login_page
from ui.reports import show_reports

session_timeout_minutes = get_session_timeout_minutes()
now = datetime.utcnow()
last_activity = st.session_state.last_activity
if (
    isinstance(last_activity, datetime)
    and now - last_activity > timedelta(minutes=session_timeout_minutes)
):
    if st.session_state.logged_in:
        log_event("info", "session_expired", timeout_minutes=session_timeout_minutes)
    reset_login_state()
    st.session_state.session_notice = "Your session expired due to inactivity. Please sign in again."

st.session_state.last_activity = now

if not st.session_state.logged_in:
    if st.session_state.session_notice:
        st.info(st.session_state.session_notice)
        st.session_state.session_notice = None
    show_login_page()
else:
    col1, col2 = st.sidebar.columns([3, 1])
    with col1:
        st.sidebar.title("FinSight AI")
    with col2:
        if st.sidebar.button("Logout", key="logout_btn"):
            log_event("info", "logout_clicked", user=st.session_state.user_email)
            reset_login_state()
            st.rerun()

    st.sidebar.markdown(f"Welcome, **{st.session_state.user_name}**")
    st.sidebar.caption(f"Storage: `{db_status.get('backend', 'unknown')}`")
    if db_status.get("fallback_reason"):
        st.sidebar.caption("MongoDB was unavailable, so the app switched to the local fallback.")

    with st.sidebar.expander("System Status"):
        st.write(db_status["message"])
        if db_status.get("fallback_reason"):
            st.code(db_status["fallback_reason"])
        st.write(f"Session timeout: {session_timeout_minutes} minutes")

    st.sidebar.markdown("---")

    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Expenses", "Budget", "Investments", "Goals", "Chat", "Reports"],
        index=0,
    )

    if page == "Dashboard":
        show_dashboard()
    elif page == "Expenses":
        show_expenses()
    elif page == "Budget":
        show_budget()
    elif page == "Investments":
        show_investments()
    elif page == "Goals":
        show_goals()
    elif page == "Chat":
        show_chat()
    elif page == "Reports":
        show_reports()

    st.sidebar.markdown("---")
    st.sidebar.markdown("© 2026 FinSight AI")
