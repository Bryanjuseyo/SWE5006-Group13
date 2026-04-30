import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Logo from '../components/Logo';

export default function HomePage() {
  return (
    <>
      <Navbar />

      <main className="container">
        <div
          className="d-flex flex-column align-items-center justify-content-center text-center"
          style={{ minHeight: 'calc(100vh - 72px)' }}
        >
          <div className="d-flex flex-column align-items-center">
            <Logo size="lg" />
            <h1 className="fw-bold mt-2">CleanMatch</h1>
            <p className="text-muted mb-4" style={{ maxWidth: 520 }}>
              Find suitable cleaners based on service requirements, availability, and preferences.
            </p>
          </div>

          <div className="d-flex gap-3">
            <Link to="/register" className="btn btn-primary px-4">
              Register
            </Link>
            <Link to="/login" className="btn btn-outline-primary px-4">
              Login
            </Link>
          </div>
        </div>
      </main>
    </>
  );
}
