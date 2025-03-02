# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import openai
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from dotenv import load_dotenv
import traceback

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

CORS(app, resources={r"/api/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"]}})

# Configure OpenAI API
openai.api_key = os.getenv("OPENAI_API_KEY")

# Database connection
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

@app.route('/api/submit-emails', methods=['POST'])
def submit_emails():
    print("\n" + "="*80)
    print("STARTING /api/submit-emails ENDPOINT")
    print("="*80)
    
    try:
        # Debug incoming request
        print(f"Request JSON: {request.json}")
        user_identifier = request.json.get('userId')
        email_pairs = request.json.get('emailPairs')
        
        print(f"User identifier: {user_identifier}")
        print(f"Number of email pairs: {len(email_pairs) if email_pairs else 0}")
        
        # Validate input
        if not user_identifier:
            print("ERROR: User ID is missing")
            return jsonify({"error": "User ID is required"}), 400
        if not email_pairs or not isinstance(email_pairs, list):
            print(f"ERROR: Email pairs invalid - Type: {type(email_pairs)}")
            return jsonify({"error": "Email pairs are required and must be a list"}), 400
        
        print("Input validation passed")
        
        # Get a database connection
        print("Getting database connection...")
        try:
            conn = get_db_connection()
            print("Database connection established")
            cur = conn.cursor(cursor_factory=RealDictCursor)
            print("Cursor created")
        except Exception as db_err:
            print(f"ERROR establishing database connection: {db_err}")
            return jsonify({"error": f"Database connection error: {str(db_err)}"}), 500
        
        try:
            # Check if this user exists or create them
            print(f"Looking up or creating user: {user_identifier}")
            if isinstance(user_identifier, str) and not user_identifier.isdigit():
                print("User identifier is a string (email)")
                # Look up user by email/identifier
                cur.execute(
                    "SELECT id FROM users WHERE email = %s",
                    (user_identifier,)
                )
                user_row = cur.fetchone()
                
                if user_row:
                    # User exists, use their ID
                    user_id = user_row['id']
                    print(f"Existing user found, ID: {user_id}")
                else:
                    # Create a new user
                    print("User not found, creating new user")
                    cur.execute(
                        "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id",
                        (user_identifier, "placeholder_password_hash")
                    )
                    user_id = cur.fetchone()['id']
                    print(f"New user created, ID: {user_id}")
                    conn.commit()
                    print("User creation committed")
            else:
                # Assume it's already a valid numeric ID
                print("User identifier appears to be numeric")
                user_id = int(user_identifier) if user_identifier else None
                print(f"Interpreted user ID: {user_id}")
            
            if not user_id:
                print("ERROR: Failed to get or create user")
                return jsonify({"error": "User not found or could not be created"}), 400
            
            # Save email pairs to database
            print(f"Saving {len(email_pairs)} email pairs to database")
            valid_pairs = 0
            for i, pair in enumerate(email_pairs):
                # Validate pair structure
                if not isinstance(pair, dict) or 'question' not in pair or 'answer' not in pair:
                    print(f"Skipping invalid pair at index {i}: {pair}")
                    continue  # Skip invalid pairs
                
                try:
                    print(f"Inserting pair {i+1}/{len(email_pairs)}")
                    cur.execute(
                        "INSERT INTO email_pairs (user_id, question, answer) VALUES (%s, %s, %s) RETURNING id",
                        (user_id, pair['question'], pair['answer'])
                    )
                    pair_id = cur.fetchone()['id']
                    print(f"Pair inserted with ID: {pair_id}")
                    valid_pairs += 1
                except Exception as pair_err:
                    print(f"ERROR inserting pair {i+1}: {pair_err}")
                    raise
            
            print(f"Successfully inserted {valid_pairs} email pairs")
            conn.commit()
            print("Email pairs insertion committed")
            
            # Analyze writing style using OpenAI
            print("Starting OpenAI writing style analysis...")
            try:
                style_analysis = analyze_writing_style(email_pairs)
                print("Raw style analysis result type:", type(style_analysis))
                print("Style analysis categories:", [c.get('name') for c in style_analysis.get('categories', [])] if style_analysis and 'categories' in style_analysis else "None")
                
                # Convert style_analysis dict to JSON string
                style_analysis_json = json.dumps(style_analysis)
                print(f"Style analysis JSON string length: {len(style_analysis_json)}")
                
                # Save style analysis to database
                print("Saving style analysis to database")
                cur.execute(
                    "INSERT INTO style_analysis (user_id, analysis_json) VALUES (%s, %s) RETURNING id",
                    (user_id, style_analysis_json)
                )
                analysis_id = cur.fetchone()['id']
                print(f"Style analysis inserted with ID: {analysis_id}")
                conn.commit()
                print("Style analysis insertion committed")
                
                # Generate synthetic emails based on style categories
                print("Starting synthetic email generation...")
                synthetic_emails = generate_synthetic_emails(style_analysis, email_pairs)
                print(f"Synthetic emails generation result: {len(synthetic_emails.keys()) if synthetic_emails else 0} categories")
                
                # Check if we got valid synthetic emails
                if synthetic_emails:
                    print(f"Generated synthetic emails for {len(synthetic_emails)} categories")
                    print(f"Categories: {', '.join(synthetic_emails.keys())}")
                    
                    # Save synthetic emails to database
                    print("Saving synthetic emails to database")
                    total_emails = 0
                    
                    # First, check the table schema
                    print("Checking synthetic_emails table schema")
                    try:
                        cur.execute("""
                            SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_name = 'synthetic_emails'
                        """)
                        columns = [row['column_name'] for row in cur.fetchall()]
                        print(f"Table columns: {columns}")
                        
                        has_rating_feedback = 'rating' in columns and 'feedback' in columns
                        print(f"Table has rating and feedback columns: {has_rating_feedback}")
                    except Exception as schema_err:
                        print(f"ERROR determining table schema: {schema_err}")
                        columns = []
                        has_rating_feedback = False
                    
                    # Now insert the emails
                    for category, emails in synthetic_emails.items():
                        print(f"Processing category: {category} with {len(emails)} emails")
                        
                        for i, email in enumerate(emails):
                            # Check if email is a string or an object with content field
                            if isinstance(email, str):
                                email_content = email
                                print(f"Email {i+1} is a string of length {len(email_content)}")
                            else:
                                email_content = email.get('content', str(email))
                                print(f"Email {i+1} is an object, extracted content of length {len(email_content)}")
                            
                            try:
                                # Use the appropriate INSERT based on schema
                                if has_rating_feedback:
                                    print(f"Inserting email {i+1} with rating/feedback columns")
                                    cur.execute(
                                        "INSERT INTO synthetic_emails (user_id, category, content, approved, rating, feedback) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                                        (user_id, category, email_content, False, None, None)
                                    )
                                else:
                                    print(f"Inserting email {i+1} without rating/feedback columns")
                                    cur.execute(
                                        "INSERT INTO synthetic_emails (user_id, category, content, approved) VALUES (%s, %s, %s, %s) RETURNING id",
                                        (user_id, category, email_content, False)
                                    )
                                
                                email_id = cur.fetchone()['id']
                                print(f"Email inserted with ID: {email_id}")
                                total_emails += 1
                            except Exception as email_err:
                                print(f"ERROR inserting email {i+1}: {email_err}")
                                # Try the alternative schema as a fallback
                                try:
                                    print("Trying fallback insert")
                                    cur.execute(
                                        "INSERT INTO synthetic_emails (user_id, category, content, approved) VALUES (%s, %s, %s, %s) RETURNING id",
                                        (user_id, category, email_content, False)
                                    )
                                    email_id = cur.fetchone()['id']
                                    print(f"Email inserted with fallback with ID: {email_id}")
                                    total_emails += 1
                                except Exception as fallback_err:
                                    print(f"FALLBACK ERROR inserting email: {fallback_err}")
                                    # Print the actual SQL that would be executed
                                    print(f"SQL would be: INSERT INTO synthetic_emails (user_id, category, content, approved) VALUES ({user_id}, '{category}', [content length: {len(email_content)}], False)")
                                    # Continue with the next email rather than aborting
                                    continue
                    
                    print(f"Successfully inserted {total_emails} synthetic emails")
                    conn.commit()
                    print("Synthetic emails insertion committed")
                    
                    print("Sending success response")
                    return jsonify({
                        'success': True,
                        'userId': user_id,
                        'styleAnalysis': style_analysis,
                        'syntheticEmails': synthetic_emails
                    })
                else:
                    print("No synthetic emails were generated")
                    return jsonify({
                        'success': False,
                        'error': "Failed to generate synthetic emails",
                        'userId': user_id,
                        'styleAnalysis': style_analysis
                    }), 500
                
            except Exception as analysis_err:
                print(f"ERROR during analysis or generation: {analysis_err}")
                print(f"Error type: {type(analysis_err)}")
                print(f"Error traceback: {traceback.format_exc()}")
                conn.rollback()
                print("Transaction rolled back")
                return jsonify({
                    'success': False,
                    'error': f"Error during analysis: {str(analysis_err)}",
                    'userId': user_id
                }), 500
        
        except Exception as e:
            conn.rollback()
            print(f"ERROR in submit_emails: {e}")
            print(f"Error type: {type(e)}")
            print(f"Error traceback: {traceback.format_exc()}")
            return jsonify({"error": str(e)}), 500
        
    except Exception as outer_e:
        print(f"CRITICAL ERROR in submit_emails endpoint: {outer_e}")
        print(f"Error type: {type(outer_e)}")
        print(f"Error traceback: {traceback.format_exc()}")
        return jsonify({"error": "Internal server error", "details": str(outer_e)}), 500
    
    finally:
        # Always close the cursor and connection
        try:
            if 'cur' in locals() and cur:
                cur.close()
                print("Cursor closed")
            if 'conn' in locals() and conn:
                conn.close()
                print("Connection closed")
        except Exception as close_err:
            print(f"ERROR closing database resources: {close_err}")
        
        print("="*80)
        print("COMPLETED /api/submit-emails ENDPOINT")
        print("="*80 + "\n")


