import hashlib
import secrets
from flask import Blueprint, request, jsonify, session
from app.services.db_service import DatabaseService

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User login endpoint
    
    Expects:
    - email: User email
    - password: User password
    
    Returns:
    - success: Login success status
    - userId: User ID if successful
    - message: Status message
    """
    try:
        email = request.json.get('email')
        password = request.json.get('password')
        
        if not email or not password:
            return jsonify({"success": False, "message": "Email and password are required"}), 400
        
        # Hash the password for comparison
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Authenticate user
        user = DatabaseService.authenticate_user(email, password_hash)
        
        if user:
            # Generate a session token
            session_token = secrets.token_hex(16)
            
            # Store the session
            DatabaseService.store_session(user['id'], session_token)
            
            return jsonify({
                "success": True,
                "userId": user['id'],
                "email": user['email'],
                "sessionToken": session_token,
                "message": "Login successful"
            })
        else:
            return jsonify({"success": False, "message": "Invalid email or password"}), 401
    
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    User registration endpoint
    
    Expects:
    - email: User email
    - password: User password
    
    Returns:
    - success: Registration success status
    - userId: User ID if successful
    - message: Status message
    """
    try:
        email = request.json.get('email')
        password = request.json.get('password')
        
        if not email or not password:
            return jsonify({"success": False, "message": "Email and password are required"}), 400
        
        # Check if user already exists
        existing_user = DatabaseService.get_user_by_email(email)
        if existing_user:
            return jsonify({"success": False, "message": "User with this email already exists"}), 409
        
        # Hash the password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Create the user
        user_id = DatabaseService.create_user(email, password_hash)
        
        if user_id:
            # Generate a session token
            session_token = secrets.token_hex(16)
            
            # Store the session
            DatabaseService.store_session(user_id, session_token)
            
            return jsonify({
                "success": True,
                "userId": user_id,
                "email": email,
                "sessionToken": session_token,
                "message": "Registration successful"
            })
        else:
            return jsonify({"success": False, "message": "Failed to create user"}), 500
    
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@auth_bp.route('/verify-session', methods=['POST'])
def verify_session():
    """
    Verify user session token
    
    Expects:
    - userId: User ID
    - sessionToken: Session token
    
    Returns:
    - success: Verification success status
    - message: Status message
    """
    try:
        user_id = request.json.get('userId')
        session_token = request.json.get('sessionToken')
        
        if not user_id or not session_token:
            return jsonify({"success": False, "message": "User ID and session token are required"}), 400
        
        # Verify session
        is_valid = DatabaseService.verify_session(user_id, session_token)
        
        if is_valid:
            return jsonify({
                "success": True,
                "message": "Session valid"
            })
        else:
            return jsonify({"success": False, "message": "Invalid or expired session"}), 401
    
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    User logout endpoint
    
    Expects:
    - userId: User ID
    - sessionToken: Session token
    
    Returns:
    - success: Logout success status
    - message: Status message
    """
    try:
        user_id = request.json.get('userId')
        session_token = request.json.get('sessionToken')
        
        if not user_id or not session_token:
            return jsonify({"success": False, "message": "User ID and session token are required"}), 400
        
        # Clear the session
        DatabaseService.clear_session(user_id, session_token)
        
        return jsonify({
            "success": True,
            "message": "Logout successful"
        })
    
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500