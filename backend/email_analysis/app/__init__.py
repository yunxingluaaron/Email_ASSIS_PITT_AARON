from flask import Flask, render_template, redirect, url_for
from app.config import config_by_name
from app.extensions import cors, db
from flask_cors import CORS
from app.model.model import User, Session

def create_app(config_name='dev'):
    """
    Application factory pattern for Flask app
    """
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])
    
    # Initialize extensions
    CORS(app, resources={
        r"/api/*": {
            "origins": "http://localhost:3000",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "X-User-ID", "X-Session-Token"],
            "supports_credentials": True
        }
    })

        # Add a route handler specifically for OPTIONS requests
    @app.route('/api/synthetic-emails', methods=['OPTIONS'])
    def options_synthetic_emails():
        return '', 200

        # Add an after_request handler to ensure OPTIONS requests work
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,X-User-ID,X-Session-Token')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

    db.init_app(app)
    
    # Import models to ensure they are registered with SQLAlchem
    
    # Create database tables within application context
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully!")
        except Exception as e:
            print(f"Error creating database tables: {e}")
    
    # Register blueprints
    from app.api.email_routes import email_bp
    from app.api.user_routes import user_bp
    from app.api.auth_routes import auth_bp
   
    app.register_blueprint(email_bp, url_prefix='/api')
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
   
    # Add routes for HTML pages
    @app.route('/')
    def index():
        return redirect(url_for('login'))
   
    @app.route('/login')
    def login():
        return render_template('login.html')
   
    @app.route('/register')
    def register():
        return render_template('register.html')
   
    @app.route('/dashboard')
    def dashboard():
        return render_template('dashboard.html')
   
    # Register error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
   
    @app.errorhandler(500)
    def server_error(error):
        return {'error': 'Server error'}, 500
   
    return app