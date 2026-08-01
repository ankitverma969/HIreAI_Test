import React, { useState } from 'react';
import { NavLink, useLocation, Link } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';
import styles from './Layout.module.css';

export const Layout = ({ children }) => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  // Generate breadcrumbs from current path
  const pathnames = location.pathname.split('/').filter((x) => x);
  
  // Custom mapping for human readable titles
  const routeNames = {
    '': 'Dashboard',
    'upload': 'Screening Setup',
    'processing': 'Live Screening Pipeline',
    'results': 'Screening Results',
    'analytics': 'Candidate Analytics',
    'settings': 'Configurations'
  };

  const getPageTitle = () => {
    const lastPath = pathnames[pathnames.length - 1] || '';
    // Handle candidate dynamic ID title
    if (pathnames[pathnames.length - 2] === 'results') {
      return 'Candidate Profile Details';
    }
    return routeNames[lastPath] || 'Talent Dashboard';
  };

  const menuItems = [
    { path: '/', label: 'Dashboard', icon: '📊' },
    { path: '/upload', label: 'Screening Setup', icon: '📋' },
    { path: '/processing', label: 'Live Pipeline', icon: '⚙️' },
    { path: '/results', label: 'Screening Results', icon: '🏆' },
    { path: '/analytics', label: 'Analytics', icon: '📈' },
    { path: '/settings', label: 'Settings', icon: '⚙️' },
  ];

  return (
    <div className={styles.wrapper}>
      {/* Sidebar Navigation */}
      <aside className={`${styles.sidebar} ${isSidebarOpen ? styles.sidebarOpen : styles.sidebarClosed}`}>
        <div className={styles.brand}>
          <div className={styles.brandLogo}>🤖</div>
          <span className={`${styles.brandName} ${!isSidebarOpen ? styles.collapsedText : ''}`}>
            HIreAI Agent
          </span>
        </div>
        
        <nav className={styles.navMenu}>
          {menuItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `${styles.navLink} ${isActive ? styles.navActive : ''}`
              }
            >
              <span className={styles.navIcon}>{item.icon}</span>
              <span className={!isSidebarOpen ? styles.collapsedText : ''}>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className={styles.sidebarFooter}>
          <span className={!isSidebarOpen ? styles.collapsedText : ''}>
            HIreAI ATS v1.0.0
          </span>
        </div>
      </aside>

      {/* Main Container */}
      <div className={styles.mainContainer}>
        {/* Top Navbar */}
        <header className={styles.topNav}>
          <div className={styles.leftControls}>
            <button className={styles.toggleBtn} onClick={toggleSidebar} aria-label="Toggle Sidebar">
              {isSidebarOpen ? '◀' : '▶'}
            </button>
          </div>

          <div className={styles.rightControls}>
            <button 
              className={styles.themeToggle} 
              onClick={toggleTheme} 
              aria-label="Toggle Dark/Light Mode"
            >
              {theme === 'light' ? '🌙' : '☀️'}
            </button>
            <div className={styles.userBadge}>
              <div className={styles.avatar}>HR</div>
              <span>Recruiter Portal</span>
            </div>
          </div>
        </header>

        {/* Content Body */}
        <main className={styles.contentArea}>
          <div className={styles.contentWrapper}>
            <div className={styles.pageHeader}>
              {/* Breadcrumbs */}
              <div className={styles.breadcrumbs}>
                <Link to="/" style={{ color: 'inherit', textDecoration: 'none' }}>Home</Link>
                {pathnames.map((value, index) => {
                  const to = `/${pathnames.slice(0, index + 1).join('/')}`;
                  const isLast = index === pathnames.length - 1;
                  const label = routeNames[value] || value;
                  return (
                    <React.Fragment key={to}>
                      <span className={styles.breadcrumbSeparator}>/</span>
                      {isLast ? (
                        <span>{label}</span>
                      ) : (
                        <Link to={to} style={{ color: 'inherit', textDecoration: 'none' }}>{label}</Link>
                      )}
                    </React.Fragment>
                  );
                })}
              </div>
              <h1 className={styles.pageTitle}>{getPageTitle()}</h1>
            </div>

            {/* Inner Route Component page */}
            {children}
          </div>
        </main>

        {/* Footer */}
        <footer className={styles.footer}>
          <span>© {new Date().getFullYear()} HIreAI. All rights reserved.</span>
          <span>Enterprise ATS Portal</span>
        </footer>
      </div>
    </div>
  );
};

export default Layout;
