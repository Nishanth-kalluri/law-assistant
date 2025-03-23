"""Search functionality for retrieving relevant legal information."""
import re
import streamlit as st
from src.config import MAX_RESULTS

def identify_source_sections(content, metadata, url_tracker=None):
    """Identify sources for content based on both content analysis and metadata.
    
    Args:
        content: The text content to analyze
        metadata: Document metadata
        url_tracker: Optional dictionary mapping section IDs to URLs
        
    Returns:
        List of tuples containing (source_id, source_url)
    """
    sources = []
    url_tracker = url_tracker or {}
    
    # Extract sources from metadata first (more reliable)
    for key, value in metadata.items():
        if key.startswith('source_') and key != 'source_file':
            # Check if value is a string before using startswith
            if isinstance(value, str) and value.startswith('http'):
                source_id = key.replace('source_', '')
                sources.append((source_id, value))
    
    # If no sources found in metadata, try content analysis
    if not sources:
        # Direct URL matches
        url_pattern = r'https://www\.cga\.ct\.gov/current/pub/[^\s]+'
        direct_urls = re.findall(url_pattern, content)
        sources.extend([("Official Source", url) for url in direct_urls])

        # Section code matches with URL tracking
        section_pattern = r'Sec\.\s+(\d+[a-z]?-\d+[a-z]?(?:-\d+[a-z]?)?)'
        for section in re.findall(section_pattern, content):
            if section in url_tracker:
                sources.append((f"Section {section}", url_tracker[section]))
    
    # Fallback if still no sources
    if not sources:
        sources.append(("Connecticut General Statutes", "https://www.cga.ct.gov/current/pub/titles.htm"))
    
    # Deduplicate and limit sources
    unique_sources = []
    seen_urls = set()
    
    for source_id, url in sources:
        if url not in seen_urls:
            unique_sources.append((source_id, url))
            seen_urls.add(url)
    
    return unique_sources[:3]  # Limit to top 3 sources

def perform_similarity_search(query, vectorstore, n_results=MAX_RESULTS, url_tracker=None):
    """Perform similarity search and return results with source information.
    
    Args:
        query: The search query
        vectorstore: The vector store to search
        n_results: Number of results to return
        url_tracker: Optional dictionary mapping section IDs to URLs
        
    Returns:
        List of formatted search results
    """
    if not vectorstore:
        return []
    
    try:
        # Perform the search
        results = vectorstore.similarity_search_with_score(query, k=n_results)
        
        formatted_results = []
        for doc, score in results:
            try:
                # Extract content and metadata
                content = doc.page_content
                metadata = doc.metadata
                
                # Get sources from both content and metadata
                sources = identify_source_sections(content, metadata, url_tracker)
                
                # Format and add to results
                formatted_results.append({
                    "content": content,
                    "sources": sources,
                    "relevance_score": score,
                    "metadata": metadata
                })
            except Exception as e:
                # Add simplified result without sources if there's an error
                formatted_results.append({
                    "content": doc.page_content,
                    "sources": [("Connecticut General Statutes", "https://www.cga.ct.gov/current/pub/titles.htm")],
                    "relevance_score": score,
                    "metadata": {}
                })
        
        return formatted_results
    except Exception as e:
        # Return empty results on error
        return []