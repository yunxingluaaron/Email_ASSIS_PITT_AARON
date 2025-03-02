# openai_helpers.py
import openai
import json
import os
from typing import List, Dict, Any

# Configure OpenAI API
openai.api_key = os.getenv("OPENAI_API_KEY")

def analyze_email_style(email_pairs: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Analyze user's email writing style using OpenAI API
    
    Args:
        email_pairs: List of dictionaries with 'question' and 'answer' keys
        
    Returns:
        Dictionary containing style analysis results
    """
    prompt = f"""
    I have a collection of email question-answer pairs written by a user. I need you to analyze their writing style.
    Please provide:
    1. A detailed summary of their writing habits and style
    2. Categorize their email style into 5 distinct categories (e.g., formal business, casual professional, friendly, technical, etc.)
    3. For each category, list key characteristics that define the style
    
    Here are the email pairs:
    {json.dumps(email_pairs, indent=2)}
    
    Provide your analysis in JSON format with the following structure:
    {{
        "overall_style_summary": "string",
        "categories": [
            {{
                "name": "string",
                "description": "string",
                "key_characteristics": ["string", "string", ...]
            }},
            ...
        ]
    }}
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert email analyst with deep understanding of writing styles and tone."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,  # Lower temperature for more consistent analysis
            max_tokens=2000   # Ensure we get a complete response
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        print(f"Error in analyze_email_style: {e}")
        raise

def generate_synthetic_emails(style_analysis: Dict[str, Any], original_emails: List[Dict[str, str]], num_samples: int = 10) -> Dict[str, List[str]]:
    """
    Generate synthetic email samples for each style category
    
    Args:
        style_analysis: Dictionary containing style analysis results
        original_emails: List of original email pairs for reference
        num_samples: Number of synthetic emails to generate per category
        
    Returns:
        Dictionary mapping category names to lists of synthetic emails
    """
    synthetic_emails = {}
    
    for category in style_analysis['categories']:
        category_name = category['name']
        synthetic_emails[category_name] = []
        
        prompt = f"""
        I need you to generate {num_samples} synthetic emails that match the following style category:
        
        Category: {category_name}
        Description: {category['description']}
        Key Characteristics: {', '.join(category['key_characteristics'])}
        
        These emails should be similar to the user's writing style as described, but should be completely new emails
        on various topics. Make them realistic and varied in topics, length and purpose.
        
        Here are examples of the user's original emails for reference:
        {json.dumps(original_emails, indent=2)}
        
        Generate {num_samples} complete emails with subjects, varying in length and purpose.
        Return as a JSON array of email content.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert email writer who can mimic various writing styles precisely."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,  # Slightly higher temperature for creative variety
                max_tokens=4000   # Allow for longer responses to fit multiple emails
            )
            
            synthetic_emails[category_name] = json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error generating synthetic emails for {category_name}: {e}")
            synthetic_emails[category_name] = [f"Error generating email samples for {category_name}"]
    
    return synthetic_emails

def regenerate_improved_email(original_email: str, category: str, user_feedback: str, rating: int) -> str:
    """
    Regenerate an improved email based on user feedback
    
    Args:
        original_email: Original email content
        category: Style category of the email
        user_feedback: User's feedback comments
        rating: User's rating (0-100)
        
    Returns:
        Improved email content
    """
    prompt = f"""
    I need you to improve this email based on user feedback:
    
    Original Email:
    {original_email}
    
    Category: {category}
    User Rating: {rating}/100
    User Feedback: {user_feedback}
    
    Please rewrite the email, addressing all the issues mentioned in the feedback while preserving the
    original intent and topic of the email. Make it better match the user's style preferences.
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert email writer who can adapt and improve writing based on feedback."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,  # Lower temperature for more focused improvement
            max_tokens=2000   # Allow for a complete email response
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in regenerate_improved_email: {e}")
        raise

def generate_new_email(recipient: str, topic: str, key_points: List[str], 
                      approved_emails: List[Dict[str, str]], 
                      original_emails: List[Dict[str, str]], 
                      style_analysis: Dict[str, Any]) -> str:
    """
    Generate a new email based on user input and learned style
    
    Args:
        recipient: Name of the recipient
        topic: Email topic
        key_points: List of key points to include
        approved_emails: List of user-approved synthetic email samples
        original_emails: List of original user email pairs
        style_analysis: Style analysis results
        
    Returns:
        Generated email content
    """
    # Prepare examples from approved emails (limit to 5 for prompt size)
    examples = [email['content'] for email in approved_emails[:5]] if approved_emails else []
    
    # If no approved emails available, use original emails
    if not examples and original_emails:
        examples = [email['answer'] for email in original_emails[:5]]
    
    prompt = f"""
    I need you to draft an email to {recipient} about {topic} that includes the following key points:
    {json.dumps(key_points, indent=2)}
    
    The email should match the user's writing style. Here's an analysis of their style:
    {json.dumps(style_analysis, indent=2)}
    
    Here are examples of emails that match their style:
    {json.dumps(examples, indent=2)}
    
    Generate a complete email that sounds like it was written by this user, incorporating all the key points
    while maintaining their authentic voice, tone, and structure.
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an AI assistant that drafts emails matching a specific user's writing style perfectly."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in generate_new_email: {e}")
        raise