import React, { useState, useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Hero from './components/Hero'
import LoginModal from './components/LoginModal'
import HubSelection from './pages/HubSelection'
import UploadPage from './pages/UploadPage'
import DashboardPage from './pages/DashboardPage'
import ReportsPage from './pages/ReportsPage'
import { supabase } from './services/supabase'

function App() {
  const [showHero, setShowHero] = useState(true)
  const [isHeroExiting, setIsHeroExiting] = useState(false)
  const [showLoginModal, setShowLoginModal] = useState(false)
  const [user, setUser] = useState(null)

  // Verificar sessão inicial (embora usemos memória, o Supabase pode retornar se a aba não foi recarregada)
  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null)
      if (session?.user) {
        setShowHero(false)
      }
    })
  }, [])

  const handleAccessClick = () => {
    if (user) {
      handleTransitionToApp()
    } else {
      setShowLoginModal(true)
    }
  }

  const handleLoginSuccess = (loggedInUser) => {
    setUser(loggedInUser)
    setShowLoginModal(false)
    handleTransitionToApp()
  }

  const handleTransitionToApp = () => {
    setIsHeroExiting(true)
    setTimeout(() => {
      setShowHero(false)
    }, 1200)
  }

  const handleLogout = async () => {
    await supabase.auth.signOut()
    setUser(null)
    setIsHeroExiting(false)
    setShowHero(true)
  }

  // Componente AuthGuard interno
  const AuthGuard = ({ children }) => {
    if (!user) {
      return <Navigate to="/" replace />
    }
    return children
  }

  return (
    <>
      {showHero && (
        <Hero 
          onAccess={handleAccessClick} 
          isExiting={isHeroExiting} 
        />
      )}
      
      <LoginModal 
        isOpen={showLoginModal} 
        onClose={() => setShowLoginModal(false)}
        onLoginSuccess={handleLoginSuccess}
      />

      {!showHero && (
        <Routes>
          <Route element={<AuthGuard><Layout onLogout={handleLogout} /></AuthGuard>}>
            <Route path="/" element={<HubSelection />} />
            <Route path="/upload/:obrigacao" element={<UploadPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/reports" element={<ReportsPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      )}
    </>
  )
}

export default App
