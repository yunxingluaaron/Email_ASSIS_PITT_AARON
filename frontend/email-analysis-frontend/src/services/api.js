import axios from 'axios';
import { API_BASE_URL } from '../config';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const submitEmails = async (userId, emailPairs) => {
  try {
    const response = await apiClient.post('/api/submit-emails', {
      userId,
      emailPairs
    });
    return response.data;
  } catch (error) {
    console.error('Error submitting emails:', error);
    throw error;
  }
};

export const submitEmailFeedback = async (userId, emailId, isApproved, rating, comments) => {
  try {
    const response = await apiClient.post('/api/email-feedback', {
      userId,
      emailId,
      isApproved,
      rating,
      comments
    });
    return response.data;
  } catch (error) {
    console.error('Error submitting feedback:', error);
    throw error;
  }
};

export const generateEmail = async (userId, recipient, topic, keyPoints) => {
  try {
    const response = await apiClient.post('/api/generate-email', {
      userId,
      recipient,
      topic,
      keyPoints
    });
    return response.data;
  } catch (error) {
    console.error('Error generating email:', error);
    throw error;
  }
};

export const getUserData = async (userId) => {
  try {
    const response = await apiClient.get(`/api/user-data?userId=${userId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching user data:', error);
    throw error;
  }
};