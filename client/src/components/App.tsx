import React, { useState, useEffect } from 'react';
import '../styles/App.css';
import Header from './Header';
import Dashboard from './dashboard/Dashboard';
import Login from './Login';
import MyDevices from './MyDevices';

const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState('MyDevices');
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
  const [pageKey, setPageKey] = useState<number>(0);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    setIsLoggedIn(Boolean(token));
  }, []);

  // Force remount khi chuyển trang
  useEffect(() => {
    setPageKey(prev => prev + 1);
  }, [currentPage]);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    setIsLoggedIn(false);
  };

  // TODO: bo tam thoi ! ra khoi isLoggedIn de debug
  if (!isLoggedIn) {
    return (
      <div className="app">
        <Header currentPage={currentPage} onNavigate={setCurrentPage} />
        <div className="container">
          <Login onLogin={() => setIsLoggedIn(true)} />
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <Header 
        currentPage={currentPage} 
        onNavigate={setCurrentPage} 
        onLogout={handleLogout}
      />

      <div className="container">
        {currentPage === 'MyDevices' ? (
          <MyDevices key={`my-devices-${pageKey}`} onClose={() => {}} />
        ) : currentPage === 'Dashboard' ? (
          <Dashboard key={`dashboard-${pageKey}`} />
        ) : null}
      </div>
    </div>
  );
};

export default App;
