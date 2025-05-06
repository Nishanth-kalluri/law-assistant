"""
Core simulation engine for court simulator.
"""
from enum import Enum
from typing import List, Dict, Any, Optional
import json
import os
import random
import time
from pathlib import Path

from src.court_simulator.personas import JudgePersonality, OpposingCounselStrategy
from src.court_simulator.feedback import evaluate_argument
from src.court_simulator.llm_interface import (
    generate_judge_response,
    generate_opposing_counsel_response,
    generate_plaintiff_counsel_response
)


class SimulationState(Enum):
    """States of the court simulation."""
    SETUP = "SETUP"
    INTRODUCTION = "INTRODUCTION"
    PLAINTIFF_OPENING = "PLAINTIFF_OPENING"
    DEFENDANT_OPENING = "DEFENDANT_OPENING"
    PLAINTIFF_EVIDENCE = "PLAINTIFF_EVIDENCE"
    DEFENDANT_EVIDENCE = "DEFENDANT_EVIDENCE"
    PLAINTIFF_REBUTTAL = "PLAINTIFF_REBUTTAL"
    DEFENDANT_REBUTTAL = "DEFENDANT_REBUTTAL"
    PLAINTIFF_CLOSING = "PLAINTIFF_CLOSING"
    DEFENDANT_CLOSING = "DEFENDANT_CLOSING"
    JUDGE_QUESTIONING = "JUDGE_QUESTIONING"
    RULING = "RULING"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"


class SimulationRole(Enum):
    """Roles in the court simulation."""
    JUDGE = "judge"
    PLAINTIFF_COUNSEL = "plaintiff_counsel"
    DEFENDANT_COUNSEL = "defendant_counsel"
    SYSTEM = "system"


class Scenario:
    """Court case scenario."""
    
    def __init__(self, data):
        """Initialize a scenario from data."""
        self.id = data.get("id", "")
        self.title = data.get("title", "")
        self.case_type = data.get("case_type", "")
        self.description = data.get("description", "")
        self.facts = data.get("facts", "")
        self.legal_issues = data.get("legal_issues", [])
        self.precedents = data.get("precedents", [])
        self.statutes = data.get("statutes", [])
        self.judge_personality = data.get("judge_personality", JudgePersonality.NEUTRAL.value)
        self.plaintiff_counsel_strategy = data.get("plaintiff_counsel_strategy", 
                                                OpposingCounselStrategy.STANDARD.value)
        self.defendant_counsel_strategy = data.get("defendant_counsel_strategy", 
                                                OpposingCounselStrategy.STANDARD.value)
        self.difficulty = data.get("difficulty", "medium")