# API endpoint for user feedback on synthetic emails
@app.route('/api/email-feedback', methods=['POST'])
def email_feedback():
    user_id = request.json.get('userId')
    email_id = request.json.get('emailId')
    is_approved = request.json.get('isApproved')
    rating = request.json.get('rating')
    comments = request.json.get('comments')
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Update email approval status
    cur.execute(
        "UPDATE synthetic_emails SET approved = %s, rating = %s, feedback = %s WHERE id = %s AND user_id = %s",
        (is_approved, rating, comments, email_id, user_id)
    )
    
    conn.commit()
    
    # If not approved, regenerate improved email based on feedback
    if not is_approved and rating and comments:
        # Get the original email content
        cur.execute("SELECT content, category FROM synthetic_emails WHERE id = %s", (email_id,))
        email_data = cur.fetchone()
        
        # Regenerate improved email
        improved_email = regenerate_email(email_data['content'], email_data['category'], comments, rating)
        
        # Save improved email
        cur.execute(
            "INSERT INTO synthetic_emails (user_id, category, content, original_email_id) VALUES (%s, %s, %s, %s) RETURNING id",
            (user_id, email_data['category'], improved_email, email_id)
        )
        new_email_id = cur.fetchone()['id']
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'newEmailId': new_email_id,
            'improvedEmail': improved_email
        })
    
    cur.close()
    conn.close()
    
    return jsonify({'success': True})

