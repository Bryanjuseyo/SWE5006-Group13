import Navbar from '../components/Navbar';
import JobRequestList from '../components/JobRequestList';

export default function JobRequestListPage() {
  return (
    <>
      <Navbar />
      <main className="container py-5">
        <JobRequestList />
      </main>
    </>
  );
}
