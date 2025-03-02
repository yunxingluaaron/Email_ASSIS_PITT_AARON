-- Create users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create email_pairs table to store original user email Q&A
CREATE TABLE email_pairs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create style_analysis table to store OpenAI analysis results
CREATE TABLE style_analysis (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    analysis_json JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create synthetic_emails table to store generated email samples
CREATE TABLE synthetic_emails (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    category VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    approved BOOLEAN DEFAULT FALSE,
    rating INTEGER,
    feedback TEXT,
    original_email_id INTEGER REFERENCES synthetic_emails(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create generated_emails table to store final user-requested emails
CREATE TABLE generated_emails (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    recipient VARCHAR(255) NOT NULL,
    topic VARCHAR(255) NOT NULL,
    key_points JSONB NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indices for better query performance
CREATE INDEX idx_email_pairs_user_id ON email_pairs(user_id);
CREATE INDEX idx_style_analysis_user_id ON style_analysis(user_id);
CREATE INDEX idx_synthetic_emails_user_id ON synthetic_emails(user_id);
CREATE INDEX idx_synthetic_emails_category ON synthetic_emails(category);
CREATE INDEX idx_synthetic_emails_approved ON synthetic_emails(approved);
CREATE INDEX idx_generated_emails_user_id ON generated_emails(user_id);