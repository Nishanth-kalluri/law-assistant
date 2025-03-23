"""
Legal Assistant page implementation for Connecticut Legal Tools.
"""
import streamlit as st
from utils.ui import custom_display_conversation_history, load_system
from src.search import perform_similarity_search
from src.query_processor import process_legal_query
from utils.helpers import update_conversation_history

def show_legal_assistant():
    """Display the Legal Assistant page with chat interface."""
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
        with st.chat_message("user", avatar="👤"):
            st.write(query)
        
        # Process query
        with st.chat_message("assistant", avatar="⚖️"):
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
        with st.chat_message("assistant", avatar="⚖️"):
            st.error("System initialization failed. Please check your API keys and configuration.")