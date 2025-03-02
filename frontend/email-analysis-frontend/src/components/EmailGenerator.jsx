import React, { useState } from 'react';
import axios from 'axios';

const EmailGenerator = ({ userId = 1 }) => {
  const [recipient, setRecipient] = useState('');
  const [topic, setTopic] = useState('');
  const [keyPoints, setKeyPoints] = useState('');
  const [keyPointsList, setKeyPointsList] = useState([]);
  const [generatedEmail, setGeneratedEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleAddKeyPoint = () => {
    if (keyPoints.trim()) {
      setKeyPointsList([...keyPointsList, keyPoints.trim()]);
      setKeyPoints('');
    }
  };

  const handleRemoveKeyPoint = (index) => {
    const newList = [...keyPointsList];
    newList.splice(index, 1);
    setKeyPointsList(newList);
  };

  const effectiveUserId = 1; // Hardcoded user ID for testing

  const handleSubmit = async (e) => {
    e.preventDefault();

    
    if (!effectiveUserId) {
      setError('User ID is missing. Please make sure you are logged in.');
      return;
    }
    
    if (!recipient.trim()) {
      setError('Recipient is required');
      return;
    }
    
    if (!topic.trim()) {
      setError('Topic is required');
      return;
    }
    
    if (keyPointsList.length === 0) {
      setError('At least one key point is required');
      return;
    }
    
    setLoading(true);
    setError('');
    setSuccess(false);
    
    console.log("Sending request with userId:", effectiveUserId);
    
    try {
      const response = await axios.post('http://localhost:5000/api/generate-email', {
        userId: effectiveUserId,
        recipient: recipient,
        topic: topic,
        keyPoints: keyPointsList
      });
      
      console.log("Response received:", response.data);
      setGeneratedEmail(response.data.content);
      setSuccess(true);
      setLoading(false);
    } catch (err) {
      console.error('Error generating email:', err);
      
      // More detailed error message
      let errorMessage = 'Failed to generate email';
      if (err.response) {
        // The request was made and the server responded with an error status
        console.error('Response error data:', err.response.data);
        errorMessage = err.response.data.error || `Server error: ${err.response.status}`;
      } else if (err.request) {
        // The request was made but no response was received
        errorMessage = 'No response received from server';
      }
      
      setError(errorMessage);
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddKeyPoint();
    }
  };

  const handleCopyToClipboard = () => {
    navigator.clipboard.writeText(generatedEmail)
      .then(() => {
        alert('Email copied to clipboard!');
      })
      .catch(err => {
        console.error('Failed to copy:', err);
      });
  };

  return (
    <div className="email-generator">
      <h2>Generate New Email</h2>
      
      {!userId && (
        <div className="warning-message">
          No user ID provided. Email generation may not work correctly.
        </div>
      )}
      
      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">Email generated successfully!</div>}
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="recipient">Recipient:</label>
          <input
            type="text"
            id="recipient"
            value={recipient}
            onChange={(e) => setRecipient(e.target.value)}
            placeholder="Enter recipient name or role"
            disabled={loading}
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="topic">Email Topic:</label>
          <input
            type="text"
            id="topic"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="What is this email about?"
            disabled={loading}
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="keyPoints">Key Points:</label>
          <div className="key-points-input">
            <input
              type="text"
              id="keyPoints"
              value={keyPoints}
              onChange={(e) => setKeyPoints(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Add a key point and press Enter"
              disabled={loading}
            />
            <button 
              type="button" 
              onClick={handleAddKeyPoint}
              disabled={!keyPoints.trim() || loading}
            >
              Add
            </button>
          </div>
          
          <div className="key-points-list">
            {keyPointsList.map((point, index) => (
              <div key={index} className="key-point">
                <span>{point}</span>
                <button 
                  type="button" 
                  onClick={() => handleRemoveKeyPoint(index)}
                  disabled={loading}
                >
                  ✕
                </button>
              </div>
            ))}
            
            {keyPointsList.length === 0 && (
              <p className="hint">Add key points that should be included in your email</p>
            )}
          </div>
        </div>
        
        <button 
          type="submit" 
          className="generate-btn"
          disabled={loading}
        >
          {loading ? 'Generating...' : 'Generate Email'}
        </button>
      </form>
      
      {generatedEmail && (
        <div className="generated-email">
          <h3>Generated Email</h3>
          <div className="email-content">
            <pre>{generatedEmail}</pre>
          </div>
          <button onClick={handleCopyToClipboard} className="copy-btn">
            Copy to Clipboard
          </button>
        </div>
      )}
      
      <style jsx>{`
        .email-generator {
          max-width: 800px;
          margin: 0 auto;
          padding: 20px;
          font-family: Arial, sans-serif;
        }
        
        .form-group {
          margin-bottom: 20px;
        }
        
        label {
          display: block;
          margin-bottom: 5px;
          font-weight: bold;
        }
        
        input[type="text"] {
          width: 100%;
          padding: 10px;
          border: 1px solid #ddd;
          border-radius: 4px;
        }
        
        .key-points-input {
          display: flex;
          gap: 10px;
        }
        
        .key-points-input input {
          flex-grow: 1;
        }
        
        .key-points-list {
          margin-top: 10px;
          min-height: 40px;
        }
        
        .key-point {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 12px;
          background-color: #f0f0f0;
          border-radius: 4px;
          margin-bottom: 5px;
        }
        
        .key-point button {
          background: none;
          border: none;
          color: #999;
          cursor: pointer;
          font-size: 16px;
        }
        
        .key-point button:hover {
          color: #ff0000;
        }
        
        .hint {
          color: #999;
          font-style: italic;
        }
        
        .generate-btn {
          padding: 10px 20px;
          background-color: #4CAF50;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 16px;
        }
        
        .generate-btn:disabled {
          background-color: #cccccc;
          cursor: not-allowed;
        }
        
        .error-message {
          padding: 10px;
          background-color: #ffebee;
          color: #c62828;
          border-radius: 4px;
          margin-bottom: 20px;
        }
        
        .success-message {
          padding: 10px;
          background-color: #e8f5e9;
          color: #2e7d32;
          border-radius: 4px;
          margin-bottom: 20px;
        }
        
        .warning-message {
          padding: 10px;
          background-color: #fff8e1;
          color: #ff8f00;
          border-radius: 4px;
          margin-bottom: 20px;
        }
        
        .generated-email {
          margin-top: 30px;
          border: 1px solid #ddd;
          border-radius: 4px;
          padding: 20px;
        }
        
        .email-content {
          background-color: #f9f9f9;
          padding: 15px;
          border-radius: 4px;
          margin-bottom: 15px;
          white-space: pre-wrap;
          font-family: 'Courier New', monospace;
        }
        
        .copy-btn {
          padding: 8px 15px;
          background-color: #2196F3;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
        }
      `}</style>
    </div>
  );
};

export default EmailGenerator;