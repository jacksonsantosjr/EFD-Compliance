import React, { useState } from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Hero from './components/Hero'
import HubSelection from './pages/HubSelection'
import UploadPage from './pages/UploadPage'
import DashboardPage from './pages/DashboardPage'
import ReportsPage from './pages/ReportsPage'

function App() {
  const [showHero, setShowHero] = useState(true)
  const [isHeroExiting, setIsHeroExiting] = useState(false)

  const handleAccess = () => {
    setIsHeroExiting(true)
    setTimeout(() => {
      setShowHero(false)
    }, 1200) // Ajustado para a nova duração da transição
  }

  const handleLogout = () => {
    setIsHeroExiting(false)
    setShowHero(true)
  }

  return (
    <>
      {showHero && <Hero onAccess={handleAccess} isExiting={isHeroExiting} />}
      {!showHero && (
        <Routes>
          <Route element={<Layout onLogout={handleLogout} />}>
            <Route path="/" element={<HubSelection />} />
            <Route path="/upload/:obrigacao" element={<UploadPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/reports" element={<ReportsPage />} />
          </Route>
        </Routes>
      )}
    </>
  )
}

export default App
