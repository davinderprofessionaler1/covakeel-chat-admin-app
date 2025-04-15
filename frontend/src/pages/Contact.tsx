
import React, { useState } from 'react';
import { ArrowLeft, Mail, Send } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useNavigate } from 'react-router-dom';
import { useToast } from '@/components/ui/use-toast';

const Contact = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    category: '',
    message: ''
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Simulate form submission
    toast({
      title: "Message Sent",
      description: "Thank you for contacting us. We'll get back to you within 24 hours.",
    });
    setFormData({
      name: '',
      email: '',
      subject: '',
      category: '',
      message: ''
    });
  };

  const handleChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="mb-6">
          <Button
            variant="ghost"
            onClick={() => navigate(-1)}
            className="mb-4 gap-2 "
          >
            <ArrowLeft size={16} />
            Back
          </Button>
          
          <div className="flex items-center gap-3 mb-2 mt-8">
            <div className="bg-primary/20 p-2 rounded-lg">
              <Mail className="w-6 h-6 md:w-10 md:h-10   text-primary" />
            </div>
            <h1 className="text-3xl md:text-5xl font-bold">Contact Support</h1>
          </div>
          <p className="text-base md:text-lg text-muted-foreground mt-4">
            Get in touch with our support team. We're here to help!
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <Card className="bg-card">
              <CardHeader>
                <CardTitle>Send us a message</CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="name" className='text-base md:text-lg'>Name *</Label>
                      <Input
                        id="name"
                        value={formData.name}
                        onChange={(e) => handleChange('name', e.target.value)}
                        placeholder="Your full name"
                        required
                        className="placeholder:text-sm md:placeholder:text-base"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="email" className='text-base md:text-lg'>Email *</Label>
                      <Input
                        id="email"
                        type="email"
                        value={formData.email}
                        onChange={(e) => handleChange('email', e.target.value)}
                        placeholder="your.email@example.com"
                        required
                        className="placeholder:text-sm md:placeholder:text-base"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="category" className='text-base md:text-lg'>Category</Label>
                    <Select value={formData.category} onValueChange={(value) => handleChange('category', value)}>
                      <SelectTrigger className="text-sm md:text-base">
                        <SelectValue placeholder="Select a category" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="technical" className="text-sm md:text-base">Technical Support</SelectItem>
                        <SelectItem value="account" className="text-sm md:text-base">Account Issues</SelectItem>
                        <SelectItem value="legal" className="text-sm md:text-base">Legal Information</SelectItem>
                        <SelectItem value="billing" className="text-sm md:text-base">Billing & Subscription</SelectItem>
                        <SelectItem value="feature" className="text-sm md:text-base">Feature Request</SelectItem>
                        <SelectItem value="other" className="text-sm md:text-base">Other</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="subject" className='text-base md:text-lg'>Subject *</Label>
                    <Input
                      id="subject"
                      value={formData.subject}
                      onChange={(e) => handleChange('subject', e.target.value)}
                      placeholder="Brief description of your inquiry"
                      required
                      className="placeholder:text-sm md:placeholder:text-base"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="message" className='text-base md:text-lg'>Message *</Label>
                    <Textarea
                      id="message"
                      value={formData.message}
                      onChange={(e) => handleChange('message', e.target.value)}
                      placeholder="Please describe your issue or question in detail..."
                      rows={6}
                      required
                      className="placeholder:text-sm md:placeholder:text-base"
                    />
                  </div>

                  <Button
                    type="submit"
                    className="w-full bg-primary hover:bg-primary/90 text-primary-foreground gap-2 text-lg"
                  >
                    <Send size={16} />
                    Send Message
                  </Button>
                </form>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card className="bg-card">
              <CardHeader>
                <CardTitle>Response Time</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">
                  We typically respond to all inquiries within 24 hours during business days.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-card">
              <CardHeader>
                <CardTitle>Before You Contact Us</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-muted-foreground text-sm">
                  Check out our Help & FAQ section - you might find your answer there!
                </p>
                <Button
                  variant="outline"
                  onClick={() => navigate('/help')}
                  className="w-full"
                >
                  View Help & FAQ
                </Button>
              </CardContent>
            </Card>

            <Card className="bg-card">
              <CardHeader>
                <CardTitle>Legal Disclaimer</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground text-sm">
                  Please note that our support team cannot provide legal advice. For specific legal matters, please consult with a qualified attorney.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Contact;
