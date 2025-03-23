"""
Connecticut Legal Assistant - Streamlit Application
A tool for understanding Connecticut General Statutes using AI.
"""
import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import modules
from src.vectorstore import initialize_vectorstore
from src.search import perform_similarity_search
from src.query_processor import process_legal_query
from utils.helpers import initialize_session_state, update_conversation_history, display_conversation_history
from src.config import GOOGLE_API_KEY, PINECONE_API_KEY, GROQ_API_KEY

def build_sidebar():
    """Build simplified sidebar."""
    with st.sidebar:
        st.title("Connecticut Legal Assistant")
        
        # Clean conversation button
        if st.button("Clear Conversation", use_container_width=True):
            st.session_state.conversation_history = []
            st.rerun()
        
        st.divider()
        
        # About section
        st.subheader("About")
        st.markdown("""
        **Connecticut Legal Assistant** uses AI to help you understand Connecticut General Statutes. 
        
        This application:
        * Retrieves relevant legal information from Connecticut statutes
        * Provides accurate responses based on official legal sources
        * Cites specific sections and includes links to official documentation
        
        **Note**: This tool provides legal information, not legal advice. For specific legal problems, consult a licensed attorney.
        """)

def custom_display_conversation_history():
    """Display conversation history as a clean chat interface."""
    for message in st.session_state.conversation_history:
        role = message["role"]
        content = message["content"]
        
        with st.chat_message(role):
            st.write(content)

def load_system():
    """Initialize the vectorstore on app startup."""
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

def main():
    """Main Streamlit application."""
    # Configure page with custom theme
    st.set_page_config(
        page_title="Connecticut Legal Assistant",
        page_icon="⚖️",
        layout="wide"
    )
    
    # Custom CSS for better appearance
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
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    initialize_session_state()
    
    # Build sidebar
    build_sidebar()
    
    # Main content area
    st.title("Connecticut Legal Assistant")
    st.markdown("Ask questions about Connecticut law and receive answers based on the Connecticut General Statutes.")
    
    # Load system automatically
    system_ready = load_system()
    
    # Display conversation history with custom function
    custom_display_conversation_history()
    
    # Input for new question
    query = st.chat_input("Ask a question about Connecticut law...")
    
    if query and system_ready:
        # Display user question
        with st.chat_message("user"):
            st.write(query)
        
        # Process query
        with st.chat_message("assistant"):
            # First create an empty placeholder
            response_placeholder = st.empty()
            
            # Show a spinner while processing
            with st.spinner("Searching Connecticut General Statutes..."):
                # Perform similarity search
                relevant_results = perform_similarity_search(
                    query, 
                    st.session_state.vectorstore,
                    url_tracker=st.session_state.url_tracker
                )
                
                if not relevant_results:
                    response_placeholder.write("I couldn't find any relevant information in the Connecticut General Statutes. Please try rephrasing your question.")
                    update_conversation_history(query, "I couldn't find any relevant information in the Connecticut General Statutes. Please try rephrasing your question.")
                    return
                
                # Process query with Groq LLM
                response = process_legal_query(
                    query, 
                    relevant_results, 
                    st.session_state.conversation_history
                )
                
                # Display response directly
                response_placeholder.markdown(response)
                
                # Update conversation history
                update_conversation_history(query, response)
    
    elif query and not system_ready:
        with st.chat_message("assistant"):
            st.error("System initialization failed. Please check your API keys and configuration.")

# Run the application
if __name__ == "__main__":
    main()