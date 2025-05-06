"""
LLM interface for court simulator participants.
"""
import re
import time
from groq import Groq
from src.config import (
    GROQ_API_KEY, 
    GROQ_MODEL, 
    TEMPERATURE, 
    MAX_TOKENS, 
    TOP_P
)
from src.court_simulator.prompts import (
    JUDGE_SYSTEM_PROMPT,
    OPPOSING_COUNSEL_SYSTEM_PROMPT,
    PLAINTIFF_COUNSEL_SYSTEM_PROMPT,  # New import
    FEEDBACK_SYSTEM_PROMPT,
    JUDGE_FEW_SHOT_EXAMPLES,
    OPPOSING_COUNSEL_FEW_SHOT_EXAMPLES,
    PLAINTIFF_COUNSEL_FEW_SHOT_EXAMPLES,  # New import
    FEEDBACK_FEW_SHOT_EXAMPLES
)
from src.court_simulator.personas import JudgePersonality, OpposingCounselStrategy


def clean_response(response):
    """Remove thinking blocks and other artifacts from the LLM response.
    
    Args:
        response: Raw LLM response
        
    Returns:
        Cleaned response
    """
    if '<think>' in response and '</think>' in response:
        # Use regex to remove everything between <think> and </think> tags
        cleaned = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        return cleaned.strip()
    else:
        return response


def format_scenario_context(scenario, simulation_state, conversation_history, current_speaker=None):
    """Format the scenario context for the LLM.
    
    Args:
        scenario: The current scenario object
        simulation_state: Current state of the simulation
        conversation_history: List of previous messages
        current_speaker: Current speaker role (if applicable)
        
    Returns:
        Formatted context string
    """
    context = f"""
Case Title: {scenario.title}
Case Type: {scenario.case_type}
Case Facts: {scenario.facts}

Legal Issues:
{chr(10).join(f"- {issue}" for issue in scenario.legal_issues)}

Current Simulation State: {simulation_state.value}
"""
    
    # Add precedents if available
    if scenario.precedents:
        context += "\nRelevant Precedents:\n"
        for precedent in scenario.precedents:
            context += f"- {precedent['name']}: {precedent['holding']}\n"
    
    # Add statutes if available
    if scenario.statutes:
        context += "\nRelevant Statutes:\n"
        for statute in scenario.statutes:
            context += f"- {statute}\n"
    
    # Add conversation history context (last 3 exchanges)
    if conversation_history:
        context += "\nRecent Conversation:\n"
        for message in conversation_history[-6:]:  # Last 6 messages (3 exchanges)
            speaker = message["role"].capitalize()
            content = message["content"]
            context += f"{speaker}: {content}\n\n"
    
    return context


def call_llm_with_retry(messages, temperature=TEMPERATURE, max_tokens=MAX_TOKENS):
    """Call the LLM API with a retry mechanism.
    
    Args:
        messages: List of message objects for the LLM
        temperature: Temperature parameter for the LLM
        max_tokens: Max tokens parameter for the LLM
        
    Returns:
        Cleaned LLM response
    """
    try:
        client = Groq(api_key=GROQ_API_KEY)
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=GROQ_MODEL,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=TOP_P,
        )
        
        # Get and clean response
        raw_response = chat_completion.choices[0].message.content
        cleaned_response = clean_response(raw_response)
        
        return cleaned_response
    
    except Exception as e:
        # Wait 10 seconds and retry once
        time.sleep(10)
        try:
            client = Groq(api_key=GROQ_API_KEY)
            chat_completion = client.chat.completions.create(
                messages=messages,
                model=GROQ_MODEL,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=TOP_P,
            )
            
            # Get and clean response
            raw_response = chat_completion.choices[0].message.content
            cleaned_response = clean_response(raw_response)
            
            return cleaned_response
        
        except Exception as e:
            # Return None if both attempts fail
            return None


