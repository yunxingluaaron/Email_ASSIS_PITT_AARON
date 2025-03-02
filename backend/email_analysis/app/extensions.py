from flask_cors import CORS

# Initialize CORS with options that will be passed to init_app
cors = CORS(resources={r"/api/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"]}})