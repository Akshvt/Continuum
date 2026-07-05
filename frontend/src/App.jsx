import { BrowserRouter, Navigate, Routes, Route } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { useAuth } from './context/AuthContext.jsx'
import { healthCheck } from './lib/api.js'
import Home from './pages/Home'
import Login from './pages/Login'
import SignUp from './pages/SignUp'
import Session from './pages/Session'
import AdaptiveLearningPage from './pages/AdaptiveLearningPage'
import ForStudents from './pages/ForStudents'

/** Redirect unauthenticated users to /login; show nothing while auth loads. */
function ProtectedRoute({ children }) {
  const { auth, loading } = useAuth()
  if (loading) return null
  if (!auth) return <Navigate to="/login" replace />
  return children
}

function BackendGate({ children }) {
  const [status, setStatus] = useState('checking') // 'checking', 'ready', 'error'

  useEffect(() => {
    let attempts = 0
    const maxAttempts = 36 // 36 * 2.5s = 90 seconds
    let timeoutId

    const ping = async () => {
      try {
        await healthCheck()
        setStatus('ready')
      } catch (err) {
        attempts++
        if (attempts >= maxAttempts) {
          setStatus('error')
        } else {
          timeoutId = setTimeout(ping, 2500)
        }
      }
    }
    ping()
    return () => clearTimeout(timeoutId)
  }, [])

  if (status === 'checking') {
    return (
      <div style={{
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        height: '100vh', backgroundColor: '#0f172a', color: '#e2e8f0', fontFamily: 'system-ui, sans-serif'
      }}>
        <div style={{
          width: '40px', height: '40px', border: '3px solid rgba(255,255,255,0.1)',
          borderTopColor: '#3b82f6', borderRadius: '50%', animation: 'spin 1s linear infinite'
        }} />
        <h2 style={{ marginTop: '24px', fontWeight: 500 }}>Waking up your tutor...</h2>
        <p style={{ opacity: 0.6, marginTop: '8px', fontSize: '14px' }}>This may take a moment on cold starts.</p>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    )
  }

  if (status === 'error') {
    return (
      <div style={{
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        height: '100vh', backgroundColor: '#0f172a', color: '#e2e8f0', fontFamily: 'system-ui, sans-serif'
      }}>
        <h2 style={{ color: '#ef4444', fontWeight: 500 }}>Backend Unavailable</h2>
        <p style={{ opacity: 0.8, marginTop: '8px', marginBottom: '24px' }}>The tutor service failed to wake up in time.</p>
        <button 
          onClick={() => window.location.reload()}
          style={{
            padding: '10px 20px', backgroundColor: '#3b82f6', color: '#fff', 
            border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 500
          }}
        >
          Retry Connection
        </button>
      </div>
    )
  }

  return children
}

function App() {
  return (
    <BackendGate>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<SignUp />} />
          <Route
            path="/app"
            element={
              <ProtectedRoute>
                <Session />
              </ProtectedRoute>
            }
          />
          <Route path="/adaptive-learning" element={<AdaptiveLearningPage />} />
          <Route path="/for-students" element={<ForStudents />} />
        </Routes>
      </BrowserRouter>
    </BackendGate>
  )
}

export default App
