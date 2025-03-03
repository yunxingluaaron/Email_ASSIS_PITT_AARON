import traceback
import json
from flask import Blueprint, request, jsonify, current_app
from app.services.email_service import EmailService
from app.services.db_service import DatabaseService
from app.model.model import SyntheticEmail, StyleAnalysis, EmailPair
from app.services.ai_service import AIService
from app.extensions import db

# Create blueprint
email_bp = Blueprint('email', __name__)

@email_bp.route('/submit-emails', methods=['POST'])
def submit_emails():
    """
    Process email submission, analyze writing style, and generate synthetic emails
    
    Expects:
    - userId: User ID or email
    - emailPairs: List of email pairs with question and answer fields
    
    Returns:
    - userId: User ID
    - styleAnalysis: Writing style analysis
    - syntheticEmails: Generated synthetic emails
    """
    print("\n" + "="*80)
    print("STARTING /api/submit-emails ENDPOINT")
    print("="*80)
    
    try:
        # Get request data
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
        
        # Process emails
        print("Processing emails...")
        result = EmailService.submit_emails(user_identifier, email_pairs)
        print("Email processing completed successfully")
        
        return jsonify(result)
    
    except ValueError as e:
        print(f"ERROR: {str(e)}")
        return jsonify({"error": str(e)}), 400
    
    except Exception as e:
        print(f"CRITICAL ERROR in submit_emails endpoint: {e}")
        print(f"Error traceback: {traceback.format_exc()}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500
    
    finally:
        print("="*80)
        print("COMPLETED /api/submit-emails ENDPOINT")
        print("="*80 + "\n")

@email_bp.route('/synthetic-emails', methods=['GET'])
def get_synthetic_emails():
    """
    Endpoint to get synthetic emails for a user
    """
    try:
        # Get user ID from headers
        user_id = request.headers.get('X-User-ID')
        
        if not user_id:
            return jsonify({'error': 'User ID is required in the X-User-ID header'}), 400
        
        print(f"Fetching synthetic emails for user ID: {user_id}")
        
        # Check if synthetic emails exist for this user
        synthetic_emails = SyntheticEmail.query.filter_by(user_id=user_id).all()
        
        # If no synthetic emails found, return dummy data
        if not synthetic_emails:
            print(f"No synthetic emails found for user ID: {user_id}")
            # Return dummy data during development
            dummy_emails = {
                "Formal": [
                    {"id": "Formal_1", "content": "Subject: Quarterly Budget Review\n\nDear Finance Team,\n\nI'm writing to schedule our quarterly budget review meeting. Please prepare the necessary reports for the discussion.\n\nBest regards,\nThe Manager"}
                ],
                "Casual": [
                    {"id": "Casual_1", "content": "Subject: Team Lunch Next Week\n\nHi everyone,\n\nJust wanted to organize a team lunch next Wednesday. Let me know if you can make it!\n\nCheers,\nThe Manager"}
                ],
                "Professional": [
                    {"id": "Professional_1", "content": "Subject: Project Status Update\n\nHello Team,\n\nI'm sharing our weekly project status update. We've made significant progress on the backend integration, and we're on track to meet our deadline.\n\nRegards,\nProject Manager"}
                ]
            }
            return jsonify(dummy_emails)
        
        # Rest of your code for handling synthetic emails...
        
    except Exception as e:
        print(f"Error in get_synthetic_emails: {e}")
        print(traceback.format_exc())
        
        # Return dummy data on error
        dummy_emails = {
            "Formal": [
                {"id": "Formal_1", "content": "Subject: Quarterly Budget Review\n\nDear Finance Team,\n\nI'm writing to schedule our quarterly budget review meeting. Please prepare the necessary reports for the discussion.\n\nBest regards,\nThe Manager"}
            ],
            "Casual": [
                {"id": "Casual_1", "content": "Subject: Team Lunch Next Week\n\nHi everyone,\n\nJust wanted to organize a team lunch next Wednesday. Let me know if you can make it!\n\nCheers,\nThe Manager"}
            ]
        }
        return jsonify(dummy_emails)

@email_bp.route('/api/email-feedback', methods=['POST', 'OPTIONS'])
def submit_email_feedback():
    """
    Endpoint to submit feedback on synthetic emails
    """
    # Handle OPTIONS request (preflight)
    if request.method == 'OPTIONS':
        return '', 200
        
    data = request.json
    
    # Validate request
    if not data:
        return jsonify({'error': 'Missing request data'}), 400
        
    if 'emailId' not in data or 'category' not in data:
        return jsonify({'error': 'Missing required feedback data (emailId or category)'}), 400
    
    # Get user ID from request or headers
    user_id = data.get('userId') or request.headers.get('X-User-ID')
    
    if not user_id:
        return jsonify({'error': 'User ID is required in the request body or X-User-ID header'}), 400
    
    email_id = data.get('emailId')
    category = data.get('category')
    is_approved = data.get('isApproved', False)
    rating = data.get('rating')
    comments = data.get('comments')
    
    try:
        # Find the email
        email = SyntheticEmail.query.filter_by(id=email_id, user_id=user_id).first()
        
        if not email:
            print(f"Email not found: id={email_id}, user_id={user_id}")
            return jsonify({'error': 'Email not found'}), 404
        
        # If email is approved, just update its status
        if is_approved:
            # Update metadata to mark as approved
            try:
                metadata = json.loads(email.email_metadata) if email.email_metadata else {}
                metadata['approved'] = True
                email.email_metadata = json.dumps(metadata)
                db.session.commit()
                
                return jsonify({'success': True, 'message': 'Email approved'})
            except Exception as e:
                print(f"Error updating email status: {e}")
                return jsonify({'error': f'Failed to update email status: {str(e)}'}), 500
        
        # If email needs improvement and we have rating and comments
        if not is_approved and rating and comments:
            # Get the original email content
            original_content = email.content
            
            # Use AI service to regenerate email based on feedback
            ai_service = AIService()
            improved_email = ai_service.regenerate_email(
                original_content,
                category,
                comments,
                rating
            )
            
            # Store the improved email
            new_email = SyntheticEmail(
                user_id=user_id,
                category=category,
                content=improved_email,
                email_metadata=json.dumps({
                    'id': f"improved_{email_id}",
                    'content': improved_email,
                    'based_on': email_id,
                    'feedback': comments,
                    'rating': rating
                })
            )
            db.session.add(new_email)
            
            # Optionally mark the original as replaced
            try:
                metadata = json.loads(email.email_metadata) if email.email_metadata else {}
                metadata['replaced'] = True
                metadata['replaced_by'] = f"improved_{email_id}"
                email.email_metadata = json.dumps(metadata)
            except Exception as e:
                print(f"Error updating original email metadata: {e}")
                pass
            
            db.session.commit()
            
            # Get all emails for this category to return
            category_emails = SyntheticEmail.query.filter_by(
                user_id=user_id,
                category=category
            ).all()
            
            # Format them for response
            updated_emails = []
            for cat_email in category_emails:
                try:
                    email_data = json.loads(cat_email.email_metadata) if cat_email.email_metadata else {}
                    
                    # Skip replaced emails
                    if email_data.get('replaced', False):
                        continue
                    
                    # Ensure email_data has content and id
                    if 'id' not in email_data:
                        email_data['id'] = cat_email.id
                    if 'content' not in email_data:
                        email_data['content'] = cat_email.content
                    
                    updated_emails.append(email_data)
                except Exception as e:
                    print(f"Error processing email data: {e}")
                    updated_emails.append({
                        'id': cat_email.id,
                        'content': cat_email.content
                    })
            
            return jsonify({
                'success': True, 
                'message': 'Email improved based on feedback',
                'updatedEmails': updated_emails
            })
        
        return jsonify({'error': 'Invalid feedback data'}), 400
    
    except Exception as e:
        print(f"Error in submit_email_feedback: {e}")
        print(traceback.format_exc())
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@email_bp.route('/save-style-profile', methods=['POST'])
def save_style_profile():
    """
    Save a user's approved synthetic emails as their permanent style profile
    
    Expects:
    - userId: User ID
    
    Returns:
    - success: Success status
    - message: Status message
    """
    try:
        user_id = request.json.get('userId')
        
        if not user_id:
            return jsonify({"success": False, "message": "User ID is required"}), 400
        
        # Save the current approved synthetic emails as the user's permanent style profile
        result = DatabaseService.save_style_profile(user_id)
        
        if result:
            return jsonify({
                "success": True,
                "message": "Style profile saved successfully"
            })
        else:
            return jsonify({
                "success": False,
                "message": "No approved emails found to save as style profile"
            }), 400
            
    except Exception as e:
        print(f"ERROR in save_style_profile: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@email_bp.route('/generate-email', methods=['POST', 'OPTIONS'])
def generate_email():
    """
    Generate a new email based on user input and style preferences
    
    Expects:
    - userId: User ID
    - recipient: Email recipient
    - topic: Email topic
    - keyPoints: Key points for the email
    
    Returns:
    - success: Success status
    - emailId: Email ID
    - content: Generated email content
    """
    # Handle preflight OPTIONS request for CORS
    if request.method == 'OPTIONS':
        return '', 200
    
    print("\n" + "="*80)
    print("STARTING /api/generate-email ENDPOINT")
    print("="*80)
    
    try:
        # Get request data
        data = request.json
        user_id = data.get('userId')
        recipient = data.get('recipient')
        topic = data.get('topic')
        key_points = data.get('keyPoints', [])
        
        print(f"User ID: {user_id}")
        print(f"Recipient: {recipient}")
        print(f"Topic: {topic}")
        print(f"Key Points: {key_points}")
        
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
        
        # Generate email
        print(f"Generating email for user {user_id} to {recipient} about {topic}")
        result = EmailService.generate_email(user_id, recipient, topic, key_points)
        print("Email generation completed successfully")
        
        return jsonify(result)
    
    except Exception as e:
        print(f"CRITICAL ERROR in generate_email endpoint: {e}")
        print(f"Error traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
    
    finally:
        print("="*80)
        print("COMPLETED /api/generate-email ENDPOINT")
        print("="*80 + "\n")


@email_bp.route('/style-analysis', methods=['GET', 'OPTIONS'])
def get_style_analysis():
    """
    Get the writing style analysis for a user
    
    Expected headers:
    - X-User-ID: User identifier
    - X-Session-Token: Session authentication token
    
    Returns:
    - overall_style_summary: Summary of writing style
    - categories: List of style categories with descriptions and characteristics
    """
    print("\n" + "="*80)
    print("STARTING /api/style-analysis ENDPOINT")
    print("="*80)
    
    # Handle OPTIONS request (preflight)
    if request.method == 'OPTIONS':
        print("Handling OPTIONS request")
        return '', 200
        
    try:
        # Get user credentials from headers
        user_id = request.headers.get('X-User-ID')
        session_token = request.headers.get('X-Session-Token')
        
        print(f"Style analysis request for user: {user_id}")
        print(f"Headers: {dict(request.headers)}")
        
        # Validate required headers
        if not user_id:
            print("Error: User ID is required")
            return jsonify({"error": "User ID is required"}), 400
            
        # Debug log of all routes
        print(f"All registered routes: {[str(rule) for rule in current_app.url_map.iter_rules()]}")
            
        print(f"Calling DatabaseService.get_latest_style_analysis({user_id})")
        # Get the user's style analysis from database
        analysis = DatabaseService.get_latest_style_analysis(user_id)
        
        print(f"Analysis result: {analysis}")
        
        # If no analysis found, we should MANUALLY return dummy data for development
        # instead of a 404 error
        if not analysis:
            print("No analysis found, returning dummy data for development")
            
            dummy_data = {
                "overall_style_summary": "Your writing style is characterized by a professional tone with clear and direct communication. You tend to be concise while still being thorough in addressing key points.",
                "categories": [
                    {
                        "name": "Formality",
                        "description": "You maintain a professional tone without being overly formal. Your emails strike a good balance between professionalism and approachability.",
                        "key_characteristics": ["Professional", "Polished", "Appropriate", "Business-casual"],
                        "score": 75
                    },
                    {
                        "name": "Clarity",
                        "description": "Your writing is clear and straightforward. You use simple language and avoid unnecessary jargon, making your emails easy to understand.",
                        "key_characteristics": ["Direct", "Precise", "Logical", "Structured"],
                        "score": 85
                    },
                    {
                        "name": "Tone",
                        "description": "Your communication style is generally positive and respectful. You tend to be courteous while maintaining authority in your area of expertise.",
                        "key_characteristics": ["Respectful", "Positive", "Confident", "Balanced"],
                        "score": 80
                    }
                ]
            }
            return jsonify(dummy_data)
            
            # Commented out to always return dummy data during development
            # return jsonify({"error": "No style analysis found for this user. Please submit email samples first."}), 404
            
        # Format and return the analysis
        result = {
            "overall_style_summary": analysis.get("summary", "No style summary available."),
            "categories": []
        }
        
        # Add all style categories to the response
        for category in analysis.get("categories", []):
            result["categories"].append({
                "name": category.get("name", ""),
                "description": category.get("description", ""),
                "key_characteristics": category.get("characteristics", []),
                "score": category.get("score", 0)
            })
            
        print(f"Successfully retrieved style analysis for user: {user_id}")
        print(f"Formatted result: {result}")
        return jsonify(result)
        
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error fetching style analysis: {str(e)}")
        print(f"Error details: {error_details}")
        
        # ALWAYS return dummy data during development
        print("Returning dummy data due to exception")
        dummy_data = {
            "overall_style_summary": "Your writing style is characterized by a professional tone with clear and direct communication. You tend to be concise while still being thorough in addressing key points.",
            "categories": [
                {
                    "name": "Formality",
                    "description": "You maintain a professional tone without being overly formal. Your emails strike a good balance between professionalism and approachability.",
                    "key_characteristics": ["Professional", "Polished", "Appropriate", "Business-casual"],
                    "score": 75
                },
                {
                    "name": "Clarity",
                    "description": "Your writing is clear and straightforward. You use simple language and avoid unnecessary jargon, making your emails easy to understand.",
                    "key_characteristics": ["Direct", "Precise", "Logical", "Structured"],
                    "score": 85
                },
                {
                    "name": "Tone",
                    "description": "Your communication style is generally positive and respectful. You tend to be courteous while maintaining authority in your area of expertise.",
                    "key_characteristics": ["Respectful", "Positive", "Confident", "Balanced"],
                    "score": 80
                }
            ]
        }
        
        return jsonify(dummy_data)
    finally:
        print("="*80)
        print("COMPLETED /api/style-analysis ENDPOINT")
        print("="*80 + "\n")