def generate_judge_response(scenario, simulation_state, conversation_history):
    """Generate a judge response using the LLM.
    
    Args:
        scenario: The current scenario object
        simulation_state: Current state of the simulation
        conversation_history: List of previous messages
        
    Returns:
        Judge's response
    """
    # Get judge personality
    judge_personality = scenario.judge_personality
    personality_modifier = JudgePersonality.get_prompt_modifiers(judge_personality)
    
    # Format scenario context
    context = format_scenario_context(scenario, simulation_state, conversation_history)
    
    # Build user prompt
    user_prompt = f"""
{personality_modifier}

{context}

How would you respond as the judge at this point in the proceedings?
"""
    
    # Build messages for Groq format
    messages = [
        {"role": "system", "content": JUDGE_SYSTEM_PROMPT}
    ]
    
    # Add few-shot examples
    for example in JUDGE_FEW_SHOT_EXAMPLES:
        messages.append({"role": example["role"], "content": example["content"]})
    
    # Add the current query
    messages.append({"role": "user", "content": user_prompt})
    
    # Call LLM with retry
    response = call_llm_with_retry(
        messages=messages,
        temperature=0.7,  # Slightly higher temperature for more judicial variety
        max_tokens=MAX_TOKENS
    )
    
    # Return response or fallback message
    if response:
        return response
    else:
        return "The court is experiencing technical difficulties. We'll resume shortly."


def generate_plaintiff_counsel_response(scenario, simulation_state, conversation_history):
    """Generate a plaintiff counsel response using the LLM.
    
    Args:
        scenario: The current scenario object
        simulation_state: Current state of the simulation
        conversation_history: List of previous messages
        
    Returns:
        Plaintiff counsel's response
    """
    # Get plaintiff counsel strategy
    strategy = scenario.plaintiff_counsel_strategy
    strategy_modifier = OpposingCounselStrategy.get_prompt_modifiers(strategy)
    
    # Format scenario context
    context = format_scenario_context(scenario, simulation_state, conversation_history)
    
    # Build user prompt
    user_prompt = f"""
{strategy_modifier}

{context}

How would you respond as plaintiff's counsel at this point in the proceedings?
"""
    
    # Build messages for Groq format
    messages = [
        {"role": "system", "content": PLAINTIFF_COUNSEL_SYSTEM_PROMPT}
    ]
    
    # Add few-shot examples
    for example in PLAINTIFF_COUNSEL_FEW_SHOT_EXAMPLES:
        messages.append({"role": example["role"], "content": example["content"]})
    
    # Add the current query
    messages.append({"role": "user", "content": user_prompt})
    
    # Call LLM with retry
    response = call_llm_with_retry(
        messages=messages,
        temperature=0.7,  # Slightly higher for variety
        max_tokens=MAX_TOKENS
    )
    
    # Return response or fallback message
    if response:
        return response
    else:
        return "Plaintiff's counsel is preparing their response."


def generate_opposing_counsel_response(scenario, simulation_state, conversation_history):
    """Generate an opposing counsel response using the LLM.
    
    Args:
        scenario: The current scenario object
        simulation_state: Current state of the simulation
        conversation_history: List of previous messages
        
    Returns:
        Opposing counsel's response
    """
    # Get opposing counsel strategy
    strategy = scenario.defendant_counsel_strategy  # Updated to use defendant strategy
    strategy_modifier = OpposingCounselStrategy.get_prompt_modifiers(strategy)
    
    # Format scenario context
    context = format_scenario_context(scenario, simulation_state, conversation_history)
    
    # Build user prompt
    user_prompt = f"""
{strategy_modifier}

{context}

How would you respond as defendant's counsel at this point in the proceedings?
"""
    
    # Build messages for Groq format
    messages = [
        {"role": "system", "content": OPPOSING_COUNSEL_SYSTEM_PROMPT}
    ]
    
    # Add few-shot examples
    for example in OPPOSING_COUNSEL_FEW_SHOT_EXAMPLES:
        messages.append({"role": example["role"], "content": example["content"]})
    
    # Add the current query
    messages.append({"role": "user", "content": user_prompt})
    
    # Call LLM with retry
    response = call_llm_with_retry(
        messages=messages,
        temperature=0.7,  # Slightly higher for variety
        max_tokens=MAX_TOKENS
    )
    
    # Return response or fallback message
    if response:
        return response
    else:
        return "Defendant's counsel is preparing their response."


