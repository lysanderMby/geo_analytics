import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { useDashboard } from '../hooks/useApi';
import { useLocalStorage } from '../hooks/useLocalStorage';
import { User } from '../types';
import { formatPercentage, formatNumber, formatDate } from '../lib/utils';
import { BarChart3, Users, MessageSquare, TrendingUp, Plus } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function DashboardPage() {
  const [currentUser] = useLocalStorage<User | null>('current_user', null);
  const { data: dashboardData, isLoading, error } = useDashboard(currentUser?.id || '');

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg">Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-red-600">Failed to load dashboard data</div>
      </div>
    );
  }

  const stats = [
    {
      title: 'Total Prompts',
      value: formatNumber(dashboardData?.total_prompts || 0),
      icon: MessageSquare,
      description: 'Test prompts created',
      color: 'text-blue-600'
    },
    {
      title: 'Competitors',
      value: formatNumber(dashboardData?.total_competitors || 0),
      icon: Users,
      description: 'Competitors being tracked',
      color: 'text-green-600'
    },
    {
      title: 'LLM Responses',
      value: formatNumber(dashboardData?.total_responses || 0),
      icon: BarChart3,
      description: 'Total responses analyzed',
      color: 'text-purple-600'
    },
    {
      title: 'Brand Mention Rate',
      value: formatPercentage(dashboardData?.user_brand_mention_rate || 0),
      icon: TrendingUp,
      description: 'Your brand appears in responses',
      color: 'text-orange-600'
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            Welcome back, {currentUser?.business_name}
          </h1>
          <p className="text-gray-600">
            Here's how your brand is performing in AI responses
          </p>
        </div>
        <Button asChild>
          <Link to="/analytics">
            <Plus className="mr-2 h-4 w-4" />
            Start Analysis
          </Link>
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.title}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
                <Icon className={`h-4 w-4 ${stat.color}`} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                <p className="text-xs text-muted-foreground">{stat.description}</p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Discover Competitors</CardTitle>
            <CardDescription>
              Use AI to automatically find your main competitors
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild variant="outline" className="w-full">
              <Link to="/competitors">
                <Users className="mr-2 h-4 w-4" />
                Manage Competitors
              </Link>
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Generate Prompts</CardTitle>
            <CardDescription>
              Create relevant test prompts for your industry
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild variant="outline" className="w-full">
              <Link to="/prompts">
                <MessageSquare className="mr-2 h-4 w-4" />
                Manage Prompts
              </Link>
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>View Analytics</CardTitle>
            <CardDescription>
              Deep dive into your brand mention analytics
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild variant="outline" className="w-full">
              <Link to="/analytics">
                <BarChart3 className="mr-2 h-4 w-4" />
                View Analytics
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Getting Started</CardTitle>
          <CardDescription>
            Follow these steps to start tracking your brand mentions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-sm font-medium">
                1
              </div>
              <div>
                <p className="font-medium">Add API Keys</p>
                <p className="text-sm text-gray-600">Configure your OpenAI, Anthropic, or Gemini API keys</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-sm font-medium">
                2
              </div>
              <div>
                <p className="font-medium">Discover Competitors</p>
                <p className="text-sm text-gray-600">Let AI find your main competitors automatically</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-sm font-medium">
                3
              </div>
              <div>
                <p className="font-medium">Generate Test Prompts</p>
                <p className="text-sm text-gray-600">Create industry-specific prompts for testing</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-sm font-medium">
                4
              </div>
              <div>
                <p className="font-medium">Run Analysis</p>
                <p className="text-sm text-gray-600">Test your prompts and analyze brand mentions</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Summary Info */}
      {dashboardData?.last_analysis_date && (
        <Card>
          <CardHeader>
            <CardTitle>Last Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600">
              Last analysis completed on {formatDate(dashboardData.last_analysis_date)}
            </p>
            <div className="mt-4 space-y-2">
              <div className="flex justify-between">
                <span>Your Brand Mention Rate:</span>
                <span className="font-medium">
                  {formatPercentage(dashboardData.user_brand_mention_rate)}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Top Competitor Rate:</span>
                <span className="font-medium">
                  {formatPercentage(dashboardData.top_competitor_mention_rate)}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
} 