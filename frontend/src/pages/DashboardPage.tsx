import { Navigate } from 'react-router-dom';
import { getUser } from '../auth/storage';

export default function DashboardPage() {
  const user = getUser();

  if (!user) return <Navigate to="/login" replace />;

  if (user.role === 'administrator') return <Navigate to="/dashboard/admin" replace />;
  if (user.role === 'cleaner') return <Navigate to="/dashboard/cleaner" replace />;
  return <Navigate to="/dashboard/end-user" replace />;
}