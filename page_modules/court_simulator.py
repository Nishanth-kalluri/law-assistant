"""
Streamlit UI implementation for the Court Simulator.
"""
import streamlit as st
import json
from enum import Enum
import pandas as pd
import plotly.express as px
import time
from typing import Dict, List, Any, Optional

from src.court_simulator.engine import CourtSimulator, SimulationState, SimulationRole
from src.court_simulator.personas import JudgePersonality, OpposingCounselStrategy


def render_court_simulator():
    """Render the court simulator page in Streamlit."""
    st.title("Connecticut Legal Assistant: Automated Court Simulator")
    st.markdown("""
    Watch a simulated court proceeding with AI-powered judge and attorneys. 
    Select a case scenario, customize the personalities of the participants, 
    and observe how the proceedings unfold.
    """)
    
    # Initialize simulator if not in session state
    if "court_simulator" not in st.session_state:
        st.session_state.court_simulator = CourtSimulator()
        st.session_state.active_simulation = False
        st.session_state.auto_refresh = False
    
    # Get the simulator
    simulator = st.session_state.court_simulator
    
    # Display available scenarios if no simulation active
    if not st.session_state.active_simulation:
        _render_scenario_selection()
    else:
        _render_active_simulation()
        
        # Auto-refresh for auto-advance mode
        if st.session_state.auto_refresh and simulator.auto_advance:
            if simulator.should_auto_advance():
                simulator.advance_simulation()
                st.rerun()
            time.sleep(0.5)
            st.rerun()


def _render_scenario_selection():
    """Render the scenario selection and persona customization interface."""
    # Load scenarios
    simulator = st.session_state.court_simulator
    scenarios = simulator.load_scenarios()
    
    if not scenarios:
        st.error("No simulation scenarios found.")
        return
    
    # Convert to DataFrame for display
    scenarios_df = pd.DataFrame([
        {
            "ID": s.get("id", ""),
            "Title": s.get("title", ""),
            "Type": s.get("case_type", ""),
            "Difficulty": s.get("difficulty", "Medium")
        }
        for s in scenarios
    ])
    
    # Display as table
    st.subheader("Available Scenarios")
    st.dataframe(scenarios_df, hide_index=True)
    
    # Scenario selection form
    with st.form("scenario_selection"):
        st.subheader("Select a Scenario")
        selected_scenario = st.selectbox(
            "Choose a case scenario:",
            options=scenarios_df["ID"].tolist(),
            format_func=lambda x: f"{x}: {scenarios_df[scenarios_df['ID'] == x]['Title'].iloc[0]}"
        )
        
        # Display scenario details
        if selected_scenario:
            scenario_data = next((s for s in scenarios if s.get("id") == selected_scenario), None)
            if scenario_data:
                with st.expander("Scenario Details", expanded=True):
                    st.markdown(f"### {scenario_data.get('title', '')}")
                    st.markdown(f"**Type**: {scenario_data.get('case_type', '')}")
                    st.markdown(f"**Description**: {scenario_data.get('description', '')}")
                    st.markdown(f"**Facts of the Case**:")
                    st.markdown(f"{scenario_data.get('facts', '')}")
                    
                    # Display legal issues
                    legal_issues = scenario_data.get("legal_issues", [])
                    if legal_issues:
                        st.markdown("**Legal Issues**:")
                        for issue in legal_issues:
                            st.markdown(f"- {issue}")
        
        # Persona customization
        st.subheader("Customize Court Participants")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### Judge")
            judge_personality = st.selectbox(
                "Select judge personality:",
                options=[
                    "neutral", "stern", "procedural", 
                    "empathetic", "impatient"
                ],
                format_func=lambda x: x.capitalize()
            )
            st.markdown(f"*{JudgePersonality.get_description(judge_personality)}*")
        
        with col2:
            st.markdown("### Plaintiff's Counsel")
            plaintiff_strategy = st.selectbox(
                "Select plaintiff's strategy:",
                options=[
                    "standard", "aggressive", "technical", 
                    "emotional", "passive"
                ],
                format_func=lambda x: x.capitalize()
            )
            st.markdown(f"*{OpposingCounselStrategy.get_description(plaintiff_strategy)}*")
        
        with col3:
            st.markdown("### Defendant's Counsel")
            defendant_strategy = st.selectbox(
                "Select defendant's strategy:",
                options=[
                    "standard", "aggressive", "technical", 
                    "emotional", "passive"
                ],
                format_func=lambda x: x.capitalize()
            )
            st.markdown(f"*{OpposingCounselStrategy.get_description(defendant_strategy)}*")
        
        # Simulation controls
        st.subheader("Simulation Controls")
        col1, col2 = st.columns(2)
        
        with col1:
            auto_advance = st.checkbox("Auto-advance simulation", value=True)
        
        with col2:
            advance_delay = st.slider(
                "Seconds between exchanges:",
                min_value=1,
                max_value=10,
                value=5
            )
        
        # Start button
        start_button = st.form_submit_button("Start Simulation")
        
        if start_button and selected_scenario:
            # Set custom personas
            simulator.set_custom_personas(
                judge_personality,
                plaintiff_strategy,
                defendant_strategy
            )
            
            # Start simulation
            result = simulator.start_simulation(selected_scenario)
            
            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state.active_simulation = True
                st.session_state.auto_refresh = auto_advance
                
                # Set auto-advance
                simulator.set_auto_advance(auto_advance, advance_delay)
                
                # Rerun to refresh UI
                st.rerun()


