import streamlit as st
import os

# Load environment variables - handle both local and Streamlit Cloud
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available on Streamlit Cloud

from core.db import get_db_status

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_email = None
    st.session_state.user_name = None

# Page config
st.set_page_config(
    page_title="FinSight AI",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for theme
st.markdown("""
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
""", unsafe_allow_html=True)

db_status = get_db_status()
if not db_status["ok"]:
    st.error(db_status["message"])
    st.info(
        "On Streamlit Cloud, open your app settings and add `MONGODB_URI` under Secrets. "
        "You can also set `MONGODB_DB_NAME` if you do not want to use the default `finsight` database."
    )
    st.stop()

# Import modules after the database health check succeeds so Streamlit can
# render a controlled error state instead of failing during module import.
from ui.dashboard import show_dashboard
from ui.expenses import show_expenses
from ui.budget import show_budget
from ui.investments import show_investments
from ui.goals import show_goals
from ui.chat_ui import show_chat
from ui.reports import show_reports
from ui.login import show_login_page

# Check if user is logged in
if not st.session_state.logged_in:
    # Show login page
    show_login_page()
else:
    # Sidebar navigation
    col1, col2 = st.sidebar.columns([3, 1])
    with col1:
        st.sidebar.title(f"FinSight AI")
    with col2:
        if st.sidebar.button("Logout", key="logout_btn"):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.user_email = None
            st.session_state.user_name = None
            st.rerun()
    
    st.sidebar.markdown(f"Welcome, **{st.session_state.user_name}**")
    st.sidebar.markdown("---")

    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Expenses", "Budget", "Investments", "Goals", "Chat", "Reports"],
        index=0
    )

    # Main content
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

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("© 2026 FinSight AI")
