"""
Landing page implementation for Connecticut Legal Tools.
"""
import streamlit as st

def navigate_to_page(page):
    """Navigate to a specific page and reset conversation history."""
    st.session_state.current_page = page
    st.session_state.conversation_history = []

def show_landing_page():
    """Display the landing page with tool cards."""
    st.title("Connecticut Legal Tools")
    st.subheader("AI-powered legal assistants to help with Connecticut law")
    
    # Create three columns for the cards
    col1, col2, col3 = st.columns(3)
    
    # Legal Assistant Card
    with col1:
        st.markdown("""
        <div class="tool-card legal-assistant">
            <h3>Legal Assistant</h3>
            <p>Get information about Connecticut General Statutes with citations to official sources.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start Legal Assistant", key="btn_legal", use_container_width=True):
            navigate_to_page("legal_assistant")
            st.rerun()
    
    # Argument Practice Card
    with col2:
        st.markdown("""
        <div class="tool-card argument-practice">
            <h3>Argument Practice</h3>
            <p>Prepare and refine legal arguments with AI-powered feedback and suggestions.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start Argument Practice", key="btn_argument", use_container_width=True):
            navigate_to_page("argument_practice")
            st.rerun()
    
    # Court Simulator Card
    with col3:
        st.markdown("""
        <div class="tool-card court-simulator">
            <h3>Court Simulator</h3>
            <p>Practice in a simulated courtroom environment with realistic judicial interactions.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start Court Simulator", key="btn_court", use_container_width=True):
            navigate_to_page("court_simulator")
            st.rerun()
    
    # Additional information
    st.markdown("""
    ## How to use these tools
    
    1. **Select a tool** from the options above
    2. **Ask questions** or follow the prompts in the tool
    3. **Receive AI-generated responses** based on Connecticut law and legal principles
    
    Our tools are designed to assist with legal research and preparation but do not replace professional legal advice.
    """)