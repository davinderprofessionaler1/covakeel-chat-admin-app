import React, { useState, useEffect, useRef } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useAuth } from '@/hooks/useAuth';
import { useConversations } from '@/hooks/useConversations';
import { Message } from '@/hooks/ConversationsContext';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { useToast } from '@/hooks/use-toast';
import LegalIcon from './LegalIcon';
import AppSidebar from './AppSidebar';
import { ArrowUp, Menu, ChevronDown } from 'lucide-react';
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from '@/components/ui/dropdown-menu';

const Chat = () => {
  const { conversationId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  const { sendMessage, fetchMessages, createConversation } = useConversations();
  const { toast } = useToast();

  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [loadingMessages, setLoadingMessages] = useState(true);
  const [hasStartedConversation, setHasStartedConversation] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [justCreated, setJustCreated] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const isNewChat = location.pathname === '/chat/new';

  useEffect(() => {
    if (conversationId && !isNewChat) {
      if (justCreated) {
        setJustCreated(false);
        return;
      }
      loadMessages();
      setHasStartedConversation(true);
    } else if (isNewChat) {
      setMessages([]);
      setLoadingMessages(false);
      setHasStartedConversation(false);
    }
  }, [conversationId, isNewChat]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Focus the textarea on mount (page refresh)
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    // Focus the textarea when navigating to a different chat or new chat
    inputRef.current?.focus();
  }, [conversationId, isNewChat]);

  const loadMessages = async () => {
    if (!conversationId || isNewChat) return;

    setLoadingMessages(true);
    try {
      const messageHistory = await fetchMessages(conversationId);
      setMessages(messageHistory);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load conversation history",
        variant: "destructive",
      });
      navigate('/chat/new');
    } finally {
      setLoadingMessages(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setIsLoading(true);

    // Set conversation as started to trigger animation
    if (!hasStartedConversation) {
      setHasStartedConversation(true);
    }

    let currentConversationId = conversationId;

    // If this is a new chat, create a conversation first
    if (isNewChat) {
      try {
        // Use first 50 characters of the message as title
        const conversationTitle = userMessage.length > 50
          ? userMessage.substring(0, 50) + '...'
          : userMessage;

        const newConversation = await createConversation(conversationTitle);
        if (newConversation) {
          currentConversationId = newConversation.id;
          setJustCreated(true);
          // Navigate to the new conversation URL
          navigate(`/chat/${newConversation.id}`, { replace: true });
        } else {
          toast({
            title: "Error",
            description: "Failed to create conversation. Please try again.",
            variant: "destructive",
          });
          setIsLoading(false);
          return;
        }
      } catch (error) {
        toast({
          title: "Error",
          description: "Failed to create conversation. Please try again.",
          variant: "destructive",
        });
        setIsLoading(false);
        return;
      }
    }

    if (!currentConversationId) {
      setIsLoading(false);
      return;
    }

    const tempUserMessage: Message = {
      id: `temp-${Date.now()}`,
      conversationId: currentConversationId,
      sender: 'user',
      text: userMessage,
      createdAt: new Date().toISOString(),
    };
    setMessages(prev => [...prev, tempUserMessage]);

    // Initialize empty bot message in UI
    const botMessageId = `bot-${Date.now()}`;
    const botMessage: Message = {
      id: botMessageId,
      conversationId: currentConversationId,
      sender: 'assistant',
      text: '',
      createdAt: new Date().toISOString(),
    };

    setMessages(prev => [...prev, botMessage]);

    try {
      await sendMessage(currentConversationId, userMessage, (chunk: string) => {
        // Update bot message with each streamed chunk
        setMessages(prev =>
          prev.map(msg => {
            return msg.id === botMessageId
              ? { ...msg, text: msg.text + chunk }
              : msg
          })
        );
        setIsLoading(false);
      });
      // Focus the textarea after assistant response is received
      inputRef.current?.focus();
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to send message. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
      // Also focus in finally in case of error
      inputRef.current?.focus();
    }
  };

  const quickActions = [
    "What are the key provisions of the IC?",
    "Explain the Right to Information Act",
    "What is the Consumer Protection Act?",
    "Tell me about the Motor Vehicle Act penalties"
  ];

  const shouldShowWelcome = (isNewChat || (!conversationId && !isNewChat)) && !hasStartedConversation;

  return (
    <div className="h-screen bg-background flex overflow-hidden">
      {/* Sidebar for desktop, drawer for mobile */}
      <div className="hidden md:block h-full">
        <AppSidebar />
      </div>
      {/* Mobile sidebar drawer */}
      <div className={`fixed inset-0 z-50 md:hidden transition-transform duration-300 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}
        style={{ background: sidebarOpen ? 'rgba(0,0,0,0.5)' : 'transparent' }}
        onClick={() => setSidebarOpen(false)}
      >
        <div className="w-64 h-full bg-sidebar shadow-lg" onClick={e => e.stopPropagation()}>
          <AppSidebar />
        </div>
      </div>
      {/* Hamburger menu button for mobile */}
      <button
        className="md:hidden fixed top-4 left-4 z-40 bg-sidebar-accent p-2 rounded-lg shadow-lg text-sidebar-foreground focus:outline-none"
        onClick={() => setSidebarOpen(true)}
        aria-label="Open sidebar"
      >
        <Menu size={24} />
      </button>
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0 md:ml-0">
        {/* Chat Section Header */}
        {!shouldShowWelcome && <div className="sticky top-3 mx-12 md:mx-0 z-20 bg-background/95 backdrop-blur-sm flex items-center justify-between px-4 py-3">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="flex items-center gap-2 text-base font-medium text-foreground focus:outline-none">
                Untitled Chat
                <ChevronDown className="w-4 h-4 ml-1" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className='bg-sidebar-accent' align="end">
              <DropdownMenuItem>Rename</DropdownMenuItem>
              <DropdownMenuItem className="text-red-500 focus:bg-red-500/20 focus:text-red-500 hover:cursor-pointer">Delete</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>}
        {/* Welcome Screen - Only show when new chat */}
        {shouldShowWelcome && (
          <div className="flex-1 flex flex-col items-center justify-center px-2 py-4 sm:px-6 sm:py-8">
            <div className="w-full max-w-full sm:max-w-4xl mx-auto">
              <div className="text-center mb-8 sm:mb-12">
                <div className="mb-4 sm:mb-6">
                  <LegalIcon type="scales" className="w-12 h-12 sm:w-16 sm:h-16 text-primary mx-auto mb-4" />
                </div>
                <h2 className="text-2xl sm:text-3xl font-bold mb-2 sm:mb-4 bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
                  Hello {user?.username || 'User'}!
                </h2>
                <p className="text-muted-foreground text-base sm:text-lg">How can I help you with your legal questions today?</p>
              </div>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 sm:gap-4 max-w-full sm:max-w-3xl mx-auto mb-6 sm:mb-8">
                {quickActions.map((action, index) => (
                  <Button
                    key={index}
                    variant="outline"
                    className="p-4 sm:p-6 h-auto text-left justify-start hover:bg-primary/5 hover:border-primary/30 transition-all duration-200 group text-sm sm:text-base"
                    onClick={() => setInputMessage(action)}
                  >
                    <div className="group-hover:text-primary transition-colors">{action}</div>
                  </Button>
                ))}
              </div>
            </div>
          </div>
        )}
        {/* Messages Container - Only show when conversation started */}
        {hasStartedConversation && (
          <div
            ref={messagesContainerRef}
            className="flex-1 overflow-y-auto px-2 py-4 sm:px-4 sm:py-6 scroll-smooth"
          >
            {loadingMessages ? (
              <div className="w-full max-w-full sm:max-w-4xl mx-auto space-y-4 sm:space-y-6">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="animate-pulse flex space-x-3 sm:space-x-4">
                    <div className="w-8 h-8 bg-muted rounded-full flex-shrink-0"></div>
                    <div className="flex-1 space-y-2">
                      <div className="h-4 bg-muted rounded w-3/4"></div>
                      <div className="h-4 bg-muted rounded w-1/2"></div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="w-full max-w-full sm:max-w-4xl mx-auto space-y-4 sm:space-y-6">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`${message.text.length < 1 && "hidden"} flex gap-2 sm:gap-4 animate-in fade-in-0 slide-in-from-bottom-3 duration-300 ${message.sender === 'user' ? 'flex-row-reverse' : ''}`}
                  >
                    <Avatar className="flex-shrink-0 w-8 h-8">
                      <AvatarFallback className={`text-xs ${message.sender === 'user'
                        ? 'bg-primary text-primary-foreground text-xl'
                        : 'bg-muted'
                        }`}>
                        {message.sender === 'user'
                          ? user?.username?.[0]?.toUpperCase() || 'U'
                          : <LegalIcon type="justice" className="w-4 h-4" />
                        }
                      </AvatarFallback>
                    </Avatar>
                    <div className={`flex-1 max-w-[90%] sm:max-w-[80%] ${message.sender === 'user' ? 'text-right' : ''}`}>
                      <div className={`inline-block p-3 sm:p-4 rounded-2xl ${message.sender === 'user'
                        ? 'bg-primary text-primary-foreground rounded-br-md'
                        : 'bg-muted rounded-bl-md'
                        }`}>
                        <p className="whitespace-pre-wrap text-sm md:text-lgg= leading-relaxed break-words">{message.text}</p>
                      </div>
                    </div>
                  </div>
                ))}
                {/* Typing indicator */}
                {isLoading && (
                  <div className="flex gap-2 sm:gap-4 animate-in fade-in-0 slide-in-from-bottom-3 duration-300">
                    <Avatar className="flex-shrink-0 w-8 h-8">
                      <AvatarFallback className="bg-muted text-xs">
                        <LegalIcon type="justice" className="w-4 h-4" />
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1 max-w-[90%] sm:max-w-[80%]">
                      <div className="inline-block p-3 sm:p-4 rounded-2xl bg-muted rounded-bl-md">
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-muted-foreground/40 rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-muted-foreground/40 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                          <div className="w-2 h-2 bg-muted-foreground/40 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
        )}
        {/* Input Area */}
        <div
          className={`bg-background/95 backdrop-blur-sm p-2 sm:p-4 transition-all duration-500 ease-in-out`}
        >
          <form onSubmit={handleSendMessage} className="w-full max-w-full sm:max-w-4xl mx-auto">
            <div className="relative">
              <textarea
                ref={inputRef}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="Ask me anything about Indian law..."
                rows={1}
                className="w-full max-h-60 min-h-[3rem] py-3 sm:py-4 px-4 sm:px-6 pr-12 sm:pr-16 rounded-2xl border-2 border-border/50 transition-all duration-200 resize-none text-base overflow-y-auto bg-background text-foreground"
                disabled={isLoading}
                style={{ scrollbarColor: 'gray transparent' }}
                onInput={(e) => {
                  e.currentTarget.style.height = 'auto';
                  e.currentTarget.style.height = `${e.currentTarget.scrollHeight}px`;
                  if (e.currentTarget.scrollHeight > 240) {
                    e.currentTarget.style.scrollbarWidth = 'thin';
                  } else {
                    e.currentTarget.style.scrollbarWidth = 'none';
                  }
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    if (!isLoading && inputMessage.trim()) {
                      (e.target as HTMLTextAreaElement).form?.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
                    }
                  }
                }}
              />
              <Button
                type="submit"
                disabled={isLoading || !inputMessage.trim()}
                size="sm"
                className="absolute right-3 sm:right-5 bottom-3 sm:bottom-4 h-10 w-10 rounded-xl hover:scale-105 transition-transform duration-200"
              >
                {isLoading ? (
                  <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                ) : (
                  <ArrowUp className='h-5 w-5' />
                )}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground mt-2 sm:mt-3 text-center leading-relaxed">
              IndiaLawAI provides legal information for educational purposes only. Always consult a qualified lawyer for specific legal advice.
            </p>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Chat;
