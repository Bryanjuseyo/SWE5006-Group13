import { Routes, Route, Navigate } from 'react-router-dom';
import HomePage from '../pages/HomePage';
import LoginPage from '../pages/LoginPage';
import RegisterPage from '../pages/RegisterPage';
import JobRequestListPage from '../pages/JobRequestListPage';
import CreateJobRequestPage from '../pages/CreateJobRequestPage';
import EditJobRequestPage from '../pages/EditJobRequestPage';
import JobRequestDetailPage from '../pages/JobRequestDetailPage';

import DashboardPage from '../pages/DashboardPage';
import AdminDashboard from '../pages/AdminDashboard';
import CleanerDashboard from '../pages/CleanerDashboard';
import EndUserDashboard from '../pages/EndUserDashboard';
import ForbiddenPage from '../pages/ForbiddenPage';

import { RequireAuth, RequireRole } from '../auth/guards';

import ProfilePage from '../pages/ProfilePage';
import CleanerProfilePage from '../pages/CleanerProfilePage';

import ViewCleanersPage from '../pages/ViewCleanersPage';
import CleanerAvailabilityPage from '../pages/CleanerAvailabilityPage';
import CleanerSchedulePage from '../pages/CleanerSchedulePage';
import BrowseJobsPage from '../pages/BrowseJobsPage';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/job-requests" element={
        <RequireAuth>
          <JobRequestListPage />
        </RequireAuth>
        } 
      />
      <Route path="/job-requests/new" element={
        <RequireAuth>
          <CreateJobRequestPage />
        </RequireAuth>
        } 
      />
      <Route path="/job-requests/:id" element={
        <RequireAuth>
          <JobRequestDetailPage />
        </RequireAuth>
        } 
      />
      <Route path="/job-requests/:id/edit" element={
        <RequireAuth>
          <EditJobRequestPage />
        </RequireAuth>
        } 
      />

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

      <Route
        path="/profile"
        element={
          <RequireAuth>
            <ProfilePage />
          </RequireAuth>
        }
      />

      <Route
        path="/cleaner/profile"
        element={
          <RequireRole role="cleaner">
            <CleanerProfilePage />
          </RequireRole>
        }
      />

      <Route
        path="/cleaner/availability"
        element={
          <RequireRole role="cleaner">
            <CleanerAvailabilityPage />
          </RequireRole>
        }
      />

      <Route
        path="/cleaner/schedule"
        element={
          <RequireRole role="cleaner">
            <CleanerSchedulePage />
          </RequireRole>
        }
      />

      <Route
        path="/cleaner/browse-jobs"
        element={
          <RequireRole role="cleaner">
            <BrowseJobsPage />
          </RequireRole>
        }
      />

      <Route
        path="/cleaners"
        element={
          <RequireRole role="end_user">
            <ViewCleanersPage />
          </RequireRole>
        }
      />
    </Routes>
  );
}