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
    
    # Display as table with better formatting
    st.subheader("Available Scenarios")
    # Apply custom CSS for better table appearance
    st.markdown("""
    <style>
    .scenario-table {
        font-size: 1.1em;
        border-collapse: collapse;
        width: 100%;
    }
    .scenario-table th {
        background-color: #1E3A8A;
        color: white;
        padding: 12px;
        text-align: left;
    }
    .scenario-table td {
        padding: 10px;
        border-bottom: 1px solid #ddd;
    }
    .scenario-table tr:hover {
        background-color: #f5f5f5;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.dataframe(scenarios_df, hide_index=True, use_container_width=True)
    
    # Scenario selection form with improved styling
    with st.form("scenario_selection"):
        st.subheader("Select a Scenario")
        selected_scenario = st.selectbox(
            "Choose a case scenario:",
            options=scenarios_df["ID"].tolist(),
            format_func=lambda x: f"{x}: {scenarios_df[scenarios_df['ID'] == x]['Title'].iloc[0]}"
        )
        
        # Display scenario details with better formatting
        if selected_scenario:
            scenario_data = next((s for s in scenarios if s.get("id") == selected_scenario), None)
            if scenario_data:
                with st.expander("Scenario Details", expanded=True):
                    st.markdown(f"### {scenario_data.get('title', '')}")
                    
                    # Better formatted case details
                    st.markdown(
                        f"""
                        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 15px;color: #333;">
                            <p><strong>Type:</strong> {scenario_data.get('case_type', '')}</p>
                            <p><strong>Description:</strong> {scenario_data.get('description', '')}</p>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                    
                    st.markdown(f"**Facts of the Case**:")
                    st.markdown(
                        f"""
                        <div style="background-color: #edf2f7; padding: 15px; border-radius: 5px; border-left: 4px solid #3182ce;color: #333;">
                            {scenario_data.get('facts', '')}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    # Display legal issues with better formatting
                    legal_issues = scenario_data.get("legal_issues", [])
                    if legal_issues:
                        st.markdown("**Legal Issues**:")
                        issues_html = '<div style="background-color: #f0f4f8; padding: 15px; border-radius: 5px; border-left: 4px solid #4a5568;color: #333;">'
                        for issue in legal_issues:
                            issues_html += f'<p>• {issue}</p>'
                        issues_html += '</div>'
                        st.markdown(issues_html, unsafe_allow_html=True)
        
        # Persona customization with improved cards
        st.subheader("Customize Court Participants")
        
        # Define persona card colors
        card_colors = {
            "judge": "#E3F2FD",  # Light blue for judge
            "plaintiff": "#E8F5E9",  # Light green for plaintiff
            "defendant": "#FFF3E0"   # Light orange for defendant
        }
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div style="background-color: {card_colors['judge']}; padding: 15px; border-radius: 5px; height: 100px;">
                <h3 style="text-align: center; color: #1565C0;">Judge</h3>
            </div>
            """, unsafe_allow_html=True)
            judge_personality = st.selectbox(
                "Select judge personality:",
                options=[
                    "neutral", "stern", "procedural", 
                    "empathetic", "impatient"
                ],
                format_func=lambda x: x.capitalize(),
                key="judge_personality_selector"
            )
            st.markdown(
                f"<div style='font-style: italic; padding: 10px; background-color: #f0f0f0; border-radius: 5px;color: #333;'>{JudgePersonality.get_description(judge_personality)}</div>",
                unsafe_allow_html=True
            )

        with col2:
            st.markdown(f"""
            <div style="background-color: {card_colors['judge']}; padding: 15px; border-radius: 5px; height: 100px;">
                <h3 style="text-align: center; color: #1565C0;">Plaintiff</h3>
            </div>
            """, unsafe_allow_html=True)
            plaintiff_strategy = st.selectbox(
                "Select plaintiff's strategy:",
                options=[
                    "standard", "aggressive", "technical", 
                    "emotional", "passive"
                ],
                format_func=lambda x: x.capitalize(),
                key="plaintiff_strategy_selector"
            )
            st.markdown(
                f"<div style='font-style: italic; padding: 10px; background-color: #f0f0f0; border-radius: 5px;color: #333;'>{OpposingCounselStrategy.get_description(plaintiff_strategy)}</div>",
                 unsafe_allow_html=True
            )

        with col3:
            st.markdown(f"""
            <div style="background-color: {card_colors['judge']}; padding: 15px; border-radius: 5px; height: 100px;">
                <h3 style="text-align: center; color: #1565C0;">Defendant</h3>
            </div>
            """, unsafe_allow_html=True)
            defendant_strategy = st.selectbox(
                "Select defendant's strategy:",
                options=[
                    "standard", "aggressive", "technical", 
                    "emotional", "passive"
                ],
                format_func=lambda x: x.capitalize(),
                key="defendant_strategy_selector"
            )
            
            st.markdown(
                f"<div style='font-style: italic; padding: 10px; background-color: #f0f0f0; border-radius: 5px;color: #333;'>{OpposingCounselStrategy.get_description(defendant_strategy)}</div>",
                unsafe_allow_html=True
            )
        
        # Simulation controls with better organization
        st.markdown("---")
        st.subheader("Simulation Controls")
        
        control_col1, control_col2 = st.columns(2)
        
        with control_col1:
            auto_advance = st.checkbox("Auto-advance simulation", value=True)
            st.markdown(
                "<div style='font-size: 0.9em; color: #666;'>Automatically progress through the simulation</div>",
                unsafe_allow_html=True
            )
        
        with control_col2:
            advance_delay = st.slider(
                "Seconds between exchanges:",
                min_value=1,
                max_value=10,
                value=5
            )
            st.markdown(
                "<div style='font-size: 0.9em; color: #666;'>Control the pace of the simulation</div>",
                unsafe_allow_html=True
            )
        
        # Start button with better styling
        start_button = st.form_submit_button("Start Simulation")
        
        if start_button and selected_scenario:
            # Set custom personas
            simulator.set_custom_personas(
                judge_personality,
                plaintiff_strategy,
                defendant_strategy
            )
            print(judge_personality)
            
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
    """Render the active simulation interface with improved visual clarity."""
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
    
    # Display simulation controls with better styling
    st.markdown("""
    <style>
    .control-container {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .control-button {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="control-container">', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
    
    with col1:
        if is_paused and not completed:
            if st.button("▶️ Resume", key="resume_btn", use_container_width=True):
                simulator.toggle_pause()
                st.rerun()
        elif not completed:
            if st.button("⏸️ Pause", key="pause_btn", use_container_width=True):
                simulator.toggle_pause()
                st.rerun()
    
    with col2:
        if not auto_advance and not completed:
            if st.button("⏭️ Next", key="next_btn", use_container_width=True):
                simulator.advance_simulation()
                st.rerun()
    
    with col3:
        if not completed:
            auto = st.checkbox("Auto-advance", value=auto_advance, key="auto_advance_check")
            if auto != auto_advance:
                simulator.set_auto_advance(auto)
                st.session_state.auto_refresh = auto
                st.rerun()
    
    with col4:
        if not completed:
            delay = st.slider(
                "Speed (seconds)",
                min_value=1,
                max_value=10,
                value=state["advance_delay"],
                key="delay_slider"
            )
            if delay != state["advance_delay"]:
                simulator.set_auto_advance(auto_advance, delay)
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Define vibrant, accessible colors for states
    state_colors = {
        "INTRODUCTION": "#1E88E5",          # Vibrant blue
        "PLAINTIFF_OPENING": "#43A047",      # Vibrant green
        "DEFENDANT_OPENING": "#FB8C00",      # Vibrant orange
        "PLAINTIFF_EVIDENCE": "#43A047",     # Vibrant green
        "DEFENDANT_EVIDENCE": "#FB8C00",     # Vibrant orange
        "JUDGE_QUESTIONING": "#1E88E5",      # Vibrant blue
        "PLAINTIFF_REBUTTAL": "#43A047",     # Vibrant green
        "DEFENDANT_REBUTTAL": "#FB8C00",     # Vibrant orange
        "PLAINTIFF_CLOSING": "#43A047",      # Vibrant green
        "DEFENDANT_CLOSING": "#FB8C00",      # Vibrant orange
        "RULING": "#8E24AA",                # Vibrant purple
        "COMPLETED": "#757575"               # Gray
    }
    
    color = state_colors.get(current_state, "#1E88E5")
    
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
    
    # More attractive phase indicator with progress bar feel
    # Change this section (around line 389-407)
    st.markdown(f"""
        <div style='
        background-color: white; 
        padding: 15px; 
        border-radius: 8px; 
        margin-bottom: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        '>
            <h3 style='margin-bottom: 10px; text-align: center;'>Current Phase</h3>
            <div style='
            background-color: {color}; 
            padding: 12px; 
            border-radius: 5px; 
            color: white; 
            text-align: center;
            font-weight: bold;
            font-size: 1.2em;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            color: #333; 
        '>  
            {phase_name}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Display next speaker if not completed with better styling
    if active_speaker and not completed:
        speaker_names = {
            "judge": "Judge",
            "plaintiff_counsel": "Plaintiff's Counsel",
            "defendant_counsel": "Defendant's Counsel"
        }
        
        speaker_colors = {
            "judge": "#1E88E5",            # Blue for judge
            "plaintiff_counsel": "#43A047", # Green for plaintiff
            "defendant_counsel": "#FB8C00"  # Orange for defendant
        }
        
        speaker_name = speaker_names.get(active_speaker, active_speaker)
        speaker_color = speaker_colors.get(active_speaker, "#757575")
        
        st.markdown(f"""
        <div style='
            background-color: #f8f9fa; 
            padding: 10px; 
            border-radius: 5px; 
            text-align: center;
            margin-bottom: 20px;
            border-left: 5px solid {speaker_color};
            color: #333; 
        '>
            <span style='font-weight: bold; color: {speaker_color};'>Next to speak:</span> {speaker_name}
        </div>
        """, unsafe_allow_html=True)
    
    # Display conversation with much better visual distinction between speakers
    st.subheader("Court Proceedings")
    
    # Create custom CSS for better message styling
    st.markdown("""
    <style>
    .message-container {
        margin-bottom: 15px;
        border-radius: 8px;
        overflow: hidden;
    }
    .message-header {
        padding: 8px 15px;
        color: white;
        font-weight: bold;
    }
    .message-content {
        padding: 15px;
        background-color: #f8f9fa;
        border-bottom-left-radius: 8px;
        border-bottom-right-radius: 8px;
        color: #333;  
    }
    .judge-header {
        background-color: #1E88E5;
    }
    .plaintiff-header {
        background-color: #43A047;
    }
    .defendant-header {
        background-color: #FB8C00;
    }
    .system-header {
        background-color: #757575;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Add a progress tracker for the proceedings
    if not completed:
        all_states = [
            "INTRODUCTION", "PLAINTIFF_OPENING", "DEFENDANT_OPENING", 
            "PLAINTIFF_EVIDENCE", "DEFENDANT_EVIDENCE", "JUDGE_QUESTIONING",
            "PLAINTIFF_REBUTTAL", "DEFENDANT_REBUTTAL", 
            "PLAINTIFF_CLOSING", "DEFENDANT_CLOSING", "RULING"
        ]
        
        current_index = all_states.index(current_state) if current_state in all_states else 0
        progress = (current_index + 1) / len(all_states)
        
        st.progress(progress)
        
        st.markdown(f"""
        <div style='text-align: center; margin-bottom: 20px; font-size: 0.9em; color: #666;'>
            Phase {current_index + 1} of {len(all_states)}
        </div>
        """, unsafe_allow_html=True)
    
    # Create a container for the court transcript
    transcript_container = st.container()
    
    with transcript_container:
        # Use custom styled message containers instead of chat_message for more control
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            role_label = role.replace("_", " ").title()
            
            if role == "judge":
                header_class = "judge-header"
                role_icon = "👨‍⚖️"
                role_label = "Judge"
            elif role == "plaintiff_counsel":
                header_class = "plaintiff-header"
                role_icon = "👩‍💼"
                role_label = "Plaintiff's Counsel"
            elif role == "defendant_counsel":
                header_class = "defendant-header"
                role_icon = "👨‍💼"
                role_label = "Defendant's Counsel"
            else:
                header_class = "system-header"
                role_icon = "ℹ️"
                role_label = "Court System"
            
            # Render custom message container
            st.markdown(f"""
            <div class="message-container">
                <div class="message-header {header_class}">
                    {role_icon} {role_label}
                </div>
                <div class="message-content">
                    {content}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Option to restart if completed with better styling
    if completed:
        st.markdown("""
        <div style="text-align: center; margin: 30px 0;">
            <h3>Simulation Complete</h3>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Start New Simulation", type="primary", use_container_width=True):
            st.session_state.active_simulation = False
            st.rerun()