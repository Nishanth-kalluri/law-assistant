"""Process legal queries using Groq LLM with retrieved context."""
import re
from groq import Groq
from src.config import (
    GROQ_API_KEY, 
    GROQ_MODEL, 
    TEMPERATURE, 
    MAX_TOKENS, 
    TOP_P,
    MAX_HISTORY
)
from src.prompts.system_prompt import SYSTEM_PROMPT
from src.prompts.few_shot import FEW_SHOT_EXAMPLES  # Add this import


def format_conversation_history(history):
    """Format conversation history for the LLM.
    
    Args:
        history: List of conversation messages
        
    Returns:
        List of formatted messages
    """
    return [{"role": message["role"], "content": message["content"]} for message in history]

def clean_response(response):
    """Remove thinking blocks from the LLM response.
    
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

def process_legal_query(query, relevant_results, conversation_history=None):
    """Process legal query using Groq LLM with retrieved context.
    
    Args:
        query: User's legal question
        relevant_results: Search results to use as context
        conversation_history: Optional conversation history
        
    Returns:
        LLM response
    """
    # Extract content and sources from relevant results
    context_parts = []
    all_sources = []
    
    for result in relevant_results:
        context_parts.append(result["content"])
        all_sources.extend(result["sources"])
    
    # Combine context with source information
    context = "\n\n".join(context_parts)
    
    # Deduplicate sources
    unique_sources = []
    seen_source_ids = set()
    
    for source_id, source_path in all_sources:
        if source_id not in seen_source_ids:
            unique_sources.append((source_id, source_path))
            seen_source_ids.add(source_id)
    
    # Format sources for the prompt
    source_info = "\n".join([f"- {source_id}: {source_path}" for source_id, source_path in unique_sources[:5]])
    
    # Build messages list for Groq format
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    for example in FEW_SHOT_EXAMPLES:
        messages.append({"role": example["role"], "content": example["content"]})
    # Add conversation history (limited to MAX_HISTORY exchanges)
    if conversation_history:
        conv_history = format_conversation_history(conversation_history[-MAX_HISTORY:])
        messages.extend(conv_history)
    
    # Add retrieved context with source tracking
    context_message = f"""
    Here are the relevant Connecticut General Statutes for this query:
    
    {context}
    
    Source information:
    {source_info}
    
    Use this information to answer the following legal question.
    """
    
    messages.extend([
        {"role": "user", "content": context_message},
        {"role": "assistant", "content": "I've received the relevant Connecticut statutes and will use this information to provide an accurate response."}
    ])
    
    # Add current query
    messages.append({"role": "user", "content": query})
    
    # Call Groq API
    try:
        client = Groq(api_key=GROQ_API_KEY)
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=GROQ_MODEL,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            top_p=TOP_P,
        )
        
        # Get and clean response
        raw_response = chat_completion.choices[0].message.content
        cleaned_response = clean_response(raw_response)
        
        # Add source citations if missing
        if not any(f"{source_id}" in cleaned_response for source_id, _ in unique_sources):
            source_section = "\n\n## Sources:\n" + "\n".join([f"- {source_id}: {source_path}" for source_id, source_path in unique_sources[:5]])
            cleaned_response += source_section
        
        return cleaned_response
    
    except Exception as e:
        error_message = f"Error processing query with Groq LLM: {str(e)}"
        return f"I encountered an error while processing your query. Please try again or rephrase your question.\n\nTechnical details: {str(e)}"