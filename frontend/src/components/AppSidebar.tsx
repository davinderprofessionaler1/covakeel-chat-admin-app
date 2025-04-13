import React, { useState } from 'react';
import { Plus, Search, Settings, HelpCircle, Shield, FileText, Mail, LogOut, User, MoreVertical, Trash2, Pencil } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useAuth } from '@/hooks/useAuth';
import { useConversations } from '@/hooks/useConversations';
import { useNavigate, useLocation } from 'react-router-dom';
import LegalIcon from './LegalIcon';
import { formatDistanceToNow } from 'date-fns';
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '@/components/ui/dropdown-menu';

const AppSidebar = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState('');
  const { user, logout } = useAuth();
  const { conversations, deleteConversation } = useConversations();
  const navigate = useNavigate();
  const location = useLocation();

  // Extract active conversation id from the URL
  const match = location.pathname.match(/\/chat\/(.+)/);
  const activeConversationId = match ? match[1] : null;

  const handleNewChat = () => {
    navigate('/chat/new');
  };

  const handleRename = (convId: string, currentTitle: string) => {
    setRenamingId(convId);
    setRenameValue(currentTitle);
  };

  const handleRenameSubmit = (convId: string) => {
    // For now, update locally (no backend API for rename)
    // If backend needed, add API call here
    const idx = conversations.findIndex(c => c.id === convId);
    if (idx !== -1 && renameValue.trim()) {
      conversations[idx].title = renameValue.trim();
    }
    setRenamingId(null);
    setRenameValue('');
  };

  const handleDelete = async (convId: string) => {
    await deleteConversation(convId);
    if (activeConversationId === convId) {
      navigate('/chat/new');
    }
  };

  const filteredConversations = conversations.filter(conv =>
    conv.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const groupedConversations = filteredConversations.reduce((groups, conv) => {
    const date = new Date(conv.createdAt);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    let group = 'Older';
    if (date.toDateString() === today.toDateString()) {
      group = 'Today';
    } else if (date.toDateString() === yesterday.toDateString()) {
      group = 'Yesterday';
    }

    if (!groups[group]) groups[group] = [];
    groups[group].push(conv);
    return groups;
  }, {} as Record<string, typeof conversations>);

  return (
    <>
      <div className="w-64 bg-sidebar h-screen flex flex-col border-r border-sidebar-border">
        {/* Header */}
        <div className="p-4">
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-primary/20 p-2 rounded-lg">
              <LegalIcon type="justice" className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h2 className="font-semibold text-sidebar-foreground">Legal AI</h2>
            </div>
          </div>

          <Button 
            onClick={handleNewChat}
            className="w-full bg-sidebar-accent hover:bg-sidebar-accent/80 text-sidebar-accent-foreground justify-start gap-2"
          >
            <Plus size={16} />
            New Chat
          </Button>
        </div>

        {/* Search */}
        <div className="px-4 mb-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-sidebar-foreground/50" />
            <Input
              placeholder="Search anything..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 bg-sidebar-accent/50 border-sidebar-border text-sidebar-foreground placeholder:text-sidebar-foreground/50"
            />
          </div>
        </div>

        {/* Conversations */}
        <div className="flex-1 overflow-y-auto px-4">
          {Object.entries(groupedConversations).map(([group, convs]) => (
            <div key={group} className="mb-4">
              <h3 className="text-xs font-medium text-sidebar-foreground/70 mb-2 px-2">{group}</h3>
              <div className="space-y-1">
                {convs.map((conv) => {
                  const isActive = activeConversationId === conv.id;
                  return (
                    <div
                      key={conv.id}
                      className={`group flex items-center justify-between p-2 rounded-lg cursor-pointer transition-colors
                        ${isActive ? 'bg-sidebar-accent/80 text-primary font-semibold' : 'hover:bg-sidebar-accent'}
                      `}
                    >
                      <div
                        className="flex-1 min-w-0"
                        onClick={() => navigate(`/chat/${conv.id}`)}
                      >
                        {renamingId === conv.id ? (
                          <form
                            onSubmit={e => {
                              e.preventDefault();
                              handleRenameSubmit(conv.id);
                            }}
                          >
                            <input
                              autoFocus
                              className="text-sm text-sidebar-foreground bg-sidebar-accent rounded px-1 py-0.5 w-full outline-none border border-sidebar-border"
                              value={renameValue}
                              onChange={e => setRenameValue(e.target.value)}
                              onBlur={() => handleRenameSubmit(conv.id)}
                              maxLength={50}
                            />
                          </form>
                        ) : (
                          <>
                            <p className={`text-sm truncate ${isActive ? 'text-primary' : 'text-sidebar-foreground'}`}>{conv.title || 'Untitled'}</p>
                            <p className={`text-xs ${isActive ? 'text-primary/70' : 'text-sidebar-foreground/50'}`}>
                              {formatDistanceToNow(new Date(conv.createdAt), { addSuffix: true })}
                            </p>
                          </>
                        )}
                      </div>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <button
                            className="ml-2 p-1 rounded hover:bg-sidebar-accent/60 text-sidebar-foreground/60 hover:text-sidebar-foreground"
                            onClick={e => e.stopPropagation()}
                            aria-label="More options"
                          >
                            <MoreVertical size={18} />
                          </button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent className='bg-sidebar-accent' align="end" onClick={e => e.stopPropagation()}>
                          <DropdownMenuItem
                            className="hover:cursor-pointer"
                            onClick={() => handleRename(conv.id, conv.title)}
                          >
                            <Pencil className='h-4 w-4 mr-2'/> Rename
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            className="text-red-500 focus:bg-red-500/20 focus:text-red-500 hover:cursor-pointer"
                            onClick={() => handleDelete(conv.id)}
                          >
                            <Trash2 className='h-4 w-4 mr-2'/> Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}

          {conversations.length === 0 && (
            <div className="text-center py-8">
              <LegalIcon type="document" className="w-12 h-12 text-sidebar-foreground/30 mx-auto mb-2" />
              <p className="text-sm text-sidebar-foreground/50">No conversations yet</p>
            </div>
          )}
        </div>

        {/* Settings Button */}
        <div className="p-4 border-t border-sidebar-border">
          <Button
            onClick={() => setShowSettings(true)}
            variant="secondary"
            className="w-full justify-start gap-2 bg-background hover:bg-sidebar-accent/50 text-sidebar-accent-foreground "
          >
            <Settings size={16} />
            Settings
          </Button>
        </div>
      </div>

      {/* Settings Dialog */}
      <Dialog open={showSettings} onOpenChange={setShowSettings}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Settings</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">Manage your account and preferences</p>
            
            {/* User Profile */}
            <div className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg">
              <Avatar>
                <AvatarFallback className="bg-primary text-primary-foreground">
                  {user?.username?.[0]?.toUpperCase() || 'U'}
                </AvatarFallback>
              </Avatar>
              <div>
                <p className="font-medium">{user?.username || 'User'}</p>
                <p className="text-sm text-muted-foreground">{user?.email || 'user@example.com'}</p>
              </div>
            </div>

            <Separator />

            {/* Settings Menu */}
            <div className="space-y-3">
              <Button
                variant="ghost"
                className="w-full justify-start gap-3 h-auto p-3"
                onClick={() => {
                  setShowSettings(false);
                  navigate('/profile');
                }}
              >
                <User size={16} />
                <div className="text-left">
                  <p className="font-medium">Profile Settings</p>
                </div>
              </Button>

              <Button
                variant="ghost"
                className="w-full justify-start gap-3 h-auto p-3"
                onClick={() => {
                  setShowSettings(false);
                  navigate('/help');
                }}
              >
                <HelpCircle size={16} />
                <div className="text-left">
                  <p className="font-medium">Help & FAQ</p>
                </div>
              </Button>

              <Button
                variant="ghost"
                className="w-full justify-start gap-3 h-auto p-3"
                onClick={() => {
                  setShowSettings(false);
                  navigate('/privacy');
                }}
              >
                <Shield size={16} />
                <div className="text-left">
                  <p className="font-medium">Privacy Policy</p>
                </div>
              </Button>

              <Button
                variant="ghost"
                className="w-full justify-start gap-3 h-auto p-3"
                onClick={() => {
                  setShowSettings(false);
                  navigate('/terms');
                }}
              >
                <FileText size={16} />
                <div className="text-left">
                  <p className="font-medium">Terms of Service</p>
                </div>
              </Button>

              <Button
                variant="ghost"
                className="w-full justify-start gap-3 h-auto p-3"
                onClick={() => {
                  setShowSettings(false);
                  navigate('/contact');
                }}
              >
                <Mail size={16} />
                <div className="text-left">
                  <p className="font-medium">Contact Support</p>
                </div>
              </Button>

              <Separator />

              <Button
                variant="ghost"
                className="w-full justify-start gap-3 h-auto p-3 text-red-400 hover:text-red-400 hover:bg-destructive/10"
                onClick={() => {
                  setShowSettings(false);
                  logout();
                }}
              >
                <LogOut size={16} />
                <div className="text-left">
                  <p className="font-medium">Logout</p>
                </div>
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default AppSidebar;
