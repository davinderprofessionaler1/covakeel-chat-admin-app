import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from '@/hooks/useAuth';
import { useNavigate, Link, Outlet } from 'react-router-dom';
import { useToast } from '@/hooks/use-toast';
import LegalIcon from './LegalIcon';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) {
      toast({
        title: "Missing Information",
        description: "Please fill in all fields",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    try {
      await login(username, password);
      toast({
        title: "Welcome back!",
        description: "You've been successfully logged in.",
      });
      navigate('/chat/new');
    } catch (error) {
      toast({
        title: "Login Failed",
        description: "Invalid username or password. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-background to-card/50 p-6">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8 animate-fade-in">
          <Link to="/" className="inline-flex items-center space-x-3 mb-4">
            <LegalIcon type="justice" className="w-8 h-8 text-primary" />
            <span className="text-2xl font-bold text-primary">IndiaLawAI</span>
          </Link>
          <h1 className="text-3xl md:text-5xl font-bold mb-2">Welcome Back</h1>
          <p className="text-muted-foreground text-lg">Sign in to continue your legal consultations</p>
        </div>

        <Card className="animate-scale-in border-border/50 shadow-xl">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl md:text-3xl font-bold text-center ">Sign In</CardTitle>
            <CardDescription className="text-center text-base md:text-lg">
              Enter your credentials to access your account
            </CardDescription>
          </CardHeader>
          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label className='text-md' htmlFor="username">Username</Label>
                <Input
                  id="username"
                  type="text"
                  placeholder="Enter your username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  disabled={isLoading}
                  className="transition-all duration-200 focus:ring-2 focus:ring-primary/20 text-base md:text-lg"
                />
              </div>
              <div className="space-y-2">
                <Label className='text-md' htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={isLoading}                    
                  className="transition-all duration-200 focus:ring-2 focus:ring-primary/20 text-base md:text-lg"
                />
              </div>
            </CardContent>
            <CardFooter className="flex flex-col space-y-4">
              <Button 
                type="submit" 
                className="w-full hover:scale-105 transition-transform text-base md:text-lg" 
                disabled={isLoading}
              >
                {isLoading ? (
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                    <span>Signing In...</span>
                  </div>
                ) : (
                  'Sign In'
                )}
              </Button>
              <div className="text-center text-base md:text-lg text-muted-foreground">
                Don't have an account?{' '}
                <Link to="/register" className="text-primary hover:underline font-medium">
                  Create one here
                </Link>
              </div>
            </CardFooter>
          </form>
        </Card>

        <div className="text-center mt-6 animate-slide-up">
          <p className="text-base md:text-base text-muted-foreground">
            By signing in, you agree to our <Link to="terms" className="underline text-yellow-600">legal terms</Link> and <Link to="privacy" className="underline text-yellow-600">privacy policy</Link>
          </p>
        </div>
      </div>
      <Outlet />
    </div>
  );
};

export default Login;
