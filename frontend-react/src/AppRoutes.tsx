import { Routes, Route, Navigate } from 'react-router-dom';

import { AdminDashboardPage } from './features/admin/components/AdminDashboardPage';
import { AdminLayout } from './features/admin/components/AdminLayout';
import { AdminLogsPage } from './features/admin/components/AdminLogsPage';
import { AdminPromptsPage } from './features/admin/components/AdminPromptsPage';
import { AdminUsersPage } from './features/admin/components/AdminUsersPage';
import { LoginPage } from './features/auth/LoginPage';
import { BodyPage } from './features/body/BodyPage';
import { ChatPage } from './features/chat/ChatPage';
import { DashboardPage } from './features/dashboard/DashboardPage';
import { MemoriesPage } from './features/memories/MemoriesPage';
import { NutritionPage } from './features/nutrition/NutritionPage';
import { OnboardingPage } from './features/onboarding/components/OnboardingPage';
import { SettingsPage } from './features/settings/SettingsPage';
import { WorkoutListPage } from './features/workouts/WorkoutListPage';
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
        path="/"
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      >
        {/* Dashboard / Home */}
        <Route index element={<DashboardPage />} />
        
        {/* Workouts */}
        <Route path="workouts" element={<WorkoutListPage />} />
        {/* Nutrition */}
        <Route path="nutrition" element={<NutritionPage />} />
        {/* Body */}
        <Route path="body" element={<BodyPage />} />
        {/* Chat */}
        <Route path="chat" element={<ChatPage />} />
        <Route path="memories" element={<MemoriesPage />} />
        <Route path="settings" element={<SettingsPage />} />

        {/* Admin Routes */}
        <Route
          path="admin"
          element={
            <ProtectedRoute requireAdmin>
              <AdminLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<AdminDashboardPage />} />
          <Route path="users" element={<AdminUsersPage />} />
          <Route path="logs" element={<AdminLogsPage />} />
          <Route path="prompts" element={<AdminPromptsPage />} />
        </Route>
      </Route>

      {/* Catch-all - Redirect to home */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