class CourtSimulator:
    """Court simulation engine."""
    
    def __init__(self):
        """Initialize the court simulator."""
        self.scenario = None
        self.state = SimulationState.SETUP
        self.conversation_history = []
        self.feedback = None
        self.active_speaker = None
        self.is_paused = True
        self.auto_advance = False
        self.advance_delay = 3  # seconds between exchanges in auto mode
        self.last_advance_time = None
        
        # Custom personalities
        self.custom_judge_personality = None
        self.custom_plaintiff_strategy = None
        self.custom_defendant_strategy = None
    
    def load_scenarios(self) -> List[Dict[str, Any]]:
        """
        Load all available scenarios.
        
        Returns:
            List of scenario data dictionaries
        """
        scenarios = []
        scenario_dir = Path("src/data/scenarios")
        
        # Ensure the directory exists
        if not scenario_dir.exists():
            return scenarios
        
        # Load each JSON file
        for file_path in scenario_dir.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    scenario_data = json.load(f)
                    scenarios.append(scenario_data)
            except Exception as e:
                print(f"Error loading scenario {file_path}: {e}")
        
        return scenarios
    
    def set_custom_personas(self, judge_personality: str, plaintiff_strategy: str, defendant_strategy: str):
        """
        Set custom personas for the simulation participants.
        
        Args:
            judge_personality: Judge personality type
            plaintiff_strategy: Plaintiff counsel strategy
            defendant_strategy: Defendant counsel strategy
        """
        self.custom_judge_personality = judge_personality
        self.custom_plaintiff_strategy = plaintiff_strategy
        self.custom_defendant_strategy = defendant_strategy
    
    def start_simulation(self, scenario_id: str) -> Dict[str, Any]:
        """
        Start a new simulation with the specified scenario.
        
        Args:
            scenario_id: ID of the scenario to load
            
        Returns:
            Dict with initial simulation state
        """
        # Load all scenarios
        scenarios = self.load_scenarios()
        
        # Find the requested scenario
        scenario_data = None
        for data in scenarios:
            if data.get("id") == scenario_id:
                scenario_data = data
                break
        
        if not scenario_data:
            return {"error": f"Scenario with ID {scenario_id} not found"}
        
        # Apply custom personas if set
        if self.custom_judge_personality:
            scenario_data["judge_personality"] = self.custom_judge_personality
        if self.custom_plaintiff_strategy:
            scenario_data["plaintiff_counsel_strategy"] = self.custom_plaintiff_strategy
        if self.custom_defendant_strategy:
            scenario_data["defendant_counsel_strategy"] = self.custom_defendant_strategy
        
        # Initialize simulation
        self.scenario = Scenario(scenario_data)
        self.state = SimulationState.INTRODUCTION
        self.conversation_history = []
        self.feedback = None
        self.is_paused = True
        self.last_advance_time = time.time()
        
        # Generate judge introduction
        judge_intro = self._generate_introduction()
        
        # Add to conversation history
        self.conversation_history.append({
            "role": SimulationRole.JUDGE.value,
            "content": judge_intro
        })
        
        # Set next speaker
        self.active_speaker = SimulationRole.PLAINTIFF_COUNSEL
        
        # Return initial state
        return {
            "scenario": scenario_data,
            "state": self.state.value,
            "messages": self.conversation_history,
            "active_speaker": self.active_speaker.value
        }
    
    def toggle_pause(self) -> Dict[str, Any]:
        """
        Toggle the pause state of the simulation.
        
        Returns:
            Dict with current simulation state
        """
        self.is_paused = not self.is_paused
        
        if not self.is_paused:
            self.last_advance_time = time.time()
            
        return self.get_state()
    
    def set_auto_advance(self, auto_advance: bool, delay: float = None) -> Dict[str, Any]:
        """
        Set auto-advance mode and delay.
        
        Args:
            auto_advance: Whether to auto-advance the simulation
            delay: Time in seconds between advances (if None, uses current value)
            
        Returns:
            Dict with current simulation state
        """
        self.auto_advance = auto_advance
        if delay is not None:
            self.advance_delay = delay
            
        return self.get_state()
    
    def advance_simulation(self) -> Dict[str, Any]:
        """
        Advance the simulation to the next exchange.
        
        Returns:
            Dict with updated simulation state
        """
        if not self.scenario:
            return {"error": "No active simulation"}
            
        if self.state == SimulationState.COMPLETED:
            return {"error": "Simulation has already completed"}
            
        # Determine next action based on current state and speaker
        if self.state == SimulationState.INTRODUCTION:
            # After judge introduction, plaintiff counsel gives opening
            try:
                response = generate_plaintiff_counsel_response(
                    self.scenario,
                    self.state,
                    self.conversation_history
                )
                self.conversation_history.append({
                    "role": SimulationRole.PLAINTIFF_COUNSEL.value,
                    "content": response
                })
                self.state = SimulationState.PLAINTIFF_OPENING
                self.active_speaker = SimulationRole.DEFENDANT_COUNSEL
            except Exception as e:
                print(f"Error generating plaintiff opening: {e}")
                self.conversation_history.append({
                    "role": SimulationRole.PLAINTIFF_COUNSEL.value,
                    "content": "Plaintiff's counsel is preparing their opening statement."
                })
                self.state = SimulationState.PLAINTIFF_OPENING
                self.active_speaker = SimulationRole.DEFENDANT_COUNSEL
            
        elif self.state == SimulationState.PLAINTIFF_OPENING:
            # Defendant counsel gives opening
            try:
                response = generate_opposing_counsel_response(
                    self.scenario,
                    self.state,
                    self.conversation_history
                )
                self.conversation_history.append({
                    "role": SimulationRole.DEFENDANT_COUNSEL.value,
                    "content": response
                })
                self.state = SimulationState.DEFENDANT_OPENING
                self.active_speaker = SimulationRole.JUDGE
            except Exception as e:
                print(f"Error generating defendant opening: {e}")
                self.conversation_history.append({
                    "role": SimulationRole.DEFENDANT_COUNSEL.value,
                    "content": "Defendant's counsel is preparing their opening statement."
                })
                self.state = SimulationState.DEFENDANT_OPENING
                self.active_speaker = SimulationRole.JUDGE
            
        elif self.state == SimulationState.DEFENDANT_OPENING:
            # Judge transitions to evidence phase
            try:
                response = generate_judge_response(
                    self.scenario,
                    SimulationState.PLAINTIFF_EVIDENCE,
                    self.conversation_history
                )
                self.conversation_history.append({
                    "role": SimulationRole.JUDGE.value,
                    "content": response
                })
                self.state = SimulationState.PLAINTIFF_EVIDENCE
                self.active_speaker = SimulationRole.PLAINTIFF_COUNSEL
            except Exception as e:
                print(f"Error generating judge response: {e}")
                self.conversation_history.append({
                    "role": SimulationRole.JUDGE.value,
                    "content": "Thank you for your opening statements. We will now proceed to the evidence phase. Plaintiff's counsel, please present your evidence."
                })
                self.state = SimulationState.PLAINTIFF_EVIDENCE
                self.active_speaker = SimulationRole.PLAINTIFF_COUNSEL
            
        elif self.state == SimulationState.PLAINTIFF_EVIDENCE:
            # Plaintiff presents evidence
            try:
                response = generate_plaintiff_counsel_response(
                    self.scenario,
                    self.state,
                    self.conversation_history
                )
                self.conversation_history.append({
                    "role": SimulationRole.PLAINTIFF_COUNSEL.value,
                    "content": response
                })
                self.state = SimulationState.DEFENDANT_EVIDENCE
                self.active_speaker = SimulationRole.DEFENDANT_COUNSEL
            except Exception as e:
                print(f"Error generating plaintiff evidence: {e}")
                self.conversation_history.append({
                    "role": SimulationRole.PLAINTIFF_COUNSEL.value,
                    "content": "Your Honor, the plaintiff would like to present the following evidence..."
                })
                self.state = SimulationState.DEFENDANT_EVIDENCE
                self.active_speaker = SimulationRole.DEFENDANT_COUNSEL
            
        elif self.state == SimulationState.DEFENDANT_EVIDENCE:
            # Defendant presents evidence
            try:
                response = generate_opposing_counsel_response(
                    self.scenario,
                    self.state,
                    self.conversation_history
                )
                self.conversation_history.append({
                    "role": SimulationRole.DEFENDANT_COUNSEL.value,
                    "content": response
                })
                self.state = SimulationState.JUDGE_QUESTIONING
                self.active_speaker = SimulationRole.JUDGE
            except Exception as e:
                print(f"Error generating defendant evidence: {e}")
                self.conversation_history.append({
                    "role": SimulationRole.DEFENDANT_COUNSEL.value,
                    "content": "Your Honor, the defendant would like to present the following evidence..."
                })
                self.state = SimulationState.JUDGE_QUESTIONING
                self.active_speaker = SimulationRole.JUDGE
            
        elif self.state == SimulationState.JUDGE_QUESTIONING:
            # Judge asks questions
            try:
                response = generate_judge_response(
                    self.scenario,
                    self.state,
                    self.conversation_history
                )
                self.conversation_history.append({
                    "role": SimulationRole.JUDGE.value,
                    "content": response
                })
                self.state = SimulationState.PLAINTIFF_REBUTTAL
                self.active_speaker = SimulationRole.PLAINTIFF_COUNSEL
            except Exception as e:
                print(f"Error generating judge questioning: {e}")
                self.conversation_history.append({
                    "role": SimulationRole.JUDGE.value,
                    "content": "I have some questions for both counsels based on the evidence presented..."
                })
                self.state = SimulationState.PLAINTIFF_REBUTTAL
                self.active_speaker = SimulationRole.PLAINTIFF_COUNSEL
            
        elif self.state == SimulationState.PLAINTIFF_REBUTTAL:
            # Plaintiff rebuttal
            try:
                response = generate_plaintiff_counsel_response(
                    self.scenario,
                    self.state,
                    self.conversation_history
                )
                self.conversation_history.append({
                    "role": SimulationRole.PLAINTIFF_COUNSEL.value,
                    "content": response
                })
                self.state = SimulationState.DEFENDANT_REBUTTAL
                self.active_speaker = SimulationRole.DEFENDANT_COUNSEL
            except Exception as e:
                print(f"Error generating plaintiff rebuttal: {e}")
                self.conversation_history.append({
                    "role": SimulationRole.PLAINTIFF_COUNSEL.value,
                    "content": "Your Honor, in response to the defendant's arguments..."
                })
                self.state = SimulationState.DEFENDANT_REBUTTAL
                self.active_speaker = SimulationRole.DEFENDANT_COUNSEL
            
        elif self.state == SimulationState.DEFENDANT_REBUTTAL:
            # Defendant rebuttal
            try:
                response = generate_opposing_counsel_response(
                    self.scenario,
                    self.state,
                    self.conversation_history
                )
                self.conversation_history.append({
                    "role": SimulationRole.DEFENDANT_COUNSEL.value,
                    "content": response
                })
                self.state = SimulationState.PLAINTIFF_CLOSING
                self.active_speaker = SimulationRole.PLAINTIFF_COUNSEL
            except Exception as e:
                print(f"Error generating defendant rebuttal: {e}")
                self.conversation_history.append({
                    "role": SimulationRole.DEFENDANT_COUNSEL.value,
                    "content": "Your Honor, in response to the plaintiff's arguments..."
                })
                self.state = SimulationState.PLAINTIFF_CLOSING
                self.active_speaker = SimulationRole.PLAINTIFF_COUNSEL
            
        elif self.state == SimulationState.PLAINTIFF_CLOSING:
            # Plaintiff closing argument
            try:
                response = generate_plaintiff_counsel_response(
                    self.scenario,
                    self.state,
                    self.conversation_history
                )
                self.conversation_history.append({
                    "role": SimulationRole.PLAINTIFF_COUNSEL.value,
                    "content": response
                })
                self.state = SimulationState.DEFENDANT_CLOSING
                self.active_speaker = SimulationRole.DEFENDANT_COUNSEL
            except Exception as e:
                print(f"Error generating plaintiff closing: {e}")
                self.conversation_history.append({
                    "role": SimulationRole.PLAINTIFF_COUNSEL.value,
                    "content": "Your Honor, in conclusion, I would like to emphasize..."
                })
                self.state = SimulationState.DEFENDANT_CLOSING
                self.active_speaker = SimulationRole.DEFENDANT_COUNSEL
            
        elif self.state == SimulationState.DEFENDANT_CLOSING:
            # Defendant closing argument
            try:
                response = generate_opposing_counsel_response(
                    self.scenario,
                    self.state,
                    self.conversation_history
                )
                self.conversation_history.append({
                    "role": SimulationRole.DEFENDANT_COUNSEL.value,
                    "content": response
                })
                self.state = SimulationState.RULING
                self.active_speaker = SimulationRole.JUDGE
            except Exception as e:
                print(f"Error generating defendant closing: {e}")
                self.conversation_history.append({
                    "role": SimulationRole.DEFENDANT_COUNSEL.value,
                    "content": "Your Honor, in conclusion, I would like to emphasize..."
                })
                self.state = SimulationState.RULING
                self.active_speaker = SimulationRole.JUDGE
            
        elif self.state == SimulationState.RULING:
            # Judge gives ruling
            try:
                response = generate_judge_response(
                    self.scenario,
                    self.state,
                    self.conversation_history
                )
                self.conversation_history.append({
                    "role": SimulationRole.JUDGE.value,
                    "content": response
                })
                self.state = SimulationState.COMPLETED
                self.active_speaker = None
                self.is_paused = True
            except Exception as e:
                print(f"Error generating judge ruling: {e}")
                self.conversation_history.append({
                    "role": SimulationRole.JUDGE.value,
                    "content": "Having considered all evidence and arguments presented, the court rules as follows..."
                })
                self.state = SimulationState.COMPLETED
                self.active_speaker = None
                self.is_paused = True
            
        # Reset timer for auto-advance
        self.last_advance_time = time.time()
            
        # Return updated state
        return self.get_state()
    
    def should_auto_advance(self) -> bool:
        """
        Check if the simulation should auto-advance based on elapsed time.
        
        Returns:
            True if it's time to auto-advance, False otherwise
        """
        if self.is_paused or not self.auto_advance or self.state == SimulationState.COMPLETED:
            return False
            
        current_time = time.time()
        return (current_time - self.last_advance_time) >= self.advance_delay
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get the current simulation state.
        
        Returns:
            Dict with current simulation state
        """
        if not self.scenario:
            return {"error": "No active simulation"}
            
        result = {
            "scenario": {
                "id": self.scenario.id,
                "title": self.scenario.title,
                "case_type": self.scenario.case_type,
                "description": self.scenario.description
            },
            "state": self.state.value,
            "messages": self.conversation_history,
            "active_speaker": self.active_speaker.value if self.active_speaker else None,
            "is_paused": self.is_paused,
            "auto_advance": self.auto_advance,
            "advance_delay": self.advance_delay,
            "completed": self.state == SimulationState.COMPLETED
        }
            
        return result
    
    def _generate_introduction(self) -> str:
        """
        Generate the judge's introduction to the case.
        
        Returns:
            Introduction text
        """
        # Basic template
        case_desc = f"Case {self.scenario.id}: {self.scenario.title}"
        introduction = (
            f"All rise. The Superior Court for the State of Connecticut is now in session, "
            f"the Honorable Judge presiding.\n\n"
            f"We are here today regarding {case_desc}. "
            f"This is a {self.scenario.case_type} matter. "
            f"Counsel for the plaintiff, please prepare to present your opening statement."
        )
        
        # For more complex cases, generate with LLM
        if self.scenario.case_type not in ["simple", "basic"]:
            try:
                judge_intro = generate_judge_response(
                    self.scenario,
                    SimulationState.INTRODUCTION,
                    []  # Empty history at start
                )
                if judge_intro:
                    return judge_intro
            except:
                # Fall back to template on error
                pass
                
        return introduction