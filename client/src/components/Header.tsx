import React from 'react';
import '../styles/Header.css';

interface HeaderProps {
  currentPage: string;
  onNavigate: (page: string) => void;
  onLogout?: () => void;
}

const Header: React.FC<HeaderProps> = ({ currentPage, onNavigate, onLogout }) => {
  return (
    <header className="header">
      <div className="header-left">
        <svg className="header-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
        <h1 className="header-title">IoT Manager</h1>
      </div>
      <nav className="nav">
        <button
          onClick={() => onNavigate('MyDevices')}
          className={`nav-button ${currentPage === 'MyDevices' ? 'active' : ''}`}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z" />
          </svg>
          Thiết bị của tôi
        </button>
        <button
          onClick={() => onNavigate('Dashboard')}
          className={`nav-button ${currentPage === 'Dashboard' ? 'active' : ''}`}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
          Bảng điều khiển
        </button>
        {onLogout && (
          <button
            onClick={onLogout}
            className="nav-button nav-button-logout"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" />
            </svg>
            Đăng xuất
          </button>
        )}
      </nav>
    </header>
  );
};

export default Header;


