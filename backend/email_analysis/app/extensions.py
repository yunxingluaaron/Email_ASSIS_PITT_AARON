from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

# Create extension objects
cors = CORS()
db = SQLAlchemy()