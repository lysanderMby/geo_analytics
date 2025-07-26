import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

// Pages
import OnboardingPage from './pages/OnboardingPage';
import DashboardPage from './pages/DashboardPage';

// Components
import Layout from './components/Layout';
import { useLocalStorage } from './hooks/useLocalStorage';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

function App() {
  const [currentUser] = useLocalStorage('current_user', null);

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-background">
        <Router>
          <Routes>
            {/* Public routes */}
            <Route 
              path="/onboarding" 
              element={
                currentUser ? <Navigate to="/dashboard" replace /> : <OnboardingPage />
              } 
            />
            
            {/* Protected routes */}
            <Route
              path="/*"
              element={
                !currentUser ? (
                  <Navigate to="/onboarding" replace />
                ) : (
                  <Layout>
                    <Routes>
                      <Route path="/" element={<Navigate to="/dashboard" replace />} />
                      <Route path="/dashboard" element={<DashboardPage />} />
                      {/* TODO: Add other pages when implemented */}
                      <Route path="/*" element={<Navigate to="/dashboard" replace />} />
                    </Routes>
                  </Layout>
                )
              }
            />
          </Routes>
        </Router>
      </div>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App; 