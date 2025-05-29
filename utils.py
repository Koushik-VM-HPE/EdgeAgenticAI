# Function to extract the AI's message content from the response
def extract_ai_message_content(response_dict):
    """
    Extract the content from the AI message in the agent response.
    
    Args:
        response_dict (dict): The response dictionary from the LangGraph agent
        
    Returns:
        str: The content of the AI message, or empty string if not found
    """
    try:
        # Get the messages list from the agent dictionary
        messages = response_dict.get('agent', {}).get('messages', [])
        
        # If there are messages, get the content of the last one
        if messages and hasattr(messages[-1], 'content'):
            return messages[-1].content
        elif messages and isinstance(messages[-1], dict) and 'content' in messages[-1]:
            return messages[-1]['content']
        return ""
    except Exception as e:
        print(f"Error extracting message content: {e}")
        return ""