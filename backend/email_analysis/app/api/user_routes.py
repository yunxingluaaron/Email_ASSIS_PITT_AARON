from flask import Blueprint, request, jsonify
from app.services.db_service import DatabaseService

# Create blueprint - Make sure this is at the module level
user_bp = Blueprint('user', __name__)

@user_bp.route('/user-data', methods=['GET'])
def get_user_data():
    """
    Get all user data including email pairs, style analysis, synthetic emails, and generated emails
    
    Expects:
    - userId: User ID or email (query parameter)
    
    Returns:
    - userId: User ID
    - emailPairs: Email pairs
    - styleAnalysis: Style analysis
    - syntheticEmails: Synthetic emails
    - generatedEmails: Generated emails
    """
    try:
        # Get user identifier from query parameters
        user_identifier = request.args.get('userId')
        
        if not user_identifier:
            return jsonify({"error": "User ID is required"}), 400
        
        # Get or create user
        user_id = DatabaseService.get_or_create_user(user_identifier)
        
        if not user_id:
            return jsonify({"error": "User not found or could not be created"}), 404
        
        # Get user data
        user_data = DatabaseService.get_user_data(user_id)
        
        return jsonify(user_data)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500