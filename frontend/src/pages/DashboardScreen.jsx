import React from 'react';
import { Navbar } from '../components/Navbar';

export const DashboardScreen = () => {
  return (
    <div className="app-layout">
      <Navbar />
      <main className="dashboard-content">
        <div className="page-header">
          <h2 className="page-title">Cross-League Performance Translation</h2>
          <p className="page-subtitle">Predict player performance translations across major leagues.</p>
        </div>
      </main>
    </div>
  );
};
