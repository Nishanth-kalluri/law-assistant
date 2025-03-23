"""
Connecticut Legal Tools - Streamlit Application
A suite of tools for legal assistance, argument practice, and court simulation.
"""
import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import page functions
from page_modules.landing import show_landing_page
from page_modules.legal_assistant import show_legal_assistant
from page_modules.argument_practice import show_argument_practice
from page_modules.court_simulator import show_court_simulator

# Import utility functions
from utils.ui import build_sidebar, apply_custom_css
from utils.helpers import initialize_session_state

def initialize_extended_session_state():
    """Initialize extended session state variables."""
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "landing"
    
    # Original session state variables
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'vectorstore' not in st.session_state:
        st.session_state.vectorstore = None
    if 'url_tracker' not in st.session_state:
        st.session_state.url_tracker = {}

def main():
    """Main application function."""
    # Configure page with custom theme
    st.set_page_config(
        page_title="Connecticut Legal Tools",
        page_icon="⚖️",
        layout="wide"
    )
    
    # Apply custom CSS
    apply_custom_css()
    
    # Initialize extended session state
    initialize_extended_session_state()
    
    # Build sidebar
    build_sidebar()
    
    # Route to the correct page
    if st.session_state.current_page == "landing":
        show_landing_page()
    elif st.session_state.current_page == "legal_assistant":
        show_legal_assistant()
    elif st.session_state.current_page == "argument_practice":
        show_argument_practice()
    elif st.session_state.current_page == "court_simulator":
        show_court_simulator()
    else:
        # Default to landing if unknown page
        show_landing_page()

# Run the application
if __name__ == "__main__":
    main()