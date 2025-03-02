import json

def is_valid_json(json_string):
    """
    Check if a string is valid JSON
    
    Args:
        json_string: String to check
        
    Returns:
        bool: True if valid JSON, False otherwise
    """
    try:
        json.loads(json_string)
        return True
    except (json.JSONDecodeError, TypeError):
        return False

def extract_json_from_text(text):
    """
    Extract JSON object or array from a text that might contain other content
    
    Args:
        text: Text that might contain JSON
        
    Returns:
        dict or list or None: Parsed JSON if found, None otherwise
    """
    # Check for JSON object
    if '{' in text and '}' in text:
        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            json_content = text[start:end]
            return json.loads(json_content)
        except json.JSONDecodeError:
            pass
    
    # Check for JSON array
    if '[' in text and ']' in text:
        try:
            start = text.find('[')
            end = text.rfind(']') + 1
            json_content = text[start:end]
            return json.loads(json_content)
        except json.JSONDecodeError:
            pass
    
    return None

def clean_markdown_code_blocks(content):
    """
    Remove markdown code blocks from content
    
    Args:
        content: Text that might contain markdown code blocks
        
    Returns:
        str: Content without markdown code blocks
    """
    if not content or not isinstance(content, str):
        return content
    
    # If content is wrapped in code blocks
    if content.startswith("```") and "```" in content[3:]:
        first_marker = content.find("```")
        # Find the end of the first line containing ```
        newline_after_marker = content.find("\n", first_marker)
        if newline_after_marker != -1:
            start = newline_after_marker + 1  # Start after the newline
        else:
            start = first_marker + 3  # Just skip the ```
        
        last_marker = content.rfind("```")
        # Content is everything between first marker (after newline) and last marker
        return content[start:last_marker].strip()
    
    return content