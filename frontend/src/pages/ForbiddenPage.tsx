import Navbar from '../components/Navbar';
import { Link } from 'react-router-dom';

export default function ForbiddenPage() {
  return (
    <>
      <Navbar />
      <main className="container py-5" style={{ maxWidth: 720 }}>
        <h1 className="h3 fw-bold">403 Forbidden</h1>
        <p className="text-muted">You don’t have permission to access this page.</p>
        <Link to="/dashboard" className="btn btn-primary">Go to Dashboard</Link>
      </main>
    </>
  );
}