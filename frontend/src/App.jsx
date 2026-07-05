import { BrowserRouter, Navigate, Routes, Route, useLocation } from 'react-router-dom'
import { useAuth } from './context/AuthContext.jsx'
import { useBackend } from './context/BackendContext.jsx'
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
  const { status } = useBackend()
  const location = useLocation()
  
  // Only block these protected/interactive routes
  const isGated = ['/login', '/signup', '/app'].includes(location.pathname)

  if (!isGated) return children

  if (status === 'checking') {
    return (
      <div style={{
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        height: '100vh', backgroundColor: 'var(--paper)', color: 'var(--ink)', fontFamily: 'var(--font-sans)'
      }}>
        <div style={{
          width: '40px', height: '40px', border: '3px solid var(--line)',
          borderTopColor: 'var(--ink)', borderRadius: '50%', animation: 'spin 1s linear infinite'
        }} />
        <h2 style={{ marginTop: '24px', fontWeight: 500, letterSpacing: '-0.02em' }}>Waking up your tutor...</h2>
        <p style={{ opacity: 0.6, marginTop: '4px', fontSize: '13px' }}>(backend)</p>
        <p style={{ opacity: 0.6, marginTop: '12px', fontSize: '14px' }}>This may take a moment on cold starts.</p>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    )
  }

  if (status === 'error') {
    return (
      <div style={{
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        height: '100vh', backgroundColor: 'var(--paper)', color: 'var(--ink)', fontFamily: 'var(--font-sans)'
      }}>
        <h2 style={{ color: '#ef4444', fontWeight: 500 }}>Backend Unavailable</h2>
        <p style={{ opacity: 0.8, marginTop: '8px', marginBottom: '24px' }}>The tutor service failed to wake up in time.</p>
        <button 
          onClick={() => window.location.reload()}
          style={{
            padding: '10px 20px', backgroundColor: 'var(--ink)', color: 'var(--paper)', 
            border: 'none', borderRadius: '999px', cursor: 'pointer', fontWeight: 500
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
    <BrowserRouter>
      <BackendGate>
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
      </BackendGate>
    </BrowserRouter>
  )
}

export default App
