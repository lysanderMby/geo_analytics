import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { useCreateUser } from '../hooks/useApi';
import { useLocalStorage } from '../hooks/useLocalStorage';
import { storeApiKey } from '../lib/encryption';
import { OnboardingData, User } from '../types';

export default function OnboardingPage() {
  const navigate = useNavigate();
  const createUserMutation = useCreateUser();
  const [, setCurrentUser] = useLocalStorage<User | null>('current_user', null);
  
  const [step, setStep] = useState<'business' | 'api-keys'>('business');
  const [businessData, setBusinessData] = useState<OnboardingData>({
    email: '',
    business_name: '',
    website: '',
    sector: '',
    business_size: 'small',
    location: '',
    description: ''
  });

  const [apiKeys, setApiKeys] = useState({
    openai: '',
    anthropic: '',
    gemini: ''
  });

  const handleBusinessSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const response = await createUserMutation.mutateAsync(businessData);
      setCurrentUser(response.data);
      setStep('api-keys');
    } catch (error) {
      console.error('Failed to create user:', error);
      // Handle error (show toast, etc.)
    }
  };

  const handleApiKeysSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Store API keys securely
    Object.entries(apiKeys).forEach(([provider, key]) => {
      if (key.trim()) {
        storeApiKey(provider as 'openai' | 'anthropic' | 'gemini', key.trim());
      }
    });

    navigate('/dashboard');
  };

  const handleSkipApiKeys = () => {
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">Welcome to Geo Analytics</h1>
          <p className="mt-2 text-gray-600">
            Track your brand mentions in AI language model responses
          </p>
        </div>

        <Tabs value={step} className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="business" disabled={step !== 'business'}>
              Business Info
            </TabsTrigger>
            <TabsTrigger value="api-keys" disabled={step !== 'api-keys'}>
              API Keys
            </TabsTrigger>
          </TabsList>

          <TabsContent value="business">
            <Card>
              <CardHeader>
                <CardTitle>Business Information</CardTitle>
                <CardDescription>
                  Tell us about your business to get started
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleBusinessSubmit} className="space-y-4">
                  <div>
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      value={businessData.email}
                      onChange={(e) => setBusinessData({ ...businessData, email: e.target.value })}
                      required
                    />
                  </div>

                  <div>
                    <Label htmlFor="business_name">Business Name</Label>
                    <Input
                      id="business_name"
                      value={businessData.business_name}
                      onChange={(e) => setBusinessData({ ...businessData, business_name: e.target.value })}
                      required
                    />
                  </div>

                  <div>
                    <Label htmlFor="website">Website</Label>
                    <Input
                      id="website"
                      type="url"
                      placeholder="https://example.com"
                      value={businessData.website}
                      onChange={(e) => setBusinessData({ ...businessData, website: e.target.value })}
                      required
                    />
                  </div>

                  <div>
                    <Label htmlFor="sector">Sector/Industry</Label>
                    <Input
                      id="sector"
                      placeholder="e.g., Restaurant, Technology, Healthcare"
                      value={businessData.sector}
                      onChange={(e) => setBusinessData({ ...businessData, sector: e.target.value })}
                      required
                    />
                  </div>

                  <div>
                    <Label htmlFor="business_size">Business Size</Label>
                    <select
                      id="business_size"
                      value={businessData.business_size}
                      onChange={(e) => setBusinessData({ ...businessData, business_size: e.target.value as any })}
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
                    >
                      <option value="startup">Startup</option>
                      <option value="small">Small Business</option>
                      <option value="medium">Medium Business</option>
                      <option value="large">Large Business</option>
                      <option value="enterprise">Enterprise</option>
                    </select>
                  </div>

                  <div>
                    <Label htmlFor="location">Location</Label>
                    <Input
                      id="location"
                      placeholder="e.g., London, UK"
                      value={businessData.location}
                      onChange={(e) => setBusinessData({ ...businessData, location: e.target.value })}
                      required
                    />
                  </div>

                  <div>
                    <Label htmlFor="description">Description (Optional)</Label>
                    <textarea
                      id="description"
                      placeholder="Brief description of your business"
                      value={businessData.description}
                      onChange={(e) => setBusinessData({ ...businessData, description: e.target.value })}
                      className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
                    />
                  </div>

                  <Button
                    type="submit"
                    className="w-full"
                    disabled={createUserMutation.isLoading}
                  >
                    {createUserMutation.isLoading ? 'Creating Account...' : 'Continue'}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="api-keys">
            <Card>
              <CardHeader>
                <CardTitle>API Keys</CardTitle>
                <CardDescription>
                  Add your LLM API keys to start analyzing responses. You can add these later in settings.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleApiKeysSubmit} className="space-y-4">
                  <div>
                    <Label htmlFor="openai">OpenAI API Key (Optional)</Label>
                    <Input
                      id="openai"
                      type="password"
                      placeholder="sk-..."
                      value={apiKeys.openai}
                      onChange={(e) => setApiKeys({ ...apiKeys, openai: e.target.value })}
                    />
                  </div>

                  <div>
                    <Label htmlFor="anthropic">Anthropic API Key (Optional)</Label>
                    <Input
                      id="anthropic"
                      type="password"
                      placeholder="sk-ant-..."
                      value={apiKeys.anthropic}
                      onChange={(e) => setApiKeys({ ...apiKeys, anthropic: e.target.value })}
                    />
                  </div>

                  <div>
                    <Label htmlFor="gemini">Google Gemini API Key (Optional)</Label>
                    <Input
                      id="gemini"
                      type="password"
                      placeholder="AI..."
                      value={apiKeys.gemini}
                      onChange={(e) => setApiKeys({ ...apiKeys, gemini: e.target.value })}
                    />
                  </div>

                  <div className="space-y-2">
                    <Button type="submit" className="w-full">
                      Get Started
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      className="w-full"
                      onClick={handleSkipApiKeys}
                    >
                      Skip for Now
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
} 