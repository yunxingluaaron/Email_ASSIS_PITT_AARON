from flask import Flask
from app.config import config_by_name
from app.extensions import cors

def create_app(config_name='dev'):
    """
    Application factory pattern for Flask app
    """
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])
    
    # Initialize extensions
    cors.init_app(app)
    
    # Register blueprints
    from app.api.email_routes import email_bp
    from app.api.user_routes import user_bp
    
    app.register_blueprint(email_bp, url_prefix='/api')
    app.register_blueprint(user_bp, url_prefix='/api')
    
    # Register error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def server_error(error):
        return {'error': 'Server error'}, 500
    
    return app