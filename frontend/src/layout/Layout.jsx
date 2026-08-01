import React, { useState } from 'react';
import { NavLink, useLocation, Link } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';
import styles from './Layout.module.css';

// Navigation structure with SVG-based icon strings
const NAV_GROUPS = [
  {
    label: 'Core',
    items: [
      { path: '/',           label: 'Dashboard',        icon: '📊' },
      { path: '/upload',     label: 'Screening Setup',   icon: '📋' },
      { path: '/processing', label: 'Live Pipeline',     icon: '⚙️' },
      { path: '/results',    label: 'Results',           icon: '🏆' },
    ],
  },
  {
    label: 'Intelligence',
    items: [
      { path: '/compare',        label: 'Compare',          icon: '⚖️' },
      { path: '/chat',           label: 'AI Recruiter Chat', icon: '💬' },
      { path: '/analytics',      label: 'Analytics',        icon: '📈' },
      { path: '/insights',       label: 'Insights',         icon: '💡' },
    ],
  },
  {
    label: 'Executive',
    items: [
      { path: '/executive',      label: 'Exec Dashboard',   icon: '🎯' },
      { path: '/reports',        label: 'Reports',          icon: '📄' },
      { path: '/explainability', label: 'Explainability',   icon: '🔍' },
    ],
  },
  {
    label: 'Developer',
    items: [
      { path: '/audit',    label: 'Audit Logs',       icon: '📜' },
      { path: '/graph',    label: 'Execution Graph',  icon: '🕸️' },
      { path: '/prompts',  label: 'Prompt Inspector', icon: '🧪' },
    ],
  },
  {
    label: 'System',
    items: [
      { path: '/settings', label: 'Settings', icon: '⚙️' },
    ],
  },
];

const routeNames = {
  '':             'Dashboard',
  upload:         'Screening Setup',
  processing:     'Live Screening Pipeline',
  results:        'Screening Results',
  compare:        'Candidate Comparison',
  chat:           'AI Recruiter Chat',
  executive:      'Executive Dashboard',
  insights:       'Hiring Insights',
  reports:        'Reports',
  explainability: 'Explainability',
  audit:          'Audit Logs',
  graph:          'Execution Graph',
  prompts:        'Prompt Inspector',
  analytics:      'Candidate Analytics',
  settings:       'Configurations',
};

export const Layout = ({ children }) => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();

  // Prevent body scroll when sidebar is open on small screens
  React.useEffect(() => {
    const handleLock = () => {
      const isMobile = window.innerWidth <= 900;
      if (isMobile && isSidebarOpen) document.body.classList.add('no-scroll');
      else document.body.classList.remove('no-scroll');
    };

    handleLock();
    window.addEventListener('resize', handleLock);
    return () => {
      window.removeEventListener('resize', handleLock);
      document.body.classList.remove('no-scroll');
    };
  }, [isSidebarOpen]);

  const pathnames = location.pathname.split('/').filter(Boolean);

  const getPageTitle = () => {
    const last = pathnames[pathnames.length - 1] || '';
    if (pathnames[pathnames.length - 2] === 'results') return 'Candidate Profile';
    return routeNames[last] || 'Dashboard';
  };

  // Read the configured model from localStorage for the topbar badge
  const activeModel = localStorage.getItem('llmModel') || 'gpt-4o-mini';

  return (
    <div className={styles.wrapper}>
      {/* ── Sidebar ───────────────────────────────────────── */}
      <aside
        className={`${styles.sidebar} ${isSidebarOpen ? styles.sidebarOpen : styles.sidebarClosed}`}
        aria-label="Main Navigation"
      >
        {/* Brand */}
        <div className={styles.brand}>
          <div className={styles.brandLogo}>🤖</div>
          <div className={`${styles.brandText} ${!isSidebarOpen ? styles.collapsedText : ''}`}>
            <span className={styles.brandName}>HIreAI</span>
            <span className={styles.brandTagline}>ATS Portal v1.0</span>
          </div>
        </div>

        {/* Navigation */}
        <nav className={styles.navMenu}>
          {NAV_GROUPS.map((group) => (
            <React.Fragment key={group.label}>
              {isSidebarOpen && (
                <div className={styles.navSection}>{group.label}</div>
              )}
              {group.items.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  end={item.path === '/'}
                  className={({ isActive }) =>
                    `${styles.navLink} ${isActive ? styles.navActive : ''}`
                  }
                  title={!isSidebarOpen ? item.label : undefined}
                >
                  <span className={styles.navIcon}>{item.icon}</span>
                  <span className={`${styles.navLabel} ${!isSidebarOpen ? styles.collapsedText : ''}`}>
                    {item.label}
                  </span>
                </NavLink>
              ))}
            </React.Fragment>
          ))}
        </nav>

        {/* Sidebar Footer — connection status */}
        <div className={styles.sidebarFooter}>
          <div className={styles.wsIndicator}>
            <span className={styles.wsDot} />
            <span className={`${!isSidebarOpen ? styles.collapsedText : ''}`}>
              System Online
            </span>
          </div>
        </div>
      </aside>

      {/* ── Main Container ────────────────────────────────── */}
      <div className={styles.mainContainer}>
        {/* Top Navigation Bar */}
        <header className={styles.topNav}>
          <div className={styles.leftControls}>
            <button
              className={styles.toggleBtn}
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              aria-label="Toggle Sidebar"
            >
              {isSidebarOpen ? '◀' : '▶'}
            </button>

            <div className={styles.pageInfo}>
              <div className={styles.breadcrumbs}>
                <Link to="/" className={styles.breadcrumbLink}>Home</Link>
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
                        <Link to={to} className={styles.breadcrumbLink}>{label}</Link>
                      )}
                    </React.Fragment>
                  );
                })}
              </div>
              <span className={styles.pageTitle}>{getPageTitle()}</span>
            </div>
          </div>

          <div className={styles.rightControls}>
            {/* Active model indicator */}
            <div className={styles.modelBadge}>
              <span className={styles.modelDot} />
              {activeModel}
            </div>

            {/* Theme toggle */}
            <button
              className={styles.themeToggle}
              onClick={toggleTheme}
              aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
            >
              {theme === 'light' ? '🌙' : '☀️'}
            </button>

            {/* User badge */}
            <div className={styles.userBadge} aria-label="User account">
              <div className={styles.avatar}>HR</div>
              <span className={styles.userName}>Recruiter Portal</span>
            </div>
          </div>
        </header>

        {/* Content Body */}
        <main className={styles.contentArea}>
          <div className={styles.contentWrapper}>
            {children}
          </div>
        </main>

        {/* Footer */}
        <footer className={styles.footer}>
          <span>© {new Date().getFullYear()} HIreAI — Enterprise ATS Platform</span>
          <span>
            Powered by&nbsp;
            <a
              href="https://langchain.com"
              target="_blank"
              rel="noreferrer"
              className={styles.footerLink}
            >
              LangChain
            </a>
            &nbsp;&amp;&nbsp;
            <a
              href="https://fastapi.tiangolo.com"
              target="_blank"
              rel="noreferrer"
              className={styles.footerLink}
            >
              FastAPI
            </a>
          </span>
        </footer>
      </div>
    </div>
  );
};

export default Layout;
