import json
import openai
from flask import current_app

class AIService:
    """Service class for AI operations using OpenAI"""
    
    @staticmethod
    def analyze_writing_style(email_pairs):
        """
        Analyze writing style using OpenAI
        
        Args:
            email_pairs: List of email pairs
            
        Returns:
            dict: Style analysis result
        """
        # Set OpenAI API key
        openai.api_key = current_app.config['OPENAI_API_KEY']
        
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
            
            # Remove markdown code blocks if present
            if content.startswith("```") and "```" in content:
                # Find the first and last occurrence of ```
                start = content.find("\n", content.find("```")) + 1
                end = content.rfind("```")
                content = content[start:end].strip()
            
            # Try to parse the JSON response
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Fallback: Try to find JSON in the response content
                if '{' in content and '}' in content:
                    json_start = content.find('{')
                    json_end = content.rfind('}') + 1
                    json_content = content[json_start:json_end]
                    
                    try:
                        return json.loads(json_content)
                    except:
                        pass
                
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
            # Return a default structure if the API call fails
            return {
                "overall_style_summary": f"Analysis failed due to an API error: {str(e)}. Please try again.",
                "categories": [
                    {
                        "name": "Default Category",
                        "description": "No analysis could be performed due to an error.",
                        "key_characteristics": ["None available"]
                    }
                ]
            }
    
    @staticmethod
    def generate_synthetic_emails(style_analysis, original_emails):
        """
        Generate synthetic emails based on style categories
        
        Args:
            style_analysis: Style analysis dictionary
            original_emails: Original email pairs
            
        Returns:
            dict: Synthetic emails by category
        """
        # Set OpenAI API key
        openai.api_key = current_app.config['OPENAI_API_KEY']
        
        synthetic_emails = {}
        
        # Limit to 3 emails per category to avoid token limits
        emails_per_category = 3
        
        for category in style_analysis['categories']:
            category_name = category['name']
            synthetic_emails[category_name] = []
            
            prompt = f"""
            I need you to generate {emails_per_category} synthetic emails that match the following style category:
            
            Category: {category_name}
            Description: {category['description']}
            Key Characteristics: {', '.join(category['key_characteristics'])}
            
            These emails should be similar to the user's writing style as described, but should be completely new emails
            on various topics. Make them realistic and varied.
            
            Here are examples of the user's original emails for reference:
            {json.dumps(original_emails, indent=2)}
            
            Generate {emails_per_category} complete emails with subjects, varying in length and purpose.
            Return as a simple JSON array of strings, where each string is an entire email.
            
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
                
                # Handle markdown code blocks
                if "```" in content:
                    # Extract content between code blocks if present
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
                        content = content[start:last_marker].strip()
                    else:
                        # If the blocks are in the middle, try to extract the JSON part
                        if "[" in content and "]" in content:
                            start = content.find("[")
                            end = content.rfind("]") + 1
                            content = content[start:end].strip()
                
                # Try to parse the JSON response
                try:
                    emails = json.loads(content)
                    
                    if isinstance(emails, list):
                        synthetic_emails[category_name] = emails
                    else:
                        # If response is a dict, check if it contains an array
                        if isinstance(emails, dict):
                            for key, value in emails.items():
                                if isinstance(value, list) and value:
                                    synthetic_emails[category_name] = value
                                    break
                            
                        # If still no valid list, create placeholder
                        if not synthetic_emails[category_name]:
                            synthetic_emails[category_name] = ["Sample email for " + category_name]
                
                except json.JSONDecodeError:
                    # MULTIPLE FALLBACK STRATEGIES
                    
                    # FALLBACK 1: Try to find and extract a valid JSON array
                    if "[" in content and "]" in content:
                        try:
                            json_start = content.find("[")
                            json_end = content.rfind("]") + 1
                            json_content = content[json_start:json_end]
                            
                            # Additional cleaning - sometimes there are extra characters
                            json_content = json_content.strip()
                            
                            emails_list = json.loads(json_content)
                            if isinstance(emails_list, list):
                                synthetic_emails[category_name] = emails_list
                                continue
                        except:
                            pass
                    
                    # FALLBACK 2: Create dummy emails
                    synthetic_emails[category_name] = [
                        f"Subject: Sample Email for {category_name}\n\nDear recipient,\n\nThis is a sample email for the {category_name} category.\n\nBest regards,\nThe System"
                    ]
                    
            except Exception:
                # Create fallback emails even if API fails
                synthetic_emails[category_name] = [
                    f"Subject: Sample Email {i+1} for {category_name}\n\nDear recipient,\n\nThis is a sample email for the {category_name} category.\n\nBest regards,\nThe System" 
                    for i in range(emails_per_category)
                ]
        
        return synthetic_emails
    
    @staticmethod
    def regenerate_email(original_email, category, user_feedback, rating):
        """
        Regenerate an improved email based on user feedback
        
        Args:
            original_email: Original email content
            category: Email category
            user_feedback: User feedback comments
            rating: User rating
            
        Returns:
            str: Improved email content
        """
        # Set OpenAI API key
        openai.api_key = current_app.config['OPENAI_API_KEY']
        
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
        
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert email writer who can adapt and improve writing based on feedback."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content
    
    @staticmethod
    def generate_new_email(recipient, topic, key_points, approved_emails, original_emails, style_analysis):
        """
        Generate a new email based on user input and style preferences
        
        Args:
            recipient: Email recipient
            topic: Email topic
            key_points: Key points for the email
            approved_emails: List of approved emails
            original_emails: List of original emails
            style_analysis: Style analysis dictionary
            
        Returns:
            str: Generated email content
        """
        # Set OpenAI API key
        openai.api_key = current_app.config['OPENAI_API_KEY']
        
        # Prepare examples from approved emails
        examples = []
        for email in approved_emails:
            if isinstance(email, dict) and 'content' in email:
                examples.append(email['content'])
        
        # If no approved emails, use original emails
        if not examples:
            for email in original_emails:
                if isinstance(email, dict) and 'answer' in email:
                    examples.append(email['answer'])
        
        # Limit examples to prevent token limit issues
        if examples:
            if len(examples) > 3:
                examples = examples[:3]
        else:
            examples = ["Thank you for your email. I appreciate your time."]
        
        # Get style summary
        if isinstance(style_analysis, dict) and 'overall_style_summary' in style_analysis:
            style_summary = style_analysis['overall_style_summary']
        else:
            style_summary = "Professional, clear, and concise style."
        
        # Convert key_points to a string if it's a list
        if isinstance(key_points, list):
            key_points_str = "\n".join([f"- {point}" for point in key_points])
        else:
            key_points_str = str(key_points)
        
        # Make sure to include only first example to avoid token limits
        example_text = ""
        if examples:
            first_example = examples[0][:200] + "..." if len(examples[0]) > 200 else examples[0]
            example_text = f"Example of previous emails:\n{first_example}"
        
        prompt = f"""
        Draft an email to {recipient} about {topic} including these key points:
        {key_points_str}
        
        Style: {style_summary}
        
        {example_text}
        
        Generate a complete email with subject, greeting, body covering all key points, and sign-off.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an AI assistant that drafts emails matching a specific user's writing style. Return only the email content with no additional comments or explanations."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content