import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { AuthProvider } from './context/AuthContext.jsx'
import { BackendProvider } from './context/BackendContext.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BackendProvider>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BackendProvider>
  </StrictMode>,
)
