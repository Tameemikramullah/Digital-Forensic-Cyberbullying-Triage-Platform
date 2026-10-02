import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { login } from '../services/api'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    try {
      const data = await login(email, password)
      localStorage.setItem('access_token', data.access_token)
      navigate('/dashboard')
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Login failed'
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg))
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <form onSubmit={handleSubmit} className="bg-white p-8 rounded shadow-md w-96">
        <h1 className="text-2xl font-bold mb-4">Login</h1>
        {error && <p className="mb-2 text-red-600 text-sm">{error}</p>}
        <input className="w-full mb-2 p-2 border rounded" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
        <input className="w-full mb-4 p-2 border rounded" type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} />
        <button className="w-full bg-blue-600 text-white py-2 rounded" type="submit">Sign In</button>
        <p className="mt-4 text-center text-sm text-gray-600">
          Don&apos;t have an account? <Link to="/register" className="text-blue-600 hover:underline">Register</Link>
        </p>
      </form>
    </div>
  )
}
