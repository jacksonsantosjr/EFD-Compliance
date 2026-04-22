import { useState, useEffect } from 'react'
import { Outlet, NavLink, useLocation } from 'react-router-dom'

function Layout() {
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'light')
  const location = useLocation()

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }, [theme])

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light')
  }

  const getPageTitle = () => {
    switch (location.pathname) {
      case '/': return 'Upload de Arquivo'
      case '/dashboard': return 'Dashboard de Análise'
      case '/reports': return 'Relatórios e Dossiês'
      default: return 'EFD Compliance'
    }
  }

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <span className="logo-icon">🛡️</span>
          <span>EFD Compliance</span>
        </div>

        <nav className="sidebar-nav">
          <NavLink
            to="/"
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            end
          >
            <span className="nav-icon">📤</span>
            Upload
          </NavLink>
          <NavLink
            to="/dashboard"
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <span className="nav-icon">📊</span>
            Dashboard
          </NavLink>
          <NavLink
            to="/reports"
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <span className="nav-icon">📑</span>
            Relatórios
          </NavLink>
        </nav>

        <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: 'var(--space-4)' }}>
          <div className="nav-item" onClick={toggleTheme}>
            <span className="nav-icon">{theme === 'light' ? '🌙' : '☀️'}</span>
            {theme === 'light' ? 'Modo Escuro' : 'Modo Claro'}
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="main-area">
        <header className="header">
          <h1 className="header-title">{getPageTitle()}</h1>
          <div className="header-actions">
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-tertiary)' }}>
              v1.0.0
            </span>
          </div>
        </header>

        <div className="content">
          <Outlet />
        </div>
      </main>
    </div>
  )
}

export default Layout
