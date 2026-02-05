import { Routes, Route, Navigate } from 'react-router-dom';

import { LoginPage } from './features/auth/LoginPage';
import { BodyPage } from './features/body/BodyPage';
import { DashboardPage } from './features/dashboard/DashboardPage';
import { NutritionPage } from './features/nutrition/NutritionPage';
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
        <Route path="chat" element={<div className="text-2xl font-bold">Chat AI (Em breve)</div>} />
        <Route path="settings" element={<div className="text-2xl font-bold">Configurações (Em breve)</div>} />

        {/* Admin Routes */}
        <Route
          path="admin"
          element={
            <ProtectedRoute requireAdmin>
              <div className="text-2xl font-bold text-gradient-start">Painel Administrativo (Em breve)</div>
            </ProtectedRoute>
          }
        />
      </Route>

      {/* Catch-all - Redirect to home */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
