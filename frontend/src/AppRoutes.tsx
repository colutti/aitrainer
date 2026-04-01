import { Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';


// STATIC IMPORTS for E2E and Build Stability
import LoginPage from './features/auth/LoginPage';
import BodyPage from './features/body/BodyPage';
import ChatPage from './features/chat/ChatPage';
import DashboardPage from './features/dashboard/DashboardPage';
import LandingPage from './features/landing/LandingPage';
import PrivacyPage from './features/legal/PrivacyPage';
import TermsPage from './features/legal/TermsPage';
import MemoriesPage from './features/memories/MemoriesPage';
import OnboardingPage from './features/onboarding/components/OnboardingPage';
import IntegrationsPage from './features/settings/components/IntegrationsPage';
import SubscriptionPage from './features/settings/components/SubscriptionPage';
import TrainerSettingsPage from './features/settings/components/TrainerSettingsPage';
import UserProfilePage from './features/settings/components/UserProfilePage';
import SettingsPage from './features/settings/SettingsPage';
import WorkoutsPage from './features/workouts/WorkoutsPage';
import { AuthGuard } from './shared/components/auth/AuthGuard';
import { ProtectedRoute } from './shared/components/auth/ProtectedRoute';
import { PremiumLayout } from './shared/components/layout/PremiumLayout';
import { Skeleton } from './shared/components/ui/Skeleton';

/**
 * Loading Fallback for Suspense
 */
function PageLoader() {
  return (
    <div className="flex flex-col gap-8 animate-pulse p-8">
      <Skeleton className="h-12 w-1/3 rounded-2xl bg-white/5" />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Skeleton className="h-64 rounded-[32px] bg-white/5" />
        <Skeleton className="h-64 rounded-[32px] bg-white/5" />
        <Skeleton className="h-64 rounded-[32px] bg-white/5" />
      </div>
    </div>
  );
}

export function AppRoutes() {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<AuthGuard><LandingPage /></AuthGuard>} />
        <Route path="/login" element={<AuthGuard><LoginPage /></AuthGuard>} />
        <Route path="/termos-de-uso" element={<TermsPage />} />
        <Route path="/politica-de-privacidade" element={<PrivacyPage />} />
        <Route path="/terms" element={<Navigate to="/termos-de-uso" replace />} />
        <Route path="/privacy" element={<Navigate to="/politica-de-privacidade" replace />} />
        
        {/* Protected Onboarding */}
        <Route 
          path="/onboarding" 
          element={
            <ProtectedRoute>
              <OnboardingPage />
            </ProtectedRoute>
          } 
        />

        {/* Dashboard Protected Layout */}
        <Route 
          path="/dashboard" 
          element={
            <ProtectedRoute>
              <PremiumLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<DashboardPage />} />
          <Route path="workouts" element={<WorkoutsPage />} />
          <Route path="body/*" element={<BodyPage />} />
          <Route path="chat" element={<ChatPage />} />
          
          {/* Settings Sub-routes */}
          <Route path="settings" element={<SettingsPage />}>
            <Route index element={<Navigate to="profile" replace />} />
            <Route path="profile" element={<UserProfilePage />} />
            <Route path="subscription" element={<SubscriptionPage />} />
            <Route path="trainer" element={<TrainerSettingsPage />} />
            <Route path="integrations" element={<IntegrationsPage />} />
            <Route path="memories" element={<MemoriesPage />} />
          </Route>
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}
