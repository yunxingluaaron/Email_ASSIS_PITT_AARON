from functools import wraps
from flask import request, jsonify
from app.services.db_service import DatabaseService

def require_auth(f):
    """
    Authentication middleware to protect API routes
    
    Usage:
    @app.route('/protected-route')
    @require_auth
    def protected_route():
        # Access authenticated user via request.user_id
        pass
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Get authentication headers
        user_id = request.headers.get('X-User-ID')
        session_token = request.headers.get('X-Session-Token')
        
        # Check if auth headers are present
        if not user_id or not session_token:
            return jsonify({"error": "Authentication required", "code": "auth_required"}), 401
        
        # Verify session
        is_valid = DatabaseService.verify_session(user_id, session_token)
        
        if not is_valid:
            return jsonify({"error": "Invalid or expired session", "code": "invalid_session"}), 401
        
        # Set user_id in request for use in the route handler
        request.user_id = user_id
        
        return f(*args, **kwargs)
    
    return decorated