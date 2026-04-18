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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(90deg, #0F4C5C 0%, #06262F 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 1rem;
    }
    
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,255,255,0.6));
        border: 1px solid rgba(226, 232, 240, 0.8);
        padding: 1.5rem;
        border-radius: 1.2rem;
        box-shadow: 0 10px 30px -10px rgba(15, 76, 92, 0.1);
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px -10px rgba(15, 76, 92, 0.2);
    }
    
    .stButton>button {
        background: linear-gradient(90deg, #0F4C5C 0%, #156B82 100%);
        color: white;
        border: none;
        border-radius: 0.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(15, 76, 92, 0.2);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(15, 76, 92, 0.4);
        color: white;
        border: none;
    }
    
    div[data-testid="stSidebar"] {
        background-color: #F8FAFC;
        border-right: 1px solid #E2E8F0;
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
    
    # Show login page but also allow demo access
    col1, col2 = st.columns([1, 1])
    with col1:
        show_login_page()
    with col2:
        st.markdown("---")
        st.subheader("Quick Demo Access")
        st.info("Try the app without registration!")
        if st.button("Start Demo", type="primary", key="demo_access"):
            # Auto-login with demo user
            st.session_state.logged_in = True
            st.session_state.user_id = "demo_user"
            st.session_state.user_email = "demo@finsight.ai"
            st.session_state.user_name = "Demo User"
            st.session_state.last_activity = datetime.utcnow()
            st.rerun()
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
        
        st.divider()
        if st.button("🧪 Load Sample Data", help="Populate the app with sample transactions for a demo."):
            from core.db import Transaction
            count = Transaction.seed_dummy_data()
            st.success(f"Loaded {count} sample transactions!")
            st.rerun()

        if st.button("🗑️ Reset All Data", help="Permanently delete all transactions, goals, and investments.", type="secondary"):
            from core.db import get_collection
            for col_name in ["transactions", "goals", "investments", "budgets", "chat_history"]:
                # Logic to clear collection based on backend
                col = get_collection(col_name)
                # For simplicity, we can use a direct SQL if it's sqlite, or a generic way
                # But since we have a custom collection wrapper, let's just use it
                # Actually, our collection wrappers don't have 'delete_all'
                pass
            
            # Simple way: just run the script logic here
            import sqlite3
            import os
            db_path = os.getenv("SQLITE_DB_PATH", os.path.join("data", "finsight.db"))
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                conn.execute("DELETE FROM transactions")
                conn.execute("DELETE FROM goals")
                conn.execute("DELETE FROM investments")
                conn.execute("DELETE FROM budgets")
                conn.execute("DELETE FROM chat_history")
                conn.commit()
                conn.close()
                st.success("All data cleared!")
                st.rerun()

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
    st.sidebar.markdown(
        "© 2026 FinSight AI · Apache 2.0 "
        "([LICENSE](https://www.apache.org/licenses/LICENSE-2.0))"
    )
