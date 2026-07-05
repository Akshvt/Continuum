import { createContext, useContext, useState, useEffect } from 'react'
import { healthCheck } from '../lib/api'

const BackendContext = createContext(null)

export function BackendProvider({ children }) {
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

  return (
    <BackendContext.Provider value={{ status }}>
      {children}
    </BackendContext.Provider>
  )
}

export function useBackend() {
  const ctx = useContext(BackendContext)
  if (!ctx) throw new Error('useBackend must be used inside <BackendProvider>')
  return ctx
}
