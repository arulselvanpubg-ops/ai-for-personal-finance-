import streamlit as st

from core.auth import User
from utils.monitoring import log_event
from utils.validators import normalize_email, sanitize_input, validate_email


def show_login_page():
    """Display login/register page."""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.title("FinSight AI")
        st.markdown("---")

        tab1, tab2 = st.tabs(["Login", "Register"])

        with tab1:
            st.subheader("Login to Your Account")
            with st.form("login_form"):
                login_email = st.text_input(
                    "Email",
                    key="login_email",
                    placeholder="your@email.com",
                )
                login_password = st.text_input(
                    "Password",
                    type="password",
                    key="login_password",
                )

                if st.form_submit_button("Login", use_container_width=True):
                    login_email = normalize_email(login_email)
                    if not login_email or not login_password:
                        st.error("Please enter email and password.")
                    elif not validate_email(login_email):
                        st.error("Please enter a valid email address.")
                    else:
                        result = User.login(login_email, login_password)

                        if result["success"]:
                            st.session_state.user_id = result["user_id"]
                            st.session_state.user_email = result["email"]
                            st.session_state.user_name = result["name"]
                            st.session_state.logged_in = True
                            st.session_state.last_activity = None

                            st.success(f"Welcome back, {result['name']}!")
                            st.rerun()
                        else:
                            st.error(result["error"])

        with tab2:
            st.subheader("Create a New Account")
            with st.form("register_form"):
                reg_name = st.text_input(
                    "Full Name",
                    key="reg_name",
                    placeholder="John Doe",
                )
                reg_email = st.text_input(
                    "Email",
                    key="reg_email",
                    placeholder="your@email.com",
                )
                reg_password = st.text_input(
                    "Password",
                    type="password",
                    key="reg_password",
                )
                reg_confirm = st.text_input(
                    "Confirm Password",
                    type="password",
                    key="reg_confirm",
                )

                if st.form_submit_button("Register", use_container_width=True):
                    reg_name = sanitize_input(reg_name, max_length=80)
                    reg_email = normalize_email(reg_email)

                    if not reg_name or not reg_email or not reg_password or not reg_confirm:
                        st.error("Please fill in all fields.")
                    elif not validate_email(reg_email):
                        st.error("Please enter a valid email address.")
                    elif reg_password != reg_confirm:
                        st.error("Passwords do not match.")
                    elif len(reg_password) < 8:
                        st.error("Password must be at least 8 characters.")
                    else:
                        result = User.register(reg_email, reg_password, reg_name)

                        if result["success"]:
                            log_event("info", "register_completed_from_ui", email=reg_email)
                            st.success("Account created successfully! Please login.")
                            st.rerun()
                        else:
                            st.error(result["error"])

        st.markdown("---")
        st.markdown(
            "<p style='text-align: center; color: gray;'>Your personal AI finance assistant</p>",
            unsafe_allow_html=True,
        )
