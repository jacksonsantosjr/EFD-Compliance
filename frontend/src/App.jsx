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
    }, 800) // Mesma duração da animação de saída
  }

  return (
    <>
      {showHero && <Hero onAccess={handleAccess} isExiting={isHeroExiting} />}
      {!showHero && (
        <Routes>
          <Route element={<Layout />}>
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
