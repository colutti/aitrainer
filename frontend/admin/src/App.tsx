import { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

import { AdminDashboardPage } from './features/admin/components/AdminDashboardPage';
import { AdminLayout } from './features/admin/components/AdminLayout';
import { AdminLogsPage } from './features/admin/components/AdminLogsPage';
import { AdminPromptsPage } from './features/admin/components/AdminPromptsPage';
import { AdminTokensPage } from './features/admin/components/AdminTokensPage';
import { AdminUsersPage } from './features/admin/components/AdminUsersPage';
import { LoginPage } from './features/auth/LoginPage';
import { AdminProtectedRoute } from './shared/components/AdminProtectedRoute';
import { useAdminAuthStore } from './shared/hooks/useAdminAuth';

export default function App() {
  const init = useAdminAuthStore((state) => state.init);

  useEffect(() => {
    init().catch(console.error);
  }, [init]);

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <AdminProtectedRoute>
              <AdminLayout />
            </AdminProtectedRoute>
          }
        >
          <Route index element={<AdminDashboardPage />} />
          <Route path="users" element={<AdminUsersPage />} />
          <Route path="logs" element={<AdminLogsPage />} />
          <Route path="prompts" element={<AdminPromptsPage />} />
          <Route path="tokens" element={<AdminTokensPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}
