import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { getMe } from '../services/api'

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('access_token')
  const [valid, setValid] = useState<boolean | null>(null)

  useEffect(() => {
    if (!token) {
      setValid(false)
      return
    }
    let cancelled = false
    getMe()
      .then(() => {
        if (!cancelled) setValid(true)
      })
      .catch(() => {
        if (!cancelled) {
          localStorage.removeItem('access_token')
          setValid(false)
        }
      })
    return () => {
      cancelled = true
    }
  }, [token])

  if (valid === null) {
    return <div className="p-6">Loading...</div>
  }
  if (!valid) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}
