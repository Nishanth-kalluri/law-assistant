"""
Connecticut Legal Tools - Streamlit Application
A suite of tools for legal assistance, argument practice, and court simulation.
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

# Page navigation
def navigate_to_page(page):
    st.session_state.current_page = page
    # Clear conversation when switching tools
    st.session_state.conversation_history = []

# Initialize session state with additional variables
def initialize_extended_session_state():
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "landing"
    
    # Original session state variables
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'vectorstore' not in st.session_state:
        st.session_state.vectorstore = None
    if 'url_tracker' not in st.session_state:
        st.session_state.url_tracker = {}

# Sidebar for all pages
def build_sidebar():
    with st.sidebar:
        st.title("Connecticut Legal Tools")
        
        # Navigation buttons
        if st.button("⬅️ Back to Home", use_container_width=True):
            navigate_to_page("landing")
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

# Custom chat display function
def custom_display_conversation_history():
    for message in st.session_state.conversation_history:
        role = message["role"]
        content = message["content"]
        
        with st.chat_message(role, avatar="👤" if role == "user" else "⚖️"):
            st.write(content)

# Load vectorstore system
def load_system():
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

# Landing page
def show_landing_page():
    st.title("Connecticut Legal Tools")
    st.subheader("AI-powered legal assistants to help with Connecticut law")
    
    # Create three columns for the cards
    col1, col2, col3 = st.columns(3)
    
    # CSS for cards
    st.markdown("""
    <style>
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

# Legal Assistant page
def show_legal_assistant():
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

# Argument Practice page (placeholder for future implementation)
def show_argument_practice():
    st.title("Legal Argument Practice")
    st.subheader("Practice and improve your legal arguments")
    
    # Placeholder for future implementation
    st.info("This feature is coming soon. For now, you can try out the other tools.")
    
    # Mock interface to show structure
    st.markdown("""
    ## How to use Legal Argument Practice
    
    1. Enter your legal argument below
    2. Our AI will analyze your argument
    3. Receive feedback on structure, reasoning, and persuasiveness
    """)
    
    argument = st.text_area("Enter your legal argument here:", height=200)
    
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Submit Argument", use_container_width=True):
            if argument:
                with st.chat_message("assistant", avatar="⚖️"):
                    st.info("This feature is not yet implemented. Check back soon!")
            else:
                st.warning("Please enter an argument first.")

# Court Simulator page (placeholder for future implementation)
def show_court_simulator():
    st.title("Court Simulator")
    st.subheader("Experience realistic courtroom scenarios")
    
    # Placeholder for future implementation
    st.info("This feature is coming soon. For now, you can try out the other tools.")
    
    # Mock interface to show structure
    case_types = ["Contract Dispute", "Criminal Defense", "Personal Injury", "Family Law", "Custom Scenario"]
    selected_case = st.selectbox("Select a case type:", case_types)
    
    st.markdown("## Courtroom Simulation")
    st.markdown("The judge and opposing counsel will respond to your arguments.")
    
    # Custom display for mock conversation
    with st.chat_message("system", avatar="👨‍⚖️"):
        st.write(f"Welcome to the {selected_case} simulation. The court is now in session.")
    
    user_argument = st.chat_input("Present your argument to the court...")
    
    if user_argument:
        with st.chat_message("user", avatar="👤"):
            st.write(user_argument)
        
        with st.chat_message("system", avatar="👨‍⚖️"):
            st.info("This feature is not yet implemented. Check back soon!")

# Main application function
def main():
    # Configure page with custom theme
    st.set_page_config(
        page_title="Connecticut Legal Tools",
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
    h1, h2, h3 {
        color: #1E6091;
    }
    </style>
    """, unsafe_allow_html=True)
    
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