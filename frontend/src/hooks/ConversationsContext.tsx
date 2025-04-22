import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useAuth } from './useAuth';

export interface Conversation {
  id: string;
  userId: string;
  title: string;
  createdAt: string;
  updatedAt: string;
}

export interface Message {
  id: string;
  conversationId: string;
  sender: string;
  text: string;
  createdAt: string;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

interface ConversationsContextType {
  conversations: Conversation[];
  loading: boolean;
  createConversation: (title?: string) => Promise<Conversation | null>;
  deleteConversation: (conversationId: string) => Promise<void>;
  fetchMessages: (conversationId: string) => Promise<Message[]>;
  sendMessage: (
    conversationId: string,
    text: string,
    onChunk: (chunk: string) => void
  ) => Promise<void>;
  refetch: () => Promise<void>;
}

const ConversationsContext = createContext<ConversationsContextType | undefined>(undefined);

export const ConversationsProvider = ({ children }: { children: ReactNode }) => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(false);
  const { token } = useAuth();

  const fetchConversations = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/conversations/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setConversations(data);
      }
    } catch (error) {
      console.error('Failed to fetch conversations:', error);
    } finally {
      setLoading(false);
    }
  };

  const createConversation = async (title?: string): Promise<Conversation | null> => {
    if (!token) return null;
    try {
      const response = await fetch(`${API_BASE_URL}/conversations/`, {
        method: 'POST',
        body: JSON.stringify({ title: title || 'New Chat' }),
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      if (response.ok) {
        const newConversation = await response.json();
        setConversations(prev => [newConversation, ...prev]);
        return newConversation;
      }
    } catch (error) {
      console.error('Failed to create conversation:', error);
    }
    return null;
  };

  const deleteConversation = async (conversationId: string) => {
    if (!token) return;
    try {
      const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      if (response.ok) {
        setConversations(prev => prev.filter(conv => conv.id !== conversationId));
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error);
    }
  };

  const fetchMessages = async (conversationId: string): Promise<Message[]> => {
    if (!token) return [];
    try {
      const response = await fetch(`${API_BASE_URL}/messages/by_conversation/${conversationId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      if (response.ok) {
        return await response.json();
      }
    } catch (error) {
      console.error('Failed to fetch messages:', error);
    }
    return [];
  };

  const sendMessage = async (
    conversationId: string,
    text: string,
    onChunk: (chunk: string) => void
  ): Promise<void> => {
    if (!token) return;
    try {
      const response = await fetch(`${API_BASE_URL}/chat/stream?conversationId=${conversationId}&text=${encodeURIComponent(text)}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      if (response.ok) {
        const reader = response.body?.getReader();
        if (reader) {
          const decoder = new TextDecoder();
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value);
            onChunk(chunk);
          }
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  useEffect(() => {
    fetchConversations();
  }, [token]);

  return (
    <ConversationsContext.Provider value={{
      conversations,
      loading,
      createConversation,
      deleteConversation,
      fetchMessages,
      sendMessage,
      refetch: fetchConversations,
    }}>
      {children}
    </ConversationsContext.Provider>
  );
};

export const useConversationsContext = () => {
  const context = useContext(ConversationsContext);
  if (!context) {
    throw new Error('useConversationsContext must be used within a ConversationsProvider');
  }
  return context;
}; 