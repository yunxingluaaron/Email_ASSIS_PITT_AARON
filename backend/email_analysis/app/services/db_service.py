import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import current_app
import traceback

def get_db_connection():
    """
    Create and return a database connection
    """
    return psycopg2.connect(
        host=current_app.config['DB_HOST'],
        database=current_app.config['DB_NAME'],
        user=current_app.config['DB_USER'],
        password=current_app.config['DB_PASSWORD']
    )

class DatabaseService:
    """Service class for database operations"""
    
    @staticmethod
    def authenticate_user(email, password_hash):
        """
        Authenticate a user with email and password
        
        Args:
            email: User email
            password_hash: Hashed password
            
        Returns:
            dict: User data if authenticated, None otherwise
        """
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cur.execute(
                "SELECT id, email FROM users WHERE email = %s AND password_hash = %s",
                (email, password_hash)
            )
            user = cur.fetchone()
            return user
        finally:
            cur.close()
            conn.close()
    
    @staticmethod
    def get_user_by_email(email):
        """
        Get user by email
        
        Args:
            email: User email
            
        Returns:
            dict: User data if found, None otherwise
        """
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cur.execute(
                "SELECT id, email FROM users WHERE email = %s",
                (email,)
            )
            user = cur.fetchone()
            return user
        finally:
            cur.close()
            conn.close()
    
    @staticmethod
    def create_user(email, password_hash):
        """
        Create a new user
        
        Args:
            email: User email
            password_hash: Hashed password
            
        Returns:
            int: User ID if created, None otherwise
        """
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cur.execute(
                "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id",
                (email, password_hash)
            )
            user_id = cur.fetchone()['id']
            conn.commit()
            return user_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()
    
    @staticmethod
    def store_session(user_id, session_token):
        """
        Store a user session
        
        Args:
            user_id: User ID
            session_token: Session token
            
        Returns:
            bool: Success status
        """
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Check if user_sessions table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'user_sessions'
                )
            """)
            table_exists = cur.fetchone()['exists']
            
            if not table_exists:
                # Create the table if it doesn't exist
                cur.execute("""
                    CREATE TABLE user_sessions (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id),
                        session_token TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '7 days')
                    )
                """)
                conn.commit()
            
            # Clear any existing sessions for this user
            cur.execute(
                "DELETE FROM user_sessions WHERE user_id = %s",
                (user_id,)
            )
            
            # Store the new session
            cur.execute(
                "INSERT INTO user_sessions (user_id, session_token) VALUES (%s, %s)",
                (user_id, session_token)
            )
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()
    
    @staticmethod
    def verify_session(user_id, session_token):
        """
        Verify a user session
        
        Args:
            user_id: User ID
            session_token: Session token
            
        Returns:
            bool: True if session is valid, False otherwise
        """
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cur.execute(
                "SELECT id FROM user_sessions WHERE user_id = %s AND session_token = %s AND expires_at > CURRENT_TIMESTAMP",
                (user_id, session_token)
            )
            session = cur.fetchone()
            return session is not None
        finally:
            cur.close()
            conn.close()
    
    @staticmethod
    def clear_session(user_id, session_token):
        """
        Clear a user session
        
        Args:
            user_id: User ID
            session_token: Session token
            
        Returns:
            bool: Success status
        """
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cur.execute(
                "DELETE FROM user_sessions WHERE user_id = %s AND session_token = %s",
                (user_id, session_token)
            )
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()
    
    @staticmethod
    def get_or_create_user(user_identifier):
        """
        Get a user by ID or email, or create if they don't exist
        
        Args:
            user_identifier: User ID or email
            
        Returns:
            int: User ID
        """
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        user_id = None
        
        try:
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
                
                # Verify user exists
                if user_id:
                    cur.execute("SELECT id FROM users WHERE id = %s", (user_id,))
                    if not cur.fetchone():
                        user_id = None
        finally:
            cur.close()
            conn.close()
            
        return user_id
    
    @staticmethod
    def save_email_pairs(user_id, email_pairs):
        """
        Save email pairs to the database
        
        Args:
            user_id: User ID
            email_pairs: List of email pairs dictionaries
            
        Returns:
            int: Number of valid pairs saved
        """
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        valid_pairs = 0
        
        try:
            for pair in email_pairs:
                # Validate pair structure
                if not isinstance(pair, dict) or 'question' not in pair or 'answer' not in pair:
                    continue  # Skip invalid pairs
                
                cur.execute(
                    "INSERT INTO email_pairs (user_id, question, answer) VALUES (%s, %s, %s) RETURNING id",
                    (user_id, pair['question'], pair['answer'])
                )
                valid_pairs += 1
                
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()
            
        return valid_pairs
    
    @staticmethod
    def save_style_analysis(user_id, style_analysis_json):
        """
        Save style analysis to the database using SQLAlchemy model
        
        Args:
            user_id: User ID
            style_analysis_json: Style analysis as JSON string
            
        Returns:
            int: Analysis ID
        """
        try:
            from app.model.model import StyleAnalysis
            from app.extensions import db
            
            # Check if user_id needs conversion from string to int
            if isinstance(user_id, str) and user_id.isdigit():
                user_id = int(user_id)
            
            # Create a new StyleAnalysis record
            style_analysis = StyleAnalysis(
                user_id=user_id,
                analysis_data=style_analysis_json
            )
            
            # Add to session and commit
            db.session.add(style_analysis)
            db.session.commit()
            
            print(f"DEBUG: Successfully saved StyleAnalysis for user_id: {user_id}")
            print(f"DEBUG: New StyleAnalysis ID: {style_analysis.id}")
            
            return style_analysis.id
        except Exception as e:
            import traceback
            print(f"ERROR in save_style_analysis: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            db.session.rollback()
            raise e
    
    @staticmethod
    def save_synthetic_emails(user_id, synthetic_emails):
        """
        Save synthetic emails to the database
        
        Args:
            user_id: User ID
            synthetic_emails: Dictionary of synthetic emails by category
            
        Returns:
            int: Number of emails saved
        """
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        total_emails = 0
        
        try:
            # Check the table schema
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'synthetic_emails'
            """)
            columns = [row['column_name'] for row in cur.fetchall()]
            has_rating_feedback = 'rating' in columns and 'feedback' in columns
            
            for category, emails in synthetic_emails.items():
                for email in emails:
                    # Check if email is a string or an object with content field
                    if isinstance(email, str):
                        email_content = email
                    else:
                        email_content = email.get('content', str(email))
                    
                    try:
                        # Use the appropriate INSERT based on schema
                        if has_rating_feedback:
                            cur.execute(
                                "INSERT INTO synthetic_emails (user_id, category, content, approved, rating, feedback) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                                (user_id, category, email_content, False, None, None)
                            )
                        else:
                            cur.execute(
                                "INSERT INTO synthetic_emails (user_id, category, content, approved) VALUES (%s, %s, %s, %s) RETURNING id",
                                (user_id, category, email_content, False)
                            )
                        
                        total_emails += 1
                    except Exception:
                        # Try the alternative schema as a fallback
                        try:
                            cur.execute(
                                "INSERT INTO synthetic_emails (user_id, category, content, approved) VALUES (%s, %s, %s, %s) RETURNING id",
                                (user_id, category, email_content, False)
                            )
                            total_emails += 1
                        except Exception:
                            # Continue with the next email rather than aborting
                            continue
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()
            
        return total_emails
    
    @staticmethod
    def update_email_feedback(user_id, email_id, is_approved, rating, comments):
        """
        Update email approval status and feedback
        
        Args:
            user_id: User ID
            email_id: Email ID
            is_approved: Approval status
            rating: Rating value
            comments: Feedback comments
            
        Returns:
            bool: Success status
        """
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cur.execute(
                "UPDATE synthetic_emails SET approved = %s, rating = %s, feedback = %s WHERE id = %s AND user_id = %s",
                (is_approved, rating, comments, email_id, user_id)
            )
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()
    
    @staticmethod
    def get_email_content(email_id):
        """
        Get email content and category by ID
        
        Args:
            email_id: Email ID
            
        Returns:
            dict: Email data
        """
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cur.execute("SELECT content, category FROM synthetic_emails WHERE id = %s", (email_id,))
            email_data = cur.fetchone()
            return email_data
        finally:
            cur.close()
            conn.close()
    
    @staticmethod
    def save_improved_email(user_id, category, content, original_email_id):
        """
        Save improved email to database
        
        Args:
            user_id: User ID
            category: Email category
            content: Email content
            original_email_id: Original email ID
            
        Returns:
            int: New email ID
        """
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cur.execute(
                "INSERT INTO synthetic_emails (user_id, category, content, original_email_id) VALUES (%s, %s, %s, %s) RETURNING id",
                (user_id, category, content, original_email_id)
            )
            new_email_id = cur.fetchone()['id']
            conn.commit()
            return new_email_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()
            
    @staticmethod
    def save_generated_email(user_id, recipient, topic, key_points, content):
        """
        Save generated email to database
        
        Args:
            user_id: User ID
            recipient: Email recipient
            topic: Email topic
            key_points: Key points for the email
            content: Email content
            
        Returns:
            int: Email ID
        """
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Check if generated_emails table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'generated_emails'
                )
            """)
            table_exists = cur.fetchone()['exists']
            
            if not table_exists:
                # Create the table if it doesn't exist
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
            
            cur.execute(
                "INSERT INTO generated_emails (user_id, recipient, topic, key_points, content) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (user_id, recipient, topic, key_points, content)
            )
            email_id = cur.fetchone()['id']
            conn.commit()
            return email_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()
    
    @staticmethod
    def get_approved_synthetic_emails(user_id):
        """
        Get approved synthetic emails for a user, organized by category
        
        Args:
            user_id: User ID
            
        Returns:
            dict: Dictionary of approved synthetic emails by category
        """
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Get approved synthetic emails
            cur.execute(
                "SELECT id, category, content FROM synthetic_emails WHERE user_id = %s AND approved = True",
                (user_id,)
            )
            approved_emails = cur.fetchall()
            
            # Organize by category
            emails_by_category = {}
            for email in approved_emails:
                category = email['category']
                if category not in emails_by_category:
                    emails_by_category[category] = []
                
                emails_by_category[category].append(email['content'])
            
            return emails_by_category if emails_by_category else None
        finally:
            cur.close()
            conn.close()
    
# 4. Update the get_latest_style_analysis method to handle both field names
    @staticmethod
    def get_latest_style_analysis(user_id):
        """
        Get the latest style analysis for a user
        
        Args:
            user_id: The user's ID
            
        Returns:
            dict: Style analysis data or None if not found
        """
        print("\n" + "="*80)
        print(f"DEBUG: get_latest_style_analysis called for user_id: {user_id}")
        
        try:
            print(f"DEBUG: Importing StyleAnalysis model")
            from app.model.model import StyleAnalysis
            import json
            print(f"DEBUG: Successfully imported StyleAnalysis model")
            
            # Print the user_id type to help with debugging
            print(f"DEBUG: User ID type: {type(user_id)}")
            
            # Convert user_id to integer if it's a string
            if isinstance(user_id, str) and user_id.isdigit():
                user_id = int(user_id)
                print(f"DEBUG: Converted user_id to integer: {user_id}")
                
            print(f"DEBUG: Querying database for StyleAnalysis with user_id: {user_id}")
            
            # Get the count first to verify if any records exist
            analysis_count = StyleAnalysis.query.filter_by(user_id=user_id).count()
            print(f"DEBUG: Found {analysis_count} StyleAnalysis records for user_id: {user_id}")
            
            if analysis_count == 0:
                print(f"DEBUG: No StyleAnalysis found for user: {user_id}")
                return None
            
            # Get the latest analysis
            style_analysis = StyleAnalysis.query.filter_by(user_id=user_id).order_by(StyleAnalysis.created_at.desc()).first()
            
            print(f"DEBUG: Retrieved StyleAnalysis with ID: {style_analysis.id if style_analysis else None}")
            
            if style_analysis is None:
                print(f"DEBUG: No StyleAnalysis found for user: {user_id}")
                return None
            
            # Try to access analysis_data first (from the model definition)
            if hasattr(style_analysis, 'analysis_data') and style_analysis.analysis_data:
                print(f"DEBUG: Found analysis_data field")
                try:
                    if isinstance(style_analysis.analysis_data, str):
                        print(f"DEBUG: Parsing analysis_data as JSON string")
                        return json.loads(style_analysis.analysis_data)
                    elif isinstance(style_analysis.analysis_data, dict):
                        print(f"DEBUG: analysis_data is already a dictionary")
                        return style_analysis.analysis_data
                    else:
                        print(f"DEBUG: Unexpected type for analysis_data: {type(style_analysis.analysis_data)}")
                except json.JSONDecodeError as e:
                    print(f"DEBUG: Error parsing analysis_data as JSON: {e}")
            
            # Fallback to analysis_json if the field exists (from SQL queries)
            if hasattr(style_analysis, 'analysis_json') and style_analysis.analysis_json:
                print(f"DEBUG: Using analysis_json field")
                try:
                    if isinstance(style_analysis.analysis_json, str):
                        print(f"DEBUG: Parsing analysis_json as JSON string")
                        return json.loads(style_analysis.analysis_json)
                    elif isinstance(style_analysis.analysis_json, dict):
                        print(f"DEBUG: analysis_json is already a dictionary")
                        return style_analysis.analysis_json
                    else:
                        print(f"DEBUG: Unexpected type for analysis_json: {type(style_analysis.analysis_json)}")
                except json.JSONDecodeError as e:
                    print(f"DEBUG: Error parsing analysis_json as JSON: {e}")
            
            print(f"DEBUG: Could not extract valid style analysis data")
            return None
                
        except Exception as e:
            import traceback
            print(f"DEBUG: Exception in get_latest_style_analysis: {str(e)}")
            print(f"DEBUG: Exception traceback: {traceback.format_exc()}")
            return None
        finally:
            print("="*80 + "\n")
    
    @staticmethod
    def save_style_profile(user_id):
        """
        Save a user's approved synthetic emails as their permanent style profile
        
        Args:
            user_id: User ID
            
        Returns:
            bool: Success status
        """
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Check if user_style_profiles table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'user_style_profiles'
                )
            """)
            table_exists = cur.fetchone()['exists']
            
            if not table_exists:
                # Create the table if it doesn't exist
                cur.execute("""
                    CREATE TABLE user_style_profiles (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id),
                        category VARCHAR(255) NOT NULL,
                        content TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
            
            # Get user's approved synthetic emails
            cur.execute(
                "SELECT id, category, content FROM synthetic_emails WHERE user_id = %s AND approved = True",
                (user_id,)
            )
            approved_emails = cur.fetchall()
            
            if not approved_emails:
                return False
            
            # Clear any existing style profile for this user
            cur.execute(
                "DELETE FROM user_style_profiles WHERE user_id = %s",
                (user_id,)
            )
            
            # Save approved emails as style profile
            for email in approved_emails:
                cur.execute(
                    "INSERT INTO user_style_profiles (user_id, category, content) VALUES (%s, %s, %s)",
                    (user_id, email['category'], email['content'])
                )
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()
    
    @staticmethod
    def get_user_style_profile(user_id):
        """
        Get a user's style profile
        
        Args:
            user_id: User ID
            
        Returns:
            dict: Style profile by category
        """
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Check if table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'user_style_profiles'
                )
            """)
            table_exists = cur.fetchone()['exists']
            
            if not table_exists:
                return None
            
            # Get style profile
            cur.execute(
                "SELECT id, category, content FROM user_style_profiles WHERE user_id = %s",
                (user_id,)
            )
            profile_emails = cur.fetchall()
            
            # Organize by category
            profile_by_category = {}
            for email in profile_emails:
                category = email['category']
                if category not in profile_by_category:
                    profile_by_category[category] = []
                
                profile_by_category[category].append(email['content'])
            
            return profile_by_category if profile_by_category else None
        finally:
            cur.close()
            conn.close()
    
    @staticmethod
    def get_user_data(user_id):
        """
        Get all user data including email pairs, style analysis, synthetic emails, and generated emails
        
        Args:
            user_id: User ID
            
        Returns:
            dict: User data
        """
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
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
            
            return {
                "userId": user_id,
                "emailPairs": email_pairs,
                "styleAnalysis": style_analysis['analysis_json'] if style_analysis else None,
                "syntheticEmails": synthetic_emails,
                "generatedEmails": generated_emails
            }
        finally:
            cur.close()
            conn.close()