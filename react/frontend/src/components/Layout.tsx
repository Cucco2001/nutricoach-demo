import React, { ReactNode } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Home, UtensilsCrossed, MessageCircle, Settings, LogOut } from 'lucide-react';
import './Layout.css';

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const tabs = [
    { id: 'home', label: 'Home', icon: Home, path: '/home' },
    { id: 'diet', label: 'Diet', icon: UtensilsCrossed, path: '/diet' },
    { id: 'chat', label: 'Chat', icon: MessageCircle, path: '/chat' },
    { id: 'settings', label: 'Settings', icon: Settings, path: '/settings' },
  ];

  const handleTabClick = (path: string) => {
    navigate(path);
  };

  const handleLogout = () => {
    logout();
  };

  return (
    <div className="layout">
      <header className="header">
        <div className="header-left">
          <h1>🥗 NutrAICoach</h1>
        </div>
        <div className="header-right">
          <span className="user-info">Ciao, {user?.username}!</span>
          <button onClick={handleLogout} className="logout-btn">
            <LogOut size={20} />
          </button>
        </div>
      </header>

      <nav className="navigation">
        <div className="tab-container">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = location.pathname === tab.path;
            return (
              <button
                key={tab.id}
                onClick={() => handleTabClick(tab.path)}
                className={`tab ${isActive ? 'active' : ''}`}
              >
                <Icon size={20} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </nav>

      <main className="main-content">
        {children}
      </main>
    </div>
  );
};

export default Layout; 