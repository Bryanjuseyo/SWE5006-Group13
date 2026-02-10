import { Link } from 'react-router-dom';
import Logo from './Logo';

export default function Navbar() {
  return (
    <nav className="navbar bg-white border-bottom">
      <div className="container">
        <Link to="/" className="navbar-brand m-0">
          <Logo size="sm" />
        </Link>
        <div />
      </div>
    </nav>
  );
}
