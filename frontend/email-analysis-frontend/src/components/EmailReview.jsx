import React, { useState, useEffect } from 'react';
import axios from 'axios';

const EmailReview = ({ userId }) => {
  const [emails, setEmails] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [feedback, setFeedback] = useState('');
  const [selectedEmailId, setSelectedEmailId] = useState(null);
  const [rating, setRating] = useState(50);
  const [selectedCategory, setSelectedCategory] = useState('all');

  useEffect(() => {
    const fetchEmails = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`/api/user-data?userId=${userId}`);
        
        // Extract synthetic emails
        const syntheticEmails = response.data.syntheticEmails || [];
        setEmails(syntheticEmails);
        
        // Extract unique categories
        const uniqueCategories = [...new Set(syntheticEmails.map(email => email.category))];
        setCategories(uniqueCategories);
        
        setLoading(false);
      } catch (err) {
        setError(`Error fetching emails: ${err.message}`);
        setLoading(false);
      }
    };

    fetchEmails();
  }, [userId]);

  const handleApprove = async (emailId) => {
    try {
      await axios.post('/api/email-feedback', {
        userId,
        emailId,
        isApproved: true,
        rating: 100,
        comments: 'Approved'
      });
      
      // Update the local state to mark this email as approved
      setEmails(prevEmails => 
        prevEmails.map(email => 
          email.id === emailId ? { ...email, approved: true } : email
        )
      );
    } catch (err) {
      setError(`Error approving email: ${err.message}`);
    }
  };

  const handleReject = async () => {
    if (!selectedEmailId) return;
    
    try {
      const response = await axios.post('/api/email-feedback', {
        userId,
        emailId: selectedEmailId,
        isApproved: false,
        rating,
        comments: feedback
      });
      
      // If we get a new email from the response, add it to our list
      if (response.data.improvedEmail) {
        const originalEmail = emails.find(email => email.id === selectedEmailId);
        const newEmail = {
          id: response.data.newEmailId,
          category: originalEmail.category,
          content: response.data.improvedEmail,
          approved: false,
          created_at: new Date().toISOString()
        };
        
        setEmails(prevEmails => [...prevEmails, newEmail]);
      }
      
      // Reset form
      setSelectedEmailId(null);
      setFeedback('');
      setRating(50);
    } catch (err) {
      setError(`Error rejecting email: ${err.message}`);
    }
  };

  const filteredEmails = selectedCategory === 'all' 
    ? emails 
    : emails.filter(email => email.category === selectedCategory);

  if (loading) return <div>Loading emails...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!emails.length) return <div>No emails found. Please submit some email examples first.</div>;

  return (
    <div className="email-review-container">
      <h2>Review Synthetic Emails</h2>
      
      <div className="filter-controls">
        <label>
          Filter by category:
          <select 
            value={selectedCategory} 
            onChange={e => setSelectedCategory(e.target.value)}
          >
            <option value="all">All Categories</option>
            {categories.map(category => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>
        </label>
      </div>
      
      <div className="emails-list">
        {filteredEmails.map(email => (
          <div key={email.id} className={`email-card ${email.approved ? 'approved' : ''}`}>
            <h3>{email.category}</h3>
            <div className="email-content">
              <pre>{email.content}</pre>
            </div>
            <div className="email-actions">
              {!email.approved ? (
                <>
                  <button 
                    className="approve-btn" 
                    onClick={() => handleApprove(email.id)}
                  >
                    Approve
                  </button>
                  <button 
                    className="reject-btn" 
                    onClick={() => setSelectedEmailId(email.id)}
                  >
                    Reject with Feedback
                  </button>
                </>
              ) : (
                <span className="approved-tag">Approved ✓</span>
              )}
            </div>
          </div>
        ))}
      </div>
      
      {selectedEmailId && (
        <div className="feedback-form">
          <h3>Provide Feedback</h3>
          <p>Rating:</p>
          <input 
            type="range" 
            min="1" 
            max="100" 
            value={rating} 
            onChange={e => setRating(parseInt(e.target.value))} 
          />
          <p>{rating}/100</p>
          
          <label>
            Feedback:
            <textarea 
              value={feedback} 
              onChange={e => setFeedback(e.target.value)}
              placeholder="Please explain what you didn't like about this email and how it could be improved..."
              rows={5}
            />
          </label>
          
          <div className="feedback-actions">
            <button onClick={handleReject}>Submit Feedback</button>
            <button onClick={() => setSelectedEmailId(null)}>Cancel</button>
          </div>
        </div>
      )}
      
      <style jsx>{`
        .email-review-container {
          font-family: Arial, sans-serif;
          max-width: 900px;
          margin: 0 auto;
          padding: 20px;
        }
        
        .filter-controls {
          margin-bottom: 20px;
        }
        
        .emails-list {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
          gap: 20px;
        }
        
        .email-card {
          border: 1px solid #ddd;
          border-radius: 5px;
          padding: 15px;
          background-color: #f9f9f9;
        }
        
        .email-card.approved {
          background-color: #e6f7e6;
          border-color: #9fd89f;
        }
        
        .email-content {
          max-height: 200px;
          overflow-y: auto;
          margin: 10px 0;
          padding: 10px;
          background-color: white;
          border: 1px solid #eee;
          border-radius: 3px;
        }
        
        .email-content pre {
          white-space: pre-wrap;
          word-break: break-word;
        }
        
        .email-actions {
          display: flex;
          justify-content: space-between;
        }
        
        button {
          padding: 8px 15px;
          border: none;
          border-radius: 3px;
          cursor: pointer;
        }
        
        .approve-btn {
          background-color: #4CAF50;
          color: white;
        }
        
        .reject-btn {
          background-color: #f44336;
          color: white;
        }
        
        .approved-tag {
          color: #4CAF50;
          font-weight: bold;
        }
        
        .feedback-form {
          position: fixed;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          background-color: white;
          padding: 20px;
          border-radius: 5px;
          box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
          width: 80%;
          max-width: 500px;
          z-index: 10;
        }
        
        textarea {
          width: 100%;
          padding: 10px;
          margin-top: 5px;
        }
        
        .feedback-actions {
          display: flex;
          justify-content: flex-end;
          gap: 10px;
          margin-top: 15px;
        }
      `}</style>
    </div>
  );
};

export default EmailReview;