def _render_active_simulation():
    """Render the active simulation interface."""
    simulator = st.session_state.court_simulator
    state = simulator.get_state()
    
    # Check for error
    if "error" in state:
        st.error(state["error"])
        return
    
    # Extract data
    current_state = state["state"]
    messages = state["messages"]
    active_speaker = state["active_speaker"]
    is_paused = state["is_paused"]
    auto_advance = state["auto_advance"]
    completed = state.get("completed", False)
    
    # Display simulation controls
    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
    
    with col1:
        if is_paused and not completed:
            if st.button("▶️ Resume"):
                simulator.toggle_pause()
                st.rerun()
        elif not completed:
            if st.button("⏸️ Pause"):
                simulator.toggle_pause()
                st.rerun()
    
    with col2:
        if not auto_advance and not completed:
            if st.button("⏭️ Next Exchange"):
                simulator.advance_simulation()
                st.rerun()
    
    with col3:
        if not completed:
            auto = st.checkbox("Auto-advance", value=auto_advance)
            if auto != auto_advance:
                simulator.set_auto_advance(auto)
                st.session_state.auto_refresh = auto
                st.rerun()
    
    with col4:
        if not completed:
            delay = st.slider(
                "Speed (seconds between exchanges)",
                min_value=1,
                max_value=10,
                value=state["advance_delay"]
            )
            if delay != state["advance_delay"]:
                simulator.set_auto_advance(auto_advance, delay)
                st.rerun()
    
    # Display current state
    state_colors = {
        "INTRODUCTION": "blue",
        "PLAINTIFF_OPENING": "green",
        "DEFENDANT_OPENING": "orange",
        "PLAINTIFF_EVIDENCE": "green",
        "DEFENDANT_EVIDENCE": "orange",
        "JUDGE_QUESTIONING": "blue",
        "PLAINTIFF_REBUTTAL": "green",
        "DEFENDANT_REBUTTAL": "orange",
        "PLAINTIFF_CLOSING": "green",
        "DEFENDANT_CLOSING": "orange",
        "RULING": "purple",
        "COMPLETED": "gray"
    }
    
    color = state_colors.get(current_state, "blue")
    
    # Create a more descriptive phase name
    phase_names = {
        "INTRODUCTION": "Court Introduction",
        "PLAINTIFF_OPENING": "Plaintiff's Opening Statement",
        "DEFENDANT_OPENING": "Defendant's Opening Statement",
        "PLAINTIFF_EVIDENCE": "Plaintiff's Evidence Presentation",
        "DEFENDANT_EVIDENCE": "Defendant's Evidence Presentation",
        "JUDGE_QUESTIONING": "Judge's Questioning",
        "PLAINTIFF_REBUTTAL": "Plaintiff's Rebuttal",
        "DEFENDANT_REBUTTAL": "Defendant's Rebuttal",
        "PLAINTIFF_CLOSING": "Plaintiff's Closing Argument",
        "DEFENDANT_CLOSING": "Defendant's Closing Argument",
        "RULING": "Judge's Ruling",
        "COMPLETED": "Proceedings Concluded"
    }
    
    phase_name = phase_names.get(current_state, current_state)
    
    st.markdown(f"""
    <div style='
        background-color: {color}; 
        padding: 10px; 
        border-radius: 5px; 
        color: white; 
        text-align: center;
        margin-bottom: 20px;
        font-weight: bold;
        font-size: 1.2em;
    '>
        Current Phase: {phase_name}
    </div>
    """, unsafe_allow_html=True)
    
    # Display next speaker if not completed
    if active_speaker and not completed:
        speaker_names = {
            "judge": "Judge",
            "plaintiff_counsel": "Plaintiff's Counsel",
            "defendant_counsel": "Defendant's Counsel"
        }
        speaker_name = speaker_names.get(active_speaker, active_speaker)
        
        st.markdown(f"""
        <div style='
            background-color: #f0f0f0; 
            padding: 5px; 
            border-radius: 5px; 
            text-align: center;
            margin-bottom: 10px;
            font-style: italic;
        '>
            Next to speak: {speaker_name}
        </div>
        """, unsafe_allow_html=True)
    
    # Display conversation
    st.subheader("Court Proceedings")
    
    # Use chat message containers for conversation
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        
        if role == "judge":
            with st.chat_message("assistant", avatar="👨‍⚖️"):
                st.markdown(content)
        elif role == "plaintiff_counsel":
            with st.chat_message("user", avatar="👩‍💼"):
                st.markdown(content)
        elif role == "defendant_counsel":
            with st.chat_message("assistant", avatar="👨‍💼"):
                st.markdown(content)
        else:
            with st.chat_message("system"):
                st.markdown(content)
    
    # Option to restart if completed
    if completed:
        if st.button("Start New Simulation", type="primary"):
            st.session_state.active_simulation = False
            st.rerun()