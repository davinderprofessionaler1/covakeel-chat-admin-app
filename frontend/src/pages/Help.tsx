
import React from 'react';
import { ArrowLeft, HelpCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { useNavigate } from 'react-router-dom';

const Help = () => {
  const navigate = useNavigate();

  const faqs = [
    {
      question: "What is IndiaLawAI?",
      answer: "IndiaLawAI is an AI-powered legal assistant that helps you understand Indian laws, acts, and legal procedures. It provides instant access to legal information from various domains including IPC, Constitution, Tax Laws, and more."
    },
    {
      question: "How accurate is the legal information provided?",
      answer: "Our AI is trained on comprehensive legal databases and official sources. However, the information provided is for educational purposes only and should not replace professional legal advice. Always consult with a qualified lawyer for specific legal matters."
    },
    {
      question: "Is my conversation data secure?",
      answer: "Yes, we take data security seriously. All conversations are encrypted and stored securely. We do not share your personal information or conversation data with third parties."
    },
    {
      question: "Can I delete my conversations?",
      answer: "Yes, you can delete individual messages or entire conversations at any time. Simply use the delete options available in the chat interface."
    },
    {
      question: "What types of legal queries can I ask?",
      answer: "You can ask about any aspect of Indian law including criminal law, civil law, constitutional law, corporate law, tax law, property law, family law, and more. The AI can help explain legal concepts, procedures, and relevant acts."
    },
    {
      question: "How do I create a new conversation?",
      answer: "Click the 'New Chat' button in the sidebar to start a fresh conversation. Each conversation maintains its own context and history."
    },
    {
      question: "Can I search through my previous conversations?",
      answer: "Yes, use the search bar in the sidebar to find specific conversations or topics you've discussed before."
    },
    {
      question: "Is there a limit to how many questions I can ask?",
      answer: "There are no limits on the number of questions you can ask. Feel free to explore and learn about Indian laws at your own pace."
    }
  ];

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="mb-6">
          <Button
            variant="ghost"
            onClick={() => navigate(-1)}
            className="mb-4 gap-2"
          >
            <ArrowLeft size={16} />
            Back
          </Button>
          
          <div className="flex items-center gap-3 mb-2">
            <div className="bg-primary/20 p-2 rounded-lg">
              <HelpCircle className="w-6 h-6 text-primary" />
            </div>
            <h1 className="text-3xl font-bold">Help & FAQ</h1>
          </div>
          <p className="text-muted-foreground">
            Find answers to commonly asked questions about IndiaLawAI
          </p>
        </div>

        <div className="space-y-4">
          {faqs.map((faq, index) => (
            <Card key={index} className="bg-card">
              <CardHeader>
                <CardTitle className="text-lg text-foreground">{faq.question}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground leading-relaxed">{faq.answer}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <Separator className="my-8" />

        <Card className="bg-card">
          <CardHeader>
            <CardTitle>Still Need Help?</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-muted-foreground">
              If you couldn't find the answer to your question, don't hesitate to reach out to our support team.
            </p>
            <Button
              onClick={() => navigate('/contact')}
              className="bg-primary hover:bg-primary/90 text-primary-foreground"
            >
              Contact Support
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Help;
