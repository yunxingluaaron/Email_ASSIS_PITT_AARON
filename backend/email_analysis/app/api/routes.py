import traceback
from flask import Blueprint, request, jsonify
from app.services.email_service import EmailService

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

@email_bp.route('/email-feedback', methods=['POST'])
def email_feedback():
    """
    Process user feedback on synthetic emails
    
    Expects:
    - userId: User ID
    - emailId: Email ID
    - isApproved: Approval status
    - rating: Rating value
    - comments: Feedback comments
    
    Returns:
    - success: Success status
    - newEmailId: ID of improved email (if applicable)
    - improvedEmail: Improved email content (if applicable)
    """
    try:
        # Get request data
        user_id = request.json.get('userId')
        email_id = request.json.get('emailId')
        is_approved = request.json.get('isApproved')
        rating = request.json.get('rating')
        comments = request.json.get('comments')
        
        # Validate input
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        if not email_id:
            return jsonify({"error": "Email ID is required"}), 400
        
        # Process feedback
        result = EmailService.process_email_feedback(user_id, email_id, is_approved, rating, comments)
        
        return jsonify(result)
    
    except Exception as e:
        print(f"ERROR in email_feedback: {e}")
        print(f"Error traceback: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

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