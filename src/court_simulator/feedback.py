"""
Argument evaluation and feedback functionality for court simulator.
"""
from enum import Enum
from typing import Dict, List, Any
from src.court_simulator.llm_interface import generate_performance_feedback

class FeedbackCategory(Enum):
    """Categories for performance feedback."""
    LEGAL_REASONING = "legal_reasoning"
    PRESENTATION = "presentation"
    RESPONSIVENESS = "responsiveness"
    PROCEDURAL_KNOWLEDGE = "procedural_knowledge"
    OVERALL = "overall"
    
    @classmethod
    def get_description(cls, category):
        """Get description for a feedback category."""
        descriptions = {
            cls.LEGAL_REASONING.value: "Quality of legal analysis and argument construction",
            cls.PRESENTATION.value: "Clarity, organization, and persuasiveness of arguments",
            cls.RESPONSIVENESS.value: "Ability to address questions and adapt to feedback",
            cls.PROCEDURAL_KNOWLEDGE.value: "Understanding of court procedures and legal standards",
            cls.OVERALL.value: "Overall performance evaluation"
        }
        return descriptions.get(category, "No description available.")


def evaluate_argument(scenario, conversation_history, user_arguments):
    """
    Evaluates the user's arguments and provides feedback.
    
    Args:
        scenario: The current scenario object
        conversation_history: Complete conversation history
        user_arguments: List of user's argument messages
        
    Returns:
        Dict containing feedback and scores
    """
    # Generate feedback using LLM
    feedback_result = generate_performance_feedback(
        scenario, 
        conversation_history, 
        user_arguments
    )
    
    # Format the feedback for display
    formatted_feedback = {
        "summary": feedback_result["feedback_text"],
        "scores": feedback_result["scores"],
        "highlights": extract_highlights(feedback_result["feedback_text"]),
        "improvement_suggestions": extract_suggestions(feedback_result["feedback_text"])
    }
    
    return formatted_feedback


def extract_highlights(feedback_text):
    """
    Extract positive highlights from the feedback text.
    
    Args:
        feedback_text: The complete feedback text
        
    Returns:
        List of highlight points
    """
    highlights = []
    
    # Look for strengths section
    if "Strengths:" in feedback_text:
        strengths_section = feedback_text.split("Strengths:")[1].split("Areas for Improvement")[0]
        # Extract bullet points or numbered items
        for line in strengths_section.split("\n"):
            line = line.strip()
            if line.startswith("-") or line.startswith("•") or (line.startswith(str(len(highlights)+1)) and ":" in line):
                highlights.append(line.lstrip("- •123456789.").strip())
    
    # If no structured strengths section, look for positive language
    if not highlights:
        positive_keywords = ["well done", "effective", "strong", "excellent", "good", "impressive"]
        for line in feedback_text.split("\n"):
            for keyword in positive_keywords:
                if keyword in line.lower() and len(line) > 20:  # Avoid short phrases
                    highlights.append(line.strip())
                    break
    
    # Limit to top 3 highlights
    return highlights[:3]


def extract_suggestions(feedback_text):
    """
    Extract improvement suggestions from the feedback text.
    
    Args:
        feedback_text: The complete feedback text
        
    Returns:
        List of suggestion points
    """
    suggestions = []
    
    # Look for improvement section
    if "Areas for Improvement" in feedback_text:
        improvement_section = feedback_text.split("Areas for Improvement")[1].split("Suggestions")[0]
        # Extract bullet points or numbered items
        for line in improvement_section.split("\n"):
            line = line.strip()
            if line.startswith("-") or line.startswith("•") or (line.startswith(str(len(suggestions)+1)) and ":" in line):
                suggestions.append(line.lstrip("- •123456789.").strip())
    
    # Look for suggestions section as backup
    if not suggestions and "Suggestions" in feedback_text:
        suggestions_section = feedback_text.split("Suggestions")[1].split("#")[0]
        for line in suggestions_section.split("\n"):
            line = line.strip()
            if line.startswith("-") or line.startswith("•") or (line.startswith(str(len(suggestions)+1)) and ":" in line):
                suggestions.append(line.lstrip("- •123456789.").strip())
    
    # If no structured sections found, look for imperative language
    if not suggestions:
        suggestion_starters = ["consider", "try to", "should", "could", "improve", "focus on"]
        for line in feedback_text.split("\n"):
            for starter in suggestion_starters:
                if starter in line.lower() and len(line) > 20:  # Avoid short phrases
                    suggestions.append(line.strip())
                    break
    
    # Limit to top 3 suggestions
    return suggestions[:3]