# Fixed generate_synthetic_emails function to handle JSON parsing issues
# Function to generate synthetic emails based on style categories with robust error handling
def generate_synthetic_emails(style_analysis, original_emails):
    synthetic_emails = {}
    
    for category in style_analysis['categories']:
        category_name = category['name']
        synthetic_emails[category_name] = []
        
        prompt = f"""
        I need you to generate 3 synthetic emails that match the following style category:
        
        Category: {category_name}
        Description: {category['description']}
        Key Characteristics: {', '.join(category['key_characteristics'])}
        
        These emails should be similar to the user's writing style as described, but should be completely new emails
        on various topics. Make them realistic and varied.
        
        Here are examples of the user's original emails for reference:
        {json.dumps(original_emails, indent=2)}
        
        Generate 3 complete emails with subjects, varying in length and purpose.
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
            
            # Debug: Print the content
            print(f"OpenAI Response for category {category_name} (first 200 chars):", content[:200])
            
            # Remove markdown code blocks if present
            if content.startswith("```") and "```" in content:
                # Find the first and last occurrence of ```
                start = content.find("\n", content.find("```")) + 1
                end = content.rfind("```")
                content = content[start:end].strip()
            
            # Try to parse the JSON response
            try:
                emails = json.loads(content)
                if isinstance(emails, list):
                    synthetic_emails[category_name] = emails
                else:
                    # If response is not a list, check if there's a list inside
                    for key, value in emails.items():
                        if isinstance(value, list) and value:
                            synthetic_emails[category_name] = value
                            break
                    
                    # If no list is found, create a single item list
                    if not synthetic_emails[category_name]:
                        synthetic_emails[category_name] = ["Sample email for " + category_name]
            except json.JSONDecodeError as e:
                print(f"JSON parsing error for category {category_name}: {e}")
                print(f"Content that failed to parse (first 500 chars): {content[:500]}")
                
                # Fallback: Try to find JSON in the response content
                if '[' in content and ']' in content:
                    json_start = content.find('[')
                    json_end = content.rfind(']') + 1
                    json_content = content[json_start:json_end]
                    
                    try:
                        emails_list = json.loads(json_content)
                        if isinstance(emails_list, list):
                            synthetic_emails[category_name] = emails_list
                            continue
                    except:
                        pass
                
                # If still can't parse, create a dummy email
                synthetic_emails[category_name] = [
                    f"Sample email for category: {category_name}.\nDescription: {category['description']}\nKey characteristics: {', '.join(category['key_characteristics'])}"
                ]
                
        except Exception as e:
            print(f"OpenAI API error for category {category_name}: {e}")
            synthetic_emails[category_name] = [
                f"Failed to generate email for category: {category_name} due to an API error."
            ]
    
    return synthetic_emails

# Function to analyze writing style using OpenAI
# Function to analyze writing style using OpenAI with improved JSON parsing
def analyze_writing_style(email_pairs):
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
        print("OpenAI Response:", content)
        
        # Remove markdown code blocks if present
        if content.startswith("```") and "```" in content:
            # Find the first and last occurrence of ```
            start = content.find("\n", content.find("```")) + 1
            end = content.rfind("```")
            content = content[start:end].strip()
        
        # Try to parse the JSON response
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Content that failed to parse: {content}")
            
            # Fallback: Try to find JSON in the response content
            # Sometimes GPT surrounds the JSON with markdown or explanation
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

# Function to generate synthetic emails based on style categories
# Function to generate synthetic emails based on style categories with robust error handling
def generate_synthetic_emails(style_analysis, original_emails):
    print("\n" + "-"*80)
    print("STARTING generate_synthetic_emails")
    print("-"*80)
    
    synthetic_emails = {}
    
    # Limit to 3 emails per category to avoid token limits
    emails_per_category = 3
    
    for category in style_analysis['categories']:
        category_name = category['name']
        print(f"\nProcessing category: {category_name}")
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
            print(f"Calling OpenAI API for category: {category_name}...")
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert email writer who can mimic various writing styles precisely. Always respond with valid JSON without markdown formatting or code blocks."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.choices[0].message.content.strip()
            
            # Debug: Print the raw content
            print(f"Raw response (first 200 chars): {content[:200]}...")
            
            # CRITICAL FIX: Handle markdown code blocks
            if "```" in content:
                print("Detected markdown code blocks in response, cleaning...")
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
                    print(f"Cleaned content (first 200 chars): {content[:200]}...")
                else:
                    # If the blocks are in the middle, try to extract the JSON part
                    if "[" in content and "]" in content:
                        start = content.find("[")
                        end = content.rfind("]") + 1
                        content = content[start:end].strip()
                        print(f"Extracted JSON array (first 200 chars): {content[:200]}...")
            
            # Try to parse the JSON response
            try:
                print("Attempting to parse JSON...")
                emails = json.loads(content)
                
                if isinstance(emails, list):
                    print(f"Successfully parsed JSON array with {len(emails)} emails")
                    synthetic_emails[category_name] = emails
                else:
                    print(f"WARNING: Response is not a list but a {type(emails)}")
                    # If response is a dict, check if it contains an array
                    if isinstance(emails, dict):
                        for key, value in emails.items():
                            if isinstance(value, list) and value:
                                print(f"Found array in key '{key}'")
                                synthetic_emails[category_name] = value
                                break
                        
                    # If still no valid list, create placeholder
                    if not synthetic_emails[category_name]:
                        print("Creating placeholder email")
                        synthetic_emails[category_name] = ["Sample email for " + category_name]
            
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")
                
                # MULTIPLE FALLBACK STRATEGIES
                
                # FALLBACK 1: Try to find and extract a valid JSON array
                if "[" in content and "]" in content:
                    try:
                        print("Fallback 1: Extracting array by brackets")
                        json_start = content.find("[")
                        json_end = content.rfind("]") + 1
                        json_content = content[json_start:json_end]
                        
                        # Additional cleaning - sometimes there are extra characters
                        json_content = json_content.strip()
                        
                        emails_list = json.loads(json_content)
                        if isinstance(emails_list, list):
                            print(f"Fallback 1 successful: Found list with {len(emails_list)} emails")
                            synthetic_emails[category_name] = emails_list
                            continue
                    except Exception as extract_err:
                        print(f"Fallback 1 failed: {extract_err}")
                
                # FALLBACK 2: Try fixing common JSON issues
                try:
                    print("Fallback 2: Fixing common JSON issues")
                    # Replace single quotes with double quotes
                    content = content.replace("'", '"')
                    # Replace JavaScript undefined with null
                    content = content.replace("undefined", "null")
                    # Replace unquoted keys
                    import re
                    content = re.sub(r'([{,])\s*([a-zA-Z0-9_]+)\s*:', r'\1"\2":', content)
                    
                    emails = json.loads(content)
                    if isinstance(emails, list):
                        print(f"Fallback 2 successful: Found list with {len(emails)} emails")
                        synthetic_emails[category_name] = emails
                        continue
                except Exception as fix_err:
                    print(f"Fallback 2 failed: {fix_err}")
                
                # FALLBACK 3: Manual array construction
                if "Subject:" in content or "From:" in content or "To:" in content:
                    print("Fallback 3: Content looks like emails, manual splitting")
                    try:
                        # Try to split by email patterns
                        email_parts = re.split(r'\n\s*Subject:', content)
                        emails_list = []
                        
                        for part in email_parts:
                            if part.strip():
                                if not part.startswith("Subject:"):
                                    part = "Subject:" + part
                                emails_list.append(part.strip())
                        
                        if emails_list:
                            print(f"Fallback 3 successful: Manually split into {len(emails_list)} emails")
                            synthetic_emails[category_name] = emails_list
                            continue
                    except Exception as split_err:
                        print(f"Fallback 3 failed: {split_err}")
                
                # FINAL FALLBACK: Create dummy emails
                print("All fallbacks failed, creating placeholder emails")
                synthetic_emails[category_name] = [
                    f"Subject: Sample Email for {category_name}\n\nDear recipient,\n\nThis is a sample email for the {category_name} category.\n\nBest regards,\nThe System"
                ]
                
        except Exception as e:
            print(f"ERROR with OpenAI API for category {category_name}: {e}")
            # Create fallback emails even if API fails
            synthetic_emails[category_name] = [
                f"Subject: Sample Email {i+1} for {category_name}\n\nDear recipient,\n\nThis is a sample email for the {category_name} category.\n\nBest regards,\nThe System" 
                for i in range(emails_per_category)
            ]
    
    print(f"Generated synthetic emails for {len(synthetic_emails)} categories")
    print("-"*80)
    print("COMPLETED generate_synthetic_emails")
    print("-"*80 + "\n")
    return synthetic_emails

# Function to regenerate improved emails based on user feedback
def regenerate_email(original_email, category, user_feedback, rating):
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

# Add this endpoint to your Flask app (app.py)

@app.route('/api/generate-email', methods=['POST', 'OPTIONS'])
def generate_email():
    # Handle preflight OPTIONS request for CORS
    if request.method == 'OPTIONS':
        return '', 200
        
    print("\n" + "="*80)
    print("STARTING /api/generate-email ENDPOINT")
    print("="*80)
    
    # Setup detailed debugging
    import sys
    import traceback
    
    try:
        data = request.json
        print(f"Request data type: {type(data)}")
        print(f"Request data content: {data}")
        
        user_id = data.get('userId')
        print(f"User ID: {user_id} (type: {type(user_id)})")
        
        recipient = data.get('recipient')
        print(f"Recipient: {recipient}")
        
        topic = data.get('topic')
        print(f"Topic: {topic}")
        
        key_points = data.get('keyPoints', [])
        print(f"Key Points: {key_points} (type: {type(key_points)})")
        
        # Validate required fields with specific error messages
        validation_errors = []
        if not user_id:
            validation_errors.append("User ID is required")
        if not recipient:
            validation_errors.append("Recipient is required")
        if not topic:
            validation_errors.append("Topic is required")
        if not key_points or not isinstance(key_points, list) or len(key_points) == 0:
            validation_errors.append("At least one key point is required")
            
        if validation_errors:
            error_message = ", ".join(validation_errors)
            print(f"Validation error: {error_message}")
            return jsonify({"error": error_message}), 400
            
        print(f"Generating email for user {user_id} to {recipient} about {topic}")
        print(f"Key points: {key_points}")
        
        # Get database connection
        print("Getting database connection...")
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        print("Database connection established")
        
        try:
            # First, verify the user exists
            print(f"Verifying user ID: {user_id}")
            cur.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            user = cur.fetchone()
            
            if not user:
                print(f"User with ID {user_id} not found")
                return jsonify({"error": f"User with ID {user_id} not found"}), 404
            
            print(f"User found: {user}")
            
            # Get user's approved synthetic emails
            print("Fetching approved emails")
            cur.execute(
                "SELECT id, category, content FROM synthetic_emails WHERE user_id = %s AND approved = True LIMIT 5",
                (user_id,)
            )
            approved_emails = cur.fetchall()
            print(f"Found {len(approved_emails)} approved emails")
            if approved_emails:
                print(f"First approved email ID: {approved_emails[0]['id'] if 'id' in approved_emails[0] else 'N/A'}")
            
            # Get user's original email pairs
            print("Fetching original email pairs")
            cur.execute(
                "SELECT question, answer FROM email_pairs WHERE user_id = %s LIMIT 5",
                (user_id,)
            )
            original_emails = cur.fetchall()
            print(f"Found {len(original_emails)} original email pairs")
            if original_emails:
                print(f"First original email answer length: {len(original_emails[0]['answer']) if 'answer' in original_emails[0] else 'N/A'}")
            
            # Get user's style analysis
            print("Fetching style analysis")
            cur.execute(
                "SELECT analysis_json FROM style_analysis WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
                (user_id,)
            )
            style_analysis_row = cur.fetchone()
            
            if style_analysis_row:
                print(f"Raw style_analysis_row: {style_analysis_row}")
                print(f"Raw style_analysis_row type: {type(style_analysis_row)}")
                print(f"Raw style_analysis_row['analysis_json'] type: {type(style_analysis_row['analysis_json'])}")
                
                # Very careful JSON loading with lots of debug info
                try:
                    print(f"Style analysis JSON (first 100 chars): {style_analysis_row['analysis_json'][:100]}...")
                    style_analysis = json.loads(style_analysis_row['analysis_json'])
                    print(f"Style analysis parsed type: {type(style_analysis)}")
                    print(f"Style analysis keys: {list(style_analysis.keys()) if isinstance(style_analysis, dict) else 'Not a dict'}")
                    print("Retrieved style analysis")
                except Exception as json_err:
                    print(f"Error parsing style analysis JSON: {json_err}")
                    print(f"Full error: {traceback.format_exc()}")
                    # Create a default style analysis
                    style_analysis = {
                        "overall_style_summary": "Error parsing style analysis. Using default professional style.",
                        "categories": [
                            {
                                "name": "Default",
                                "description": "Default professional style.",
                                "key_characteristics": ["Professional", "Clear", "Concise"]
                            }
                        ]
                    }
            else:
                print("No style analysis found, creating placeholder")
                style_analysis = {
                    "overall_style_summary": "No style analysis available.",
                    "categories": [
                        {
                            "name": "Default",
                            "description": "Default professional style.",
                            "key_characteristics": ["Professional", "Clear", "Concise"]
                        }
                    ]
                }
            
            print("All data gathered, preparing to generate email")
                
            # Generate new email based on the data
            try:
                print("Calling generate_new_email function")
                print(f"  - recipient: {recipient}")
                print(f"  - topic: {topic}")
                print(f"  - key_points type: {type(key_points)}, length: {len(key_points)}")
                print(f"  - approved_emails type: {type(approved_emails)}, length: {len(approved_emails)}")
                print(f"  - original_emails type: {type(original_emails)}, length: {len(original_emails)}")
                print(f"  - style_analysis type: {type(style_analysis)}")
                
                new_email = generate_new_email(recipient, topic, key_points, approved_emails, original_emails, style_analysis)
                print(f"Generated new email of length: {len(new_email)}")
                print(f"Email preview: {new_email[:100]}...")
            except Exception as gen_err:
                print(f"Error generating email content: {gen_err}")
                print(f"Full traceback: {traceback.format_exc()}")
                return jsonify({"error": f"Error generating email: {str(gen_err)}"}), 500
            
            # Check if generated_emails table exists
            print("Checking if generated_emails table exists")
            try:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'generated_emails'
                    )
                """)
                table_exists = cur.fetchone()['exists']
                print(f"Table exists: {table_exists}")
                
                if not table_exists:
                    print("generated_emails table doesn't exist, creating it...")
                    cur.execute("""
                        CREATE TABLE generated_emails (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER REFERENCES users(id),
                            recipient TEXT NOT NULL,
                            topic TEXT NOT NULL,
                            key_points TEXT,
                            content TEXT NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    conn.commit()
                    print("Table created successfully")
            except Exception as table_err:
                print(f"Error checking/creating table: {table_err}")
                print(f"Full traceback: {traceback.format_exc()}")
                # Continue anyway - we'll handle insert errors separately
            
            # Save the generated email to database
            print("Saving email to database")
            try:
                print(f"key_points before json.dumps: {key_points}")
                print(f"key_points type: {type(key_points)}")
                
                # Convert key_points to a JSON string ONLY if it's not already a string
                if isinstance(key_points, str):
                    key_points_json = key_points
                    print("key_points is already a string, not converting")
                else:
                    print("Converting key_points to JSON string")
                    try:
                        key_points_json = json.dumps(key_points)
                        print(f"key_points_json after conversion: {key_points_json}")
                    except Exception as dump_err:
                        print(f"Error in json.dumps: {dump_err}")
                        print(f"Full traceback: {traceback.format_exc()}")
                        # Use a simple string representation as fallback
                        key_points_json = str(key_points)
                        print(f"Using fallback string representation: {key_points_json}")
                
                print("Executing INSERT query")
                print(f"  - user_id: {user_id} (type: {type(user_id)})")
                print(f"  - recipient: {recipient} (type: {type(recipient)})")
                print(f"  - topic: {topic} (type: {type(topic)})")
                print(f"  - key_points_json: {key_points_json} (type: {type(key_points_json)})")
                print(f"  - new_email length: {len(new_email)}")
                
                cur.execute(
                    "INSERT INTO generated_emails (user_id, recipient, topic, key_points, content) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                    (user_id, recipient, topic, key_points_json, new_email)
                )
                
                email_id = cur.fetchone()['id']
                conn.commit()
                print(f"Saved generated email with ID: {email_id}")
            except Exception as insert_err:
                print(f"Error saving email to database: {insert_err}")
                print(f"Full traceback: {traceback.format_exc()}")
                # If we can't save to DB, still return the generated email
                conn.rollback()
                return jsonify({
                    'success': True,
                    'warning': 'Email was generated but could not be saved to database',
                    'content': new_email
                })
            
            print("Successfully generated and saved email, returning response")
            return jsonify({
                'success': True,
                'emailId': email_id,
                'content': new_email
            })
            
        except Exception as e:
            conn.rollback()
            print(f"ERROR in generate_email: {e}")
            print(f"Full traceback: {traceback.format_exc()}")
            return jsonify({'error': str(e)}), 500
        
        finally:
            cur.close()
            conn.close()
            print("Database resources closed")
    
    except Exception as e:
        print(f"CRITICAL ERROR in generate_email endpoint: {e}")
        print(f"Error type: {type(e)}")
        print(f"Error args: {e.args}")
        print(f"Full traceback: {traceback.format_exc()}")
        return jsonify({'error': "Server error: " + str(e)}), 500
    
    finally:
        print("="*80)
        print("COMPLETED /api/generate-email ENDPOINT")
        print("="*80 + "\n")

# Function to generate new email based on user input with enhanced debugging
def generate_new_email(recipient, topic, key_points, approved_emails, original_emails, style_analysis):
    print("\n" + "-"*80)
    print("STARTING generate_new_email WITH ENHANCED DEBUGGING")
    print("-"*80)
    
    import traceback
    
    # Debug input parameters
    print(f"recipient: {recipient} (type: {type(recipient)})")
    print(f"topic: {topic} (type: {type(topic)})")
    print(f"key_points: {key_points} (type: {type(key_points)})")
    print(f"approved_emails: {type(approved_emails)}, length: {len(approved_emails)}")
    print(f"original_emails: {type(original_emails)}, length: {len(original_emails)}")
    print(f"style_analysis: {type(style_analysis)}")
    
    if isinstance(style_analysis, dict):
        print(f"style_analysis keys: {list(style_analysis.keys())}")
    else:
        print("WARNING: style_analysis is not a dictionary!")
    
    # Prepare examples from approved emails
    examples = []
    print("Processing approved emails:")
    for i, email in enumerate(approved_emails):
        print(f"  Approved email {i+1} type: {type(email)}")
        if isinstance(email, dict):
            print(f"  Approved email {i+1} keys: {list(email.keys())}")
            if 'content' in email:
                examples.append(email['content'])
                print(f"  Added approved email content, length: {len(email['content'])}")
            else:
                print(f"  Skipping approved email {i+1} - no content key")
        else:
            print(f"  Skipping approved email {i+1} - not a dictionary")
    
    # If no approved emails, use original emails
    if not examples:
        print("No approved emails found, processing original emails:")
        for i, email in enumerate(original_emails):
            print(f"  Original email {i+1} type: {type(email)}")
            if isinstance(email, dict):
                print(f"  Original email {i+1} keys: {list(email.keys())}")
                if 'answer' in email:
                    examples.append(email['answer'])
                    print(f"  Added original email answer, length: {len(email['answer'])}")
                else:
                    print(f"  Skipping original email {i+1} - no answer key")
            else:
                print(f"  Skipping original email {i+1} - not a dictionary")
    
    # Limit examples to prevent token limit issues
    if examples:
        print(f"Found {len(examples)} example emails")
        if len(examples) > 3:
            print("Limiting to 3 examples")
            examples = examples[:3]
    else:
        print("No example emails available, using default")
        examples = ["Thank you for your email. I appreciate your time."]
    
    # Debug examples
    for i, example in enumerate(examples):
        print(f"Example {i+1} (first 50 chars): {example[:50]}...")
    
    # Get style summary
    print("Processing style analysis for summary")
    style_summary = ""
    try:
        if isinstance(style_analysis, dict):
            if 'overall_style_summary' in style_analysis:
                style_summary = style_analysis['overall_style_summary']
                print(f"Found style summary: {style_summary[:50]}...")
            else:
                print("No overall_style_summary key in style_analysis")
                style_summary = "Professional, clear, and concise style."
        else:
            print(f"style_analysis is not a dict, it's a {type(style_analysis)}")
            style_summary = "Professional, clear, and concise style."
    except Exception as style_err:
        print(f"Error processing style analysis: {style_err}")
        print(traceback.format_exc())
        style_summary = "Professional, clear, and concise style."
    
    # Convert key_points to a string if it's a list
    print("Processing key points")
    try:
        if isinstance(key_points, list):
            key_points_str = "\n".join([f"- {point}" for point in key_points])
            print(f"Converted key_points list to string, length: {len(key_points_str)}")
        else:
            key_points_str = str(key_points)
            print(f"Converted key_points to string, length: {len(key_points_str)}")
    except Exception as kp_err:
        print(f"Error processing key points: {kp_err}")
        print(traceback.format_exc())
        key_points_str = str(key_points)
    
    # Create a simplified prompt
    print("Creating OpenAI prompt")
    try:
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
        
        print(f"Created prompt of length {len(prompt)}")
        print(f"Prompt preview: {prompt[:100]}...")
    except Exception as prompt_err:
        print(f"Error creating prompt: {prompt_err}")
        print(traceback.format_exc())
        # Fallback to simpler prompt
        prompt = f"Write an email to {recipient} about {topic}. Include the following points: {key_points_str}"
    
    try:
        print("Calling OpenAI API...")
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an AI assistant that drafts emails matching a specific user's writing style. Return only the email content with no additional comments or explanations."},
                {"role": "user", "content": prompt}
            ]
        )
        
        print("OpenAI API call successful")
        content = response.choices[0].message.content.strip()
        print(f"Generated email of length {len(content)}")
        print(f"Email preview: {content[:100]}...")
        
        return content
        
    except Exception as e:
        print(f"ERROR generating email with OpenAI: {e}")
        print(traceback.format_exc())
        raise Exception(f"Email generation failed: {str(e)}")
    finally:
        print("-"*80)
        print("COMPLETED generate_new_email")
        print("-"*80 + "\n")


# API endpoint to get user data
@app.route('/api/user-data', methods=['GET'])
def get_user_data():
    user_identifier = request.args.get('userId')
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Check if this user exists or create them
    if isinstance(user_identifier, str) and not user_identifier.isdigit():
        # Look up user by email/identifier
        cur.execute(
            "SELECT id FROM users WHERE email = %s",
            (user_identifier,)
        )
        user_row = cur.fetchone()
        
        if user_row:
            # User exists, use their ID
            user_id = user_row['id']
        else:
            # Create a new user
            cur.execute(
                "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id",
                (user_identifier, "placeholder_password_hash")
            )
            user_id = cur.fetchone()['id']
            conn.commit()
    else:
        # Assume it's already a valid numeric ID
        user_id = int(user_identifier) if user_identifier else None
    
    if not user_id:
        return jsonify({"error": "User not found"}), 404
    
    # Get user email pairs
    cur.execute(
        "SELECT id, question, answer, created_at FROM email_pairs WHERE user_id = %s ORDER BY created_at DESC",
        (user_id,)
    )
    email_pairs = cur.fetchall()
    
    # Get style analysis if it exists
    cur.execute(
        "SELECT id, analysis_json, created_at FROM style_analysis WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
        (user_id,)
    )
    style_analysis = cur.fetchone()
    
    # Get synthetic emails
    cur.execute(
        "SELECT id, category, content, approved, rating, feedback, created_at FROM synthetic_emails WHERE user_id = %s",
        (user_id,)
    )
    synthetic_emails = cur.fetchall()
    
    # Get generated emails
    cur.execute(
        "SELECT id, recipient, topic, key_points, content, created_at FROM generated_emails WHERE user_id = %s ORDER BY created_at DESC",
        (user_id,)
    )
    generated_emails = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return jsonify({
        "userId": user_id,
        "emailPairs": email_pairs,
        "styleAnalysis": style_analysis['analysis_json'] if style_analysis else None,
        "syntheticEmails": synthetic_emails,
        "generatedEmails": generated_emails
    })

if __name__ == '__main__':
    app.run(debug=True)