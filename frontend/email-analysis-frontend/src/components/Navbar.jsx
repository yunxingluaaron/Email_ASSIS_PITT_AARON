import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from './AuthContext';
import '../App.css';

const Navbar = () => {
  const { currentUser, logout } = useAuth();

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-logo">
          Email Style Analyzer
        </Link>
        
        <div className="navbar-links">
          {currentUser ? (
            <>
              <Link to="/dashboard" className="nav-link">Dashboard</Link>
              <span className="user-email">{currentUser.email}</span>
              <button onClick={logout} className="logout-button">Logout</button>
            </>
          ) : (
            <>
              <Link to="/login" className="nav-link">Login</Link>
              <Link to="/register" className="nav-link register-link">Register</Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;