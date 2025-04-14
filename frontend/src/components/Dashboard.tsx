
import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Chat from './Chat';

const Dashboard = () => {
  const navigate = useNavigate();

  // Redirect directly to chat interface
  useEffect(() => {
    // Show the chat interface directly without conversation ID
    // This will show the welcome screen with quick actions
  }, []);

  return <Chat />;
};

export default Dashboard;
