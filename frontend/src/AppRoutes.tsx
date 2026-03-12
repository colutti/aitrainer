import { Routes, Route, Navigate } from 'react-router-dom';

import { LoginPage } from './features/auth/LoginPage';
import { BodyPage } from './features/body/BodyPage';
import { ChatPage } from './features/chat/ChatPage';
import { DashboardPage } from './features/dashboard/DashboardPage';
import LandingPage from './features/landing/LandingPage';
import { MemoriesPage } from './features/memories/MemoriesPage';
import { NutritionPage } from './features/nutrition/NutritionPage';
import { OnboardingPage } from './features/onboarding/components/OnboardingPage';
import { IntegrationsPage } from './features/settings/components/IntegrationsPage';
import { TrainerSettingsPage } from './features/settings/components/TrainerSettingsPage';
import { UserProfilePage } from './features/settings/components/UserProfilePage';
import { SettingsPage } from './features/settings/SettingsPage';
import { WorkoutsPage } from './features/workouts/WorkoutsPage';
import { AuthGuard } from './shared/components/auth/AuthGuard';
import { ProtectedRoute } from './shared/components/auth/ProtectedRoute';
import { MainLayout } from './shared/components/layout/MainLayout';


/**
 * AppRoutes component
 * 
 * Defines the routing structure of the application.
 * Handles public routes, protected routes, and layouts.
 */
export function AppRoutes() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/" element={<LandingPage />} />
      <Route
        path="/login"
        element={
          <AuthGuard>
            <LoginPage />
          </AuthGuard>
        }
      />
      <Route
        path="/onboarding"
        element={
          <AuthGuard>
            <OnboardingPage />
          </AuthGuard>
        }
      />

      {/* Protected Routes - Main Layout */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      >
        {/* Dashboard / Home */}
        <Route index element={<DashboardPage />} />
        
        {/* Workouts */}
        <Route path="workouts" element={<WorkoutsPage />} />
        {/* Nutrition */}
        <Route path="nutrition" element={<NutritionPage />} />
        {/* Body Routes - Now nested for Weight/Nutrition */}
        <Route path="body">
          <Route index element={<Navigate to="weight" replace />} />
          <Route path="weight" element={<BodyPage />} />
          <Route path="nutrition" element={<BodyPage />} />
        </Route>
        
        {/* Chat */}
        <Route path="chat" element={<ChatPage />} />
        
        {/* Settings with nested routes */}
        <Route path="settings" element={<SettingsPage />}>
          <Route index element={<Navigate to="profile" replace />} />
          <Route path="profile" element={<UserProfilePage />} />
          <Route path="memories" element={<MemoriesPage />} />
          <Route path="trainer" element={<TrainerSettingsPage />} />
          <Route path="integrations" element={<IntegrationsPage />} />
        </Route>
      </Route>

      {/* Catch-all - Redirect to dashboard */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
