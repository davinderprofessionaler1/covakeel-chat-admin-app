import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "@/hooks/useAuth";
import Index from "./pages/Index";
import Login from "./components/Login";
import Register from "./components/Register";
import Chat from "./components/Chat";
import Profile from "./components/Profile";
import Help from "./pages/Help";
import Privacy from "./pages/Privacy";
import Terms from "./pages/Terms";
import Contact from "./pages/Contact";
import NotFound from "./pages/NotFound";
import PrivacyOverlay from './pages/Privacy';
import TermsOverlay from './pages/Terms';
import { ConversationsProvider } from './hooks/ConversationsContext';

const queryClient = new QueryClient();

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
};

const PublicRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useAuth();
  return !isAuthenticated ? <>{children}</> : <Navigate to="/chat/new" replace />;
};

const AppRoutes = () => {
  return (
    <Routes>
      <Route path="/" element={<Index />} />
      <Route path="/login" element={<PublicRoute><Login /></PublicRoute>}>
        <Route path="privacy" element={<PrivacyOverlay />} />
        <Route path="terms" element={<TermsOverlay />} />
      </Route>
      <Route path="/register" element={<PublicRoute><Register /></PublicRoute>}>
        <Route path="privacy" element={<PrivacyOverlay />} />
        <Route path="terms" element={<TermsOverlay />} />
      </Route>
      <Route path="/chat/new" element={<ProtectedRoute><Chat /></ProtectedRoute>} />
      <Route path="/chat/:conversationId" element={<ProtectedRoute><Chat /></ProtectedRoute>} />
      <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
      <Route path="/help" element={<Help />} />
      <Route path="/contact" element={<Contact />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
};

const App = () => (
  <AuthProvider>
    <ConversationsProvider>
      <QueryClientProvider client={queryClient}>
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <BrowserRouter>
            <AppRoutes />
          </BrowserRouter>
        </TooltipProvider>
      </QueryClientProvider>
    </ConversationsProvider>
  </AuthProvider>
);

export default App;
