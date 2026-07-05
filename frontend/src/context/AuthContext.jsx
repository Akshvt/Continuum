import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { authMe } from '../lib/api'

const STORAGE_KEY = 'continuum_auth'

const AuthContext = createContext(null)

/**
 * Stores { student_id, email } in localStorage so the identity persists
 * across browser refreshes.  On mount it validates the stored credential
 * against /api/auth/me; if the server rejects it the stored data is cleared.
 */
export function AuthProvider({ children }) {
  const [auth, setAuth] = useState(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      return raw ? JSON.parse(raw) : null
    } catch {
      return null
    }
  })

  const [loading, setLoading] = useState(true)

  // Validate stored credential on page load
  useEffect(() => {
    if (!auth?.student_id) {
      setLoading(false)
      return
    }

    authMe(auth.student_id)
      .catch(() => {
        // Stored credential rejected — wipe it so the user is redirected to login
        localStorage.removeItem(STORAGE_KEY)
        setAuth(null)
      })
      .finally(() => setLoading(false))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const login = useCallback((authData) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(authData))
    setAuth(authData)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY)
    setAuth(null)
  }, [])

  return (
    <AuthContext.Provider value={{ auth, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

/** @returns {{ auth: {student_id: string, email: string}|null, login: Function, logout: Function, loading: boolean }} */
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
