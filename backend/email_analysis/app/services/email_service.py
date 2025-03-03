import json
from app.services.db_service import DatabaseService
from app.services.ai_service import AIService

class EmailService:
    """Service class for email operations"""
    
    @staticmethod
    def submit_emails(user_identifier, email_pairs):
        """
        Process email submission, analyze writing style, and generate synthetic emails
        
        Args:
            user_identifier: User ID or email
            email_pairs: List of email pairs
            
        Returns:
            dict: Result including user ID, style analysis, and synthetic emails
        """
        print("\n" + "="*80)
        print(f"DEBUG: Starting submit_emails for user: {user_identifier}")
        print(f"DEBUG: Number of email pairs: {len(email_pairs)}")
        
        try:
            # Get or create user
            user_id = DatabaseService.get_or_create_user(user_identifier)
            if not user_id:
                print(f"ERROR: User not found or could not be created")
                raise ValueError("User not found or could not be created")
            
            print(f"DEBUG: Using user_id: {user_id}")
                
            # Check if user already has approved synthetic emails
            existing_approved_emails = DatabaseService.get_approved_synthetic_emails(user_id)
            if existing_approved_emails and len(existing_approved_emails) > 0:
                print(f"DEBUG: User has existing approved emails - returning those instead")
                # If user already has approved emails, return them instead of generating new ones
                existing_style_analysis = DatabaseService.get_latest_style_analysis(user_id)
                if existing_style_analysis:
                    return {
                        'success': True,
                        'userId': user_id,
                        'styleAnalysis': existing_style_analysis,
                        'syntheticEmails': existing_approved_emails,
                        'usingExisting': True
                    }
            
            # Save email pairs
            print(f"DEBUG: Saving email pairs")
            valid_pairs = DatabaseService.save_email_pairs(user_id, email_pairs)
            if valid_pairs == 0:
                print(f"ERROR: No valid email pairs provided")
                raise ValueError("No valid email pairs were provided")
            
            print(f"DEBUG: Saved {valid_pairs} valid email pairs")
            
            # Analyze writing style
            print(f"DEBUG: Starting writing style analysis")
            style_analysis = AIService.analyze_writing_style(email_pairs)
            print(f"DEBUG: Writing style analysis completed")
            
            # Save style analysis
            print(f"DEBUG: Converting style analysis to JSON string")
            import json
            style_analysis_json = json.dumps(style_analysis)
            print(f"DEBUG: Saving style analysis to database")
            analysis_id = DatabaseService.save_style_analysis(user_id, style_analysis_json)
            print(f"DEBUG: Style analysis saved with ID: {analysis_id}")
            
            # Generate synthetic emails
            print(f"DEBUG: Generating synthetic emails")
            synthetic_emails = AIService.generate_synthetic_emails(style_analysis, email_pairs)
            print(f"DEBUG: Synthetic emails generated")
            
            # Save synthetic emails
            print(f"DEBUG: Saving synthetic emails to database")
            total_emails = DatabaseService.save_synthetic_emails(user_id, synthetic_emails)
            print(f"DEBUG: Saved {total_emails} synthetic emails")
            
            return {
                'success': True,
                'userId': user_id,
                'styleAnalysis': style_analysis,
                'syntheticEmails': synthetic_emails
            }
        except Exception as e:
            import traceback
            print(f"ERROR in submit_emails: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            raise e
        finally:
            print("="*80 + "\n")
    
    @staticmethod
    def process_email_feedback(user_id, email_id, is_approved, rating, comments):
        """
        Process user feedback on synthetic emails
        
        Args:
            user_id: User ID
            email_id: Email ID
            is_approved: Approval status
            rating: Rating value
            comments: Feedback comments
            
        Returns:
            dict: Result including success status and improved email if applicable
        """
        # Update email approval status
        DatabaseService.update_email_feedback(user_id, email_id, is_approved, rating, comments)
        
        # If not approved, regenerate improved email based on feedback
        if not is_approved and rating and comments:
            # Get the original email content
            email_data = DatabaseService.get_email_content(email_id)
            if not email_data:
                return {'success': False, 'error': 'Email content not found'}
            
            # Regenerate improved email
            improved_email = AIService.regenerate_email(
                email_data['content'], 
                email_data['category'], 
                comments, 
                rating
            )
            
            # Save improved email
            new_email_id = DatabaseService.save_improved_email(
                user_id, 
                email_data['category'], 
                improved_email, 
                email_id
            )
            
            return {
                'success': True,
                'newEmailId': new_email_id,
                'improvedEmail': improved_email
            }
        
        return {'success': True}
    
    @staticmethod
    def generate_email(user_id, recipient, topic, key_points):
        """
        Generate a new email based on user input and style preferences
        
        Args:
            user_id: User ID
            recipient: Email recipient
            topic: Email topic
            key_points: Key points for the email
            
        Returns:
            dict: Result including generated email content
        """
        # First, check if user has a saved style profile
        style_profile = DatabaseService.get_user_style_profile(user_id)
        
        if style_profile:
            print(f"Using saved style profile for user {user_id}")
            
            # Flatten the style profile emails into a list
            profile_emails = []
            for category, emails in style_profile.items():
                for email in emails:
                    profile_emails.append({"content": email})
            
            # Get style analysis
            style_analysis = DatabaseService.get_latest_style_analysis(user_id)
            
            # Generate using the style profile
            new_email = AIService.generate_new_email(
                recipient, 
                topic, 
                key_points, 
                profile_emails,  # Using saved profile emails
                [],  # No need for original emails 
                style_analysis
            )
        else:
            print(f"No saved style profile found for user {user_id}, using standard approach")
            
            # Get user data for style reference
            user_data = DatabaseService.get_user_data(user_id)
            
            # Get approved synthetic emails
            approved_emails = [email for email in user_data['syntheticEmails'] if email['approved']]
            
            # Get original email pairs
            original_emails = user_data['emailPairs']
            
            # Get style analysis
            style_analysis = user_data['styleAnalysis']
            if style_analysis and isinstance(style_analysis, str):
                try:
                    style_analysis = json.loads(style_analysis)
                except json.JSONDecodeError:
                    # Create a default style analysis
                    style_analysis = {
                        "overall_style_summary": "Error parsing style analysis. Using default professional style.",
                        "categories": [
                            {
                                "name": "Default",
                                "description": "Default professional style.",
                                "key_characteristics": ["Professional", "Clear", "Concise"]
                            }
                        ]
                    }
                    
            # Generate email with available user data
            new_email = AIService.generate_new_email(
                recipient, 
                topic, 
                key_points, 
                approved_emails, 
                original_emails, 
                style_analysis
            )
        
        # Convert key_points to JSON string if it's a list
        if isinstance(key_points, list):
            key_points_json = json.dumps(key_points)
        else:
            key_points_json = str(key_points)
        
        # Save the generated email
        email_id = DatabaseService.save_generated_email(
            user_id, 
            recipient, 
            topic, 
            key_points_json, 
            new_email
        )
        
        return {
            'success': True,
            'emailId': email_id,
            'content': new_email
        }