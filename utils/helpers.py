"""Helper functions for the Connecticut Legal Assistant."""
import re
import streamlit as st

def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []

    if 'url_tracker' not in st.session_state:
        st.session_state.url_tracker = {}
        
    if 'vectorstore' not in st.session_state:
        st.session_state.vectorstore = None

def update_conversation_history(query, response):
    """Update the conversation history with a new exchange.
    
    Args:
        query: User query
        response: Assistant response
    """
    st.session_state.conversation_history.append({"role": "user", "content": query})
    st.session_state.conversation_history.append({"role": "assistant", "content": response})

def display_conversation_history():
    """Display the conversation history in the Streamlit UI."""
    for message in st.session_state.conversation_history:
        if message["role"] == "user":
            st.chat_message("user").write(message["content"])
        else:
            st.chat_message("assistant").write(message["content"])