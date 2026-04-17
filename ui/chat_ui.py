import streamlit as st

from ai.router import route_ai_task
from utils.monitoring import log_event, log_exception
from utils.validators import sanitize_input


def show_chat():
    st.title("FinSight Chat")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("Ask me about your finances..."):
        prompt = sanitize_input(prompt, max_length=1000)
        if not prompt:
            st.warning("Please enter a message.")
            return

        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = route_ai_task(
                        "chat",
                        user_message=prompt,
                        history=st.session_state.chat_history,
                    )
                    log_event("info", "chat_prompt_processed", prompt_length=len(prompt))
                except Exception as exc:
                    log_exception("chat_ui_request_failed", exc)
                    response = "Sorry, something went wrong while sending your message."
                st.write(response)

        st.session_state.chat_history.append({"role": "assistant", "content": response})
