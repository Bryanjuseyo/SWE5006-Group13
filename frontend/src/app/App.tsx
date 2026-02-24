import { Routes, Route, Navigate } from 'react-router-dom';
import HomePage from '../pages/HomePage';
import LoginPage from '../pages/LoginPage';
import RegisterPage from '../pages/RegisterPage';

import DashboardPage from '../pages/DashboardPage';
import AdminDashboard from '../pages/AdminDashboard';
import CleanerDashboard from '../pages/CleanerDashboard';
import EndUserDashboard from '../pages/EndUserDashboard';
import ForbiddenPage from '../pages/ForbiddenPage';

import { RequireAuth, RequireRole } from '../auth/guards';

// (Profile pages next – we’ll add after this step)
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route
        path="/dashboard"
        element={
          <RequireAuth>
            <DashboardPage />
          </RequireAuth>
        }
      />

      <Route
        path="/dashboard/end-user"
        element={
          <RequireRole role="end_user">
            <EndUserDashboard />
          </RequireRole>
        }
      />

      <Route
        path="/dashboard/cleaner"
        element={
          <RequireRole role="cleaner">
            <CleanerDashboard />
          </RequireRole>
        }
      />

      <Route
        path="/dashboard/admin"
        element={
          <RequireRole role="administrator">
            <AdminDashboard />
          </RequireRole>
        }
      />

      <Route path="/forbidden" element={<ForbiddenPage />} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}