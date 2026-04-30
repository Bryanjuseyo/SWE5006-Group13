import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';

const NAV_CARDS = [
  {
    to: '/cleaner/profile',
    title: 'Service Setup',
    description: 'Set your service type (partial/full), hourly rate, and years of experience.',
    btnLabel: 'Edit Profile',
    btnClass: 'btn-primary',
  },
  {
    to: '/cleaner/availability',
    title: 'Availability',
    description: 'Manage your available date ranges and time windows to avoid unwanted bookings.',
    btnLabel: 'Manage Availability',
    btnClass: 'btn-outline-primary',
  },
  {
    to: '/cleaner/browse-jobs',
    title: 'Browse Jobs',
    description: 'View and accept open job requests that match your service type.',
    btnLabel: 'Browse Available Jobs',
    btnClass: 'btn-success',
  },
  {
    to: '/cleaner/schedule',
    title: 'Upcoming Schedule',
    description: 'See all your upcoming confirmed and in-progress jobs in one place.',
    btnLabel: 'View Schedule',
    btnClass: 'btn-outline-secondary',
  },
];

export default function CleanerDashboard() {
  return (
    <>
      <Navbar />
      <main className="container py-5">
        <h1 className="h3 fw-bold mb-1">Cleaner Dashboard</h1>
        <p className="text-muted mb-5">Welcome back. Manage your services, availability, and jobs below.</p>

        <div className="row g-4 mb-5">
          {NAV_CARDS.map((card) => (
            <div key={card.to} className="col-12 col-md-6">
              <div className="card h-100 shadow-sm">
                <div className="card-body d-flex flex-column">
                  <h5 className="card-title fw-semibold">{card.title}</h5>
                  <p className="card-text text-muted flex-grow-1">{card.description}</p>
                  <Link to={card.to} className={`btn ${card.btnClass} mt-2 align-self-start`}>
                    {card.btnLabel}
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      </main>
    </>
  );
}
