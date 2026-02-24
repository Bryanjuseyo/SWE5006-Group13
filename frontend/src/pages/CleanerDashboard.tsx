import Navbar from '../components/Navbar';
import { Link } from 'react-router-dom';

export default function CleanerDashboard() {
  return (
    <>
      <Navbar />
      <main className="container py-5">
        <h1 className="h3 fw-bold">Cleaner Dashboard</h1>
        <p className="text-muted">Placeholder for Sprint 1.</p>
        <Link to="/cleaner/profile" className="btn btn-primary">
          Edit Cleaner Profile
        </Link>
      </main>
    </>
  );
}