def generate_performance_feedback(scenario, conversation_history, user_arguments):
    """Generate performance feedback on the user's arguments.
    
    Args:
        scenario: The current scenario object
        conversation_history: Complete conversation history
        user_arguments: List of user's argument messages
        
    Returns:
        Structured feedback with scores and suggestions
    """
    # Format all user arguments
    user_argument_text = "\n\n".join([arg["content"] for arg in user_arguments])
    
    # Format conversation context
    conversation_text = ""
    for message in conversation_history:
        role = message["role"].capitalize()
        content = message["content"]
        conversation_text += f"{role}: {content}\n\n"
    
    # Build user prompt
    user_prompt = f"""
Case Title: {scenario.title}
Case Type: {scenario.case_type}
Case Facts: {scenario.facts}

Student's Arguments:
{user_argument_text}

Full Simulation Transcript:
{conversation_text}

Provide a detailed evaluation of the student's performance in this simulated court proceeding.
Rate their performance in these categories on a scale of 1-5:
1. Legal Reasoning
2. Presentation and Advocacy
3. Responsiveness to Questions
4. Procedural Knowledge
5. Overall Performance

For each category, explain the rating with specific examples from their arguments.
Provide specific suggestions for improvement.
"""
    
    # Build messages for Groq format
    messages = [
        {"role": "system", "content": FEEDBACK_SYSTEM_PROMPT}
    ]
    
    # Add few-shot examples
    for example in FEEDBACK_FEW_SHOT_EXAMPLES:
        messages.append({"role": example["role"], "content": example["content"]})
    
    # Add the current query
    messages.append({"role": "user", "content": user_prompt})
    
    # Call LLM with retry and larger max_tokens for feedback
    response = call_llm_with_retry(
        messages=messages,
        temperature=0.4,  # Lower for more consistent evaluation
        max_tokens=1500  # Larger for detailed feedback
    )
    
    # Return response or fallback with default scores
    if not response:
        return {
            "feedback_text": "Unable to generate detailed feedback at this time.",
            "scores": {
                "legal_reasoning": 3,
                "presentation": 3,
                "responsiveness": 3,
                "procedural_knowledge": 3,
                "overall": 3
            }
        }
    
    # Extract scores (simple regex extraction)
    scores = {
        "legal_reasoning": 0,
        "presentation": 0,
        "responsiveness": 0,
        "procedural_knowledge": 0,
        "overall": 0
    }
    
    # Simple pattern matching to extract scores
    if "Legal Reasoning: " in response or "Legal Reasoning:" in response:
        match = re.search(r"Legal Reasoning:?\s*(\d+(?:\.\d+)?)", response)
        if match:
            scores["legal_reasoning"] = float(match.group(1))
    
    if "Presentation" in response:
        match = re.search(r"Presentation.*?:?\s*(\d+(?:\.\d+)?)", response)
        if match:
            scores["presentation"] = float(match.group(1))
            
    if "Responsiveness" in response:
        match = re.search(r"Responsiveness.*?:?\s*(\d+(?:\.\d+)?)", response)
        if match:
            scores["responsiveness"] = float(match.group(1))
            
    if "Procedural Knowledge" in response or "Procedural:" in response:
        match = re.search(r"Procedural.*?:?\s*(\d+(?:\.\d+)?)", response)
        if match:
            scores["procedural_knowledge"] = float(match.group(1))
            
    if "Overall" in response or "Overall:" in response:
        match = re.search(r"Overall.*?:?\s*(\d+(?:\.\d+)?)", response)
        if match:
            scores["overall"] = float(match.group(1))
    
    return {
        "feedback_text": response,
        "scores": scores
    }