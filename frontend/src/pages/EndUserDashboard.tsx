import Navbar from '../components/Navbar';
import JobRequestList from '../components/JobRequestList';

export default function EndUserDashboard() {
  return (
    <>
      <Navbar />
      <main className="container py-5">
        <h1 className="h3 fw-bold mb-4">End-User Dashboard</h1>
        <JobRequestList />
      </main>
    </>
  );
}
