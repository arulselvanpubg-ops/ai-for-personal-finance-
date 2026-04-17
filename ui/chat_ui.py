import streamlit as st
from ai.router import route_ai_task

def show_chat():
    st.title("🤖 FinSight Chat")
    
    # Initialize chat history in session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history
    for msg in st.session_state.chat_history:
        if msg['role'] == 'user':
            st.chat_message("user").write(msg['content'])
        else:
            st.chat_message("assistant").write(msg['content'])
    
    # Chat input
    if prompt := st.chat_input("Ask me about your finances..."):
        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = route_ai_task('chat', user_message=prompt, history=st.session_state.chat_history)
                st.write(response)
        
        # Add AI response to history
        st.session_state.chat_history.append({"role": "assistant", "content": response})