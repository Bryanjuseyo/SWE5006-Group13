import { Routes, Route, Navigate } from 'react-router-dom';
import HomePage from '../pages/HomePage';
import LoginPage from '../pages/LoginPage';
import RegisterPage from '../pages/RegisterPage';
import JobRequestListPage from '../pages/JobRequestListPage';
import CreateJobRequestPage from '../pages/CreateJobRequestPage';
import EditJobRequestPage from '../pages/EditJobRequestPage';
import JobRequestDetailPage from '../pages/JobRequestDetailPage';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/job-requests" element={<JobRequestListPage />} />
      <Route path="/job-requests/new" element={<CreateJobRequestPage />} />
      <Route path="/job-requests/:id" element={<JobRequestDetailPage />} />
      <Route path="/job-requests/:id/edit" element={<EditJobRequestPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
