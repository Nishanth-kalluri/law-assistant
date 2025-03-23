"""
UI utility functions for the Connecticut Legal Tools application.
"""
import streamlit as st

def build_sidebar():
    """Build the sidebar for all pages."""
    with st.sidebar:
        st.title("Connecticut Legal Tools")
        
        # Navigation buttons
        if st.button("⬅️ Back to Home", use_container_width=True):
            st.session_state.current_page = "landing"
            st.rerun()
        
        # Clean conversation button (only show when in a chat page)
        if st.session_state.current_page != "landing":
            if st.button("🗑️ Clear Conversation", use_container_width=True):
                st.session_state.conversation_history = []
                st.rerun()
        
        st.divider()
        
        # About section
        st.subheader("About")
        
        if st.session_state.current_page == "legal_assistant":
            st.markdown("""
            **Connecticut Legal Assistant** uses AI to help you understand Connecticut General Statutes. 
            
            This tool:
            * Retrieves relevant legal information from Connecticut statutes
            * Provides accurate responses based on official legal sources
            * Cites specific sections and includes links to official documentation
            """)
        
        elif st.session_state.current_page == "argument_practice":
            st.markdown("""
            **Legal Argument Practice** helps you prepare for courtroom presentations.
            
            This tool:
            * Provides constructive feedback on your legal arguments
            * Suggests improvements based on legal principles
            * Helps refine your persuasive skills
            """)
        
        elif st.session_state.current_page == "court_simulator":
            st.markdown("""
            **Court Simulator** creates realistic courtroom scenarios.
            
            This tool:
            * Simulates judicial questioning and responses
            * Creates hypothetical case scenarios
            * Provides practice for courtroom procedures
            """)
        
        else:
            st.markdown("""
            **Connecticut Legal Tools** offers three AI-powered assistants to help with various legal needs.
            
            Choose a tool from the main page to get started.
            """)
        
        st.divider()
        st.caption("**Note**: These tools provide legal information, not legal advice. For specific legal problems, consult a licensed attorney.")

def custom_display_conversation_history():
    """Display conversation history with custom styling."""
    for message in st.session_state.conversation_history:
        role = message["role"]
        content = message["content"]
        
        with st.chat_message(role, avatar="👤" if role == "user" else "⚖️"):
            st.write(content)

def load_system():
    """Load the vectorstore system if not already initialized."""
    from src.vectorstore import initialize_vectorstore
    
    if st.session_state.vectorstore is None:
        with st.spinner("Initializing system..."):
            try:
                # Silent callback to avoid UI clutter
                def silent_callback(message):
                    pass
                
                vectorstore = initialize_vectorstore(silent_callback)
                
                if vectorstore:
                    st.session_state.vectorstore = vectorstore
                    return True
                else:
                    st.error("Failed to initialize system. Please check your configuration.")
                    return False
            except Exception as e:
                st.error(f"Error initializing system: {str(e)}")
                return False
    return True

def apply_custom_css():
    """Apply custom CSS for better appearance."""
    st.markdown("""
    <style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stChatMessage {
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
    }
    h1, h2, h3 {
        color: #1E6091;
    }
    
    /* Tool cards CSS */
    .tool-card {
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        transition: transform 0.3s;
        height: 100%;
    }
    .tool-card:hover {
        transform: translateY(-5px);
    }
    .legal-assistant {
        background: linear-gradient(135deg, #2193b0, #6dd5ed);
        color: white;
    }
    .argument-practice {
        background: linear-gradient(135deg, #8e2de2, #4a00e0);
        color: white;
    }
    .court-simulator {
        background: linear-gradient(135deg, #f12711, #f5af19);
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)