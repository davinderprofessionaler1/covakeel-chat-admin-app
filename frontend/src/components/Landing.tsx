
import React from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import LegalIcon from './LegalIcon';
import { useNavigate } from 'react-router-dom';
import { Link } from 'react-router-dom';

const Landing = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: 'justice' as const,
      title: 'Constitutional Law',
      description: 'Expert guidance on fundamental rights, directive principles, and constitutional amendments'
    },
    {
      icon: 'gavel' as const,
      title: 'Criminal Law (IPC)',
      description: 'Comprehensive coverage of Indian Penal Code sections and criminal procedures'
    },
    {
      icon: 'document' as const,
      title: 'Civil & Commercial Law',
      description: 'Contract law, property rights, company law, and commercial regulations'
    },
    {
      icon: 'scales' as const,
      title: 'Tax & Financial Law',
      description: 'Income tax, GST, customs, and financial regulatory compliance'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-background via-background to-card">
      {/* Header */}
      <header className="p-6 flex justify-between items-center">
        <div className="flex items-center space-x-3">
          <LegalIcon type="justice" className="w-8 h-8 text-primary" />
          <Link to="/" className="text-base md: text-2xl font-bold text-primary">IndiaLawAI</Link>
        </div>
        <div className="space-x-4">
          <Button className='text-sm md:text-lg' variant="ghost" onClick={() => navigate('/login')}>
            Login
          </Button>
          <Button className='text-sm md:text-lg' onClick={() => navigate('/register')}>
            Get Started
          </Button>
        </div>
      </header>

      {/* Hero Section */}
      <section className="px-6 py-20 text-center max-w-6xl mx-auto">
        <div className="animate-fade-in">
          <div className="mb-8 flex justify-center">
            <div className="relative">
              <LegalIcon type="parliament" className="w-32 h-32 text-primary opacity-20 absolute -top-4 -left-4" />
              <LegalIcon type="justice" className="w-24 h-24 text-primary" />
            </div>
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-primary via-primary to-yellow-300 bg-clip-text text-transparent">
            Your Legal Copilot for
            <br />
            Indian Laws & Acts
          </h1>
          
          <p className="text-xl md:text-2xl text-muted-foreground mb-8 max-w-3xl mx-auto leading-relaxed">
            Chat with an AI trained on every act and statute. Get instant, reliable legal information 
            and guidance — anytime, anywhere.
          </p>
          
          <div className="space-y-4 sm:space-y-0 sm:space-x-4 sm:flex sm:justify-center">
            <Button 
              size="lg" 
              className="text-lg md:text-xl px-8 py-4 animate-scale-in hover:scale-105 transition-transform"
              onClick={() => navigate('/register')}
            >
              Start Chatting Now
            </Button>
            <Button 
              size="lg" 
              variant="outline" 
              className="text-lg md:text-xl px-8 py-4"
              onClick={() => navigate('/login')}
            >
              Login to Continue
            </Button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="px-6 py-20 max-w-6xl mx-auto">
        <div className="text-center mb-16 animate-slide-up">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Covers All Indian Law Domains
          </h2>
          <p className="text-lg md:text-xl text-muted-foreground">
            From constitutional provisions to criminal statutes — comprehensive legal knowledge at your fingertips
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => (
            <Card 
              key={index} 
              className="group hover:scale-105 transition-all duration-300 hover:shadow-lg hover:shadow-primary/20 animate-fade-in border-border/50"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <CardContent className="p-6 text-center">
                <div className="mb-4 flex justify-center">
                  <LegalIcon 
                    type={feature.icon} 
                    className="w-12 h-12 text-primary group-hover:scale-110 transition-transform" 
                  />
                </div>
                <h3 className="text-lg md:text-xl font-semibold mb-2">{feature.title}</h3>
                <p className="text-base text-muted-foreground">{feature.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* AI Assistant Demo Section */}
      <section className="px-6 py-20 bg-card/30">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16 animate-slide-up">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              See Our AI Assistant in Action
            </h2>
            <p className="text-lg md:text-xl text-muted-foreground">
              Experience intelligent legal research with natural language queries
            </p>
          </div>

          <div className="max-w-4xl mx-auto">
            <Card className="bg-gradient-to-r from-primary/10 to-primary/5 border-primary/20">
              <CardContent className="p-8">
                <div className="flex items-center gap-4 mb-6">
                  <div className="bg-primary/20 p-3 rounded-lg">
                    <LegalIcon type="scales" className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="text-lg md:text-xl font-semibold text-primary">Legal AI Assistant</h3>
                    <p className="text-sm md:text-base text-muted-foreground">Powered by advanced AI technology</p>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="flex justify-end">
                    <div className="bg-primary text-primary-foreground px-4 py-3 rounded-2xl rounded-tr-sm max-w-md">
                      <p className="text-sm md:text-base">What are the key provisions of the Right to Information Act?</p>
                    </div>
                  </div>

                  <div className="flex justify-start">
                    <div className="bg-muted px-4 py-2 md:ml-0 rounded-2xl rounded-tl-sm max-w-2xl">
                      <p className="md:text-base text-sm mb-2">The Right to Information Act, 2005 has several key provisions:</p>
                      <ul className="md:text-base text-sm space-y-1 ml-4">
                        <li>• Citizens can request information from public authorities</li>
                        <li>• 30-day response time for most requests</li>
                        <li>• Information must be provided in the language requested</li>
                        <li>• Establishment of Information Commissions</li>
                      </ul>
                    </div>
                  </div>

                  <div className="flex justify-end">
                    <div className="bg-primary text-primary-foreground px-4 py-3 rounded-2xl rounded-tr-sm max-w-md">
                      <p className="text-sm md:text-base">What are the penalties for non-compliance?</p>
                    </div>
                  </div>
                </div>

                <div className="mt-6 p-4 bg-background/50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
                    <p className="text-sm md:text-base text-muted-foreground italic">AI is typing...</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="px-6 py-20 text-center">
        <div className="max-w-4xl mx-auto animate-slide-up">
          <div className="mb-6">
            <LegalIcon type="scales" className="w-16 h-16 text-primary mx-auto mb-4" />
          </div>
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Ready to Navigate Indian Law with AI?
          </h2>
          <p className="text-lg md:text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Join thousands of legal professionals, students, and citizens who trust IndiaLawAI 
            for accurate legal information and guidance.
          </p>
          <Button 
            size="lg" 
            className="text-lg md:text-xl px-12 py-4 hover:scale-105 transition-transform"
            onClick={() => navigate('/register')}
          >
            Begin Your Legal Journey
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 py-12 border-t border-border/50 bg-card/20 h-[500px]">
        <div className="max-w-6xl mx-auto mt-10">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            {/* Brand Section */}
            <div className="md:col-span-2">
              <div className="flex items-center space-x-3 mb-4">
                <div className="bg-primary/20 p-2 rounded-lg">
                  <LegalIcon type="justice" className="w-6 h-10 text-primary" />
                </div>
                <div>
                  <h3 className="text-xl md:text-4xl font-bold text-primary">IndiaLawAI</h3>
                  <p className="text-base md:text-lg text-muted-foreground">Indian Law Assistant</p>
                </div>
              </div>
              <p className="text-muted-foreground mb-4 max-w-md text-lg md:text-lg">
                Your intelligent companion for navigating the complex landscape of Indian legal acts and regulations. 
                Get instant, accurate answers powered by advanced AI technology.
              </p>
            </div>

            {/* Legal Links */}
            <div>
              <h4 className="font-semibold mb-4 text-foreground text-xl md:text-3xl">Legal</h4>
              <div className="space-y-2">
                <a href="/privacy" className="block text-base md:text-lg text-muted-foreground hover:text-primary transition-colors">Privacy Policy</a>
                <a href="/terms" className="block text-base md:text-lg text-muted-foreground hover:text-primary transition-colors">Terms of Service</a>
              </div>
            </div>

            {/* Support Links */}
            <div>
              <h4 className="font-semibold mb-4 text-foreground text-xl md:text-3xl">Support</h4>
              <div className="space-y-2">
                <a href="/contact" className="block text-base md:text-lg text-muted-foreground hover:text-primary transition-colors">Contact Us</a>
                <a href="/help" className="block text-base md:text-lg text-muted-foreground hover:text-primary transition-colors">FAQ</a>
                <a href="#" className="block text-base md:text-lg text-muted-foreground hover:text-primary transition-colors">Feedback</a>
              </div>
            </div>
          </div>

          {/* Bottom Footer */}
          <div className="flex flex-col md:flex-row justify-between pt-8 border-t border-border/50">
            <p className="text-base md:text-base text-muted-foreground mb-4 md:mb-0 max-w-[600px]">
              © 2024 IndiaLawAI. All rights reserved. This service provides general legal information and should not be considered as legal advice.
            </p>
            <p className="text-base text-muted-foreground mb-10 ">
              Made with <span className="text-red-500">♥</span> for Indian Legal Community
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
