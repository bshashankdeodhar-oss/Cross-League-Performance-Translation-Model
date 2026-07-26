import React from 'react';
import { useAuth } from '../context/AuthContext';
import { LogOut, Activity } from 'lucide-react';

export const Navbar = () => {
  const { user, logout } = useAuth();

  return (
    <header className="app-navbar">
      <div className="brand-title">
        <Activity size={20} color="#2563eb" />
        CLPTM Dashboard
        <span className="brand-badge">v1.0</span>
      </div>

      {user && (
        <div className="nav-user">
          <span className={`user-badge ${user.role === 'admin' ? 'admin' : ''}`}>
            {user.username} ({user.role})
          </span>
          <button className="btn btn-outline" onClick={logout} style={{ padding: '6px 12px', fontSize: '0.85rem' }}>
            <LogOut size={14} />
            Sign out
          </button>
        </div>
      )}
    </header>
  );
};
