# test_openai.py
# A standalone script to test the OpenAI integration and JSON parsing
import os
import json
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure OpenAI API
openai.api_key = os.getenv("OPENAI_API_KEY")

def test_analyze_writing_style():
    """Test the analyze_writing_style function with a small sample."""
    # Mock data
    email_pairs = [
        {
            "question": "Can we schedule a meeting to discuss the project timeline?",
            "answer": "Hi team, I'd be happy to meet about the timeline. How does tomorrow at 2pm work for everyone? Best, Alex"
        },
        {
            "question": "What's the status on the patent application?",
            "answer": "The patent is currently under review. We should hear back in 4-6 weeks according to the USPTO timeline. Let me know if you need any specific details."
        }
    ]
    
    prompt = f"""
    I have a collection of email question-answer pairs written by a user. I need you to analyze their writing style.
    Please provide:
    1. A detailed summary of their writing habits and style
    2. Categorize their email style into 5 distinct categories (e.g., formal business, casual professional, friendly, technical, etc.)
    3. For each category, list key characteristics that define the style
    
    Here are the email pairs:
    {json.dumps(email_pairs, indent=2)}
    
    Provide your analysis as a valid JSON object with the following structure:
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

    Return only the JSON, with no markdown formatting, no code blocks, and no additional explanation.
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert email analyst with deep understanding of writing styles and tone. Always respond with valid JSON without markdown formatting or code blocks."},
                {"role": "user", "content": prompt}
            ]
        )
        
        content = response.choices[0].message.content.strip()
        
        # Debug: Print the content
        print("OpenAI Raw Response:")
        print(content)
        print("\n" + "-"*80 + "\n")
        
        # Remove markdown code blocks if present
        if content.startswith("```") and "```" in content:
            # Find the first and last occurrence of ```
            start = content.find("\n", content.find("```")) + 1
            end = content.rfind("```")
            content = content[start:end].strip()
            print("After code block removal:")
            print(content)
            print("\n" + "-"*80 + "\n")
        
        # Try to parse the JSON response
        try:
            result = json.loads(content)
            print("Successfully parsed JSON:")
            print(json.dumps(result, indent=2))
            return result
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Content that failed to parse: {content}")
            
            # Fallback: Try to find JSON in the response content
            if '{' in content and '}' in content:
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                json_content = content[json_start:json_end]
                
                print("Trying to parse extracted JSON:")
                print(json_content)
                
                try:
                    result = json.loads(json_content)
                    print("Successfully parsed extracted JSON")
                    return result
                except Exception as extract_err:
                    print(f"Failed to parse extracted JSON: {extract_err}")
            
            # If we still can't parse, create a minimal valid structure
            return {
                "overall_style_summary": "Analysis failed to generate valid JSON. Please try again.",
                "categories": [
                    {
                        "name": "Default Category",
                        "description": "No categories could be extracted from the analysis.",
                        "key_characteristics": ["None available"]
                    }
                ]
            }
            
    except Exception as e:
        print(f"OpenAI API error: {e}")
        # Return a default structure if the API call fails
        return {
            "overall_style_summary": "Analysis failed due to an API error. Please try again.",
            "categories": [
                {
                    "name": "Default Category",
                    "description": "No analysis could be performed due to an error.",
                    "key_characteristics": ["None available"]
                }
            ]
        }

def test_generate_synthetic_emails(style_analysis):
    """Test the generate_synthetic_emails function with a small sample and one category."""
    email_pairs = [
        {
            "question": "Can we schedule a meeting to discuss the project timeline?",
            "answer": "Hi team, I'd be happy to meet about the timeline. How does tomorrow at 2pm work for everyone? Best, Alex"
        }
    ]
    
    # Use just the first category to test
    category = style_analysis['categories'][0]
    category_name = category['name']
    
    prompt = f"""
    I need you to generate 1 synthetic email that matches the following style category:
    
    Category: {category_name}
    Description: {category['description']}
    Key Characteristics: {', '.join(category['key_characteristics'])}
    
    This email should be similar to the user's writing style as described, but should be a completely new email
    on a different topic. Make it realistic.
    
    Here are examples of the user's original emails for reference:
    {json.dumps(email_pairs, indent=2)}
    
    Generate 1 complete email with subject, greeting, body, and sign-off.
    Return as a simple JSON array containing a single string, where the string is the entire email.
    
    Return only the JSON array, with no markdown formatting, no code blocks, and no additional explanation.
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert email writer who can mimic various writing styles precisely. Always respond with valid JSON without markdown formatting or code blocks."},
                {"role": "user", "content": prompt}
            ]
        )
        
        content = response.choices[0].message.content.strip()
        
        # Debug: Print the content
        print(f"OpenAI Raw Response for category {category_name}:")
        print(content)
        print("\n" + "-"*80 + "\n")
        
        # Remove markdown code blocks if present
        if content.startswith("```") and "```" in content:
            # Find the first and last occurrence of ```
            start = content.find("\n", content.find("```")) + 1
            end = content.rfind("```")
            content = content[start:end].strip()
            print("After code block removal:")
            print(content)
            print("\n" + "-"*80 + "\n")
        
        # Try to parse the JSON response
        try:
            emails = json.loads(content)
            print("Successfully parsed JSON:")
            print(json.dumps(emails, indent=2))
            return emails
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Content that failed to parse: {content}")
            
            # Fallback: Try to find JSON in the response content
            if '[' in content and ']' in content:
                json_start = content.find('[')
                json_end = content.rfind(']') + 1
                json_content = content[json_start:json_end]
                
                print("Trying to parse extracted JSON array:")
                print(json_content)
                
                try:
                    emails_list = json.loads(json_content)
                    print("Successfully parsed extracted JSON array")
                    return emails_list
                except Exception as extract_err:
                    print(f"Failed to parse extracted JSON array: {extract_err}")
            
            # If still can't parse, create a dummy email
            return [
                f"Sample email for category: {category_name}.\nDescription: {category['description']}\nKey characteristics: {', '.join(category['key_characteristics'])}"
            ]
            
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return [
            f"Failed to generate email for category: {category_name} due to an API error."
        ]

if __name__ == "__main__":
    print("Testing analyze_writing_style function...")
    analysis_result = test_analyze_writing_style()
    
    if analysis_result and "categories" in analysis_result and len(analysis_result["categories"]) > 0:
        print("\nTesting generate_synthetic_emails function...")
        emails_result = test_generate_synthetic_emails(analysis_result)
        print("\nGenerated Emails:")
        for email in emails_result:
            print("-"*40)
            print(email)
    else:
        print("Style analysis failed, cannot test email generation.")