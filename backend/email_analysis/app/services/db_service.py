import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import current_app

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
        Save style analysis to the database
        
        Args:
            user_id: User ID
            style_analysis_json: Style analysis as JSON string
            
        Returns:
            int: Analysis ID
        """
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cur.execute(
                "INSERT INTO style_analysis (user_id, analysis_json) VALUES (%s, %s) RETURNING id",
                (user_id, style_analysis_json)
            )
            analysis_id = cur.fetchone()['id']
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()
            
        return analysis_id
    
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