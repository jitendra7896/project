import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { format } from 'date-fns';

const ChatHistory = () => {
  const [chats, setChats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchChatHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('/api/chat/history', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      setChats(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch chat history');
      console.error('Error fetching chat history:', err);
    } finally {
      setLoading(false);
    }
  };

  const deleteChatHistory = async () => {
    if (!window.confirm('Are you sure you want to delete all chat history? This action cannot be undone.')) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await axios.delete('/api/chat/history', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      setChats([]);
      setError(null);
    } catch (err) {
      setError('Failed to delete chat history');
      console.error('Error deleting chat history:', err);
    }
  };

  useEffect(() => {
    fetchChatHistory();
  }, []);

  if (loading) {
    return <div>Loading chat history...</div>;
  }

  return (
    <div className="chat-history">
      <div className="chat-history-header">
        <h2>Chat History</h2>
        <button 
          onClick={deleteChatHistory}
          className="delete-button"
          disabled={chats.length === 0}
        >
          Delete All History
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {chats.length === 0 ? (
        <div className="no-chats">No chat history available</div>
      ) : (
        <div className="chats-list">
          {chats.map((chat) => (
            <div key={chat.id} className="chat-item">
              <div className="chat-message">
                <strong>You:</strong> {chat.message}
              </div>
              <div className="chat-response">
                <strong>AI:</strong> {chat.response}
              </div>
              <div className="chat-meta">
                <span className="model">Model: {chat.model}</span>
                <span className="timestamp">
                  {format(new Date(chat.timestamp), 'PPpp')}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ChatHistory; 