import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { register } from '../services/api'

export default function Register() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState('INVESTIGATOR')
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    try {
      await register(email, password, role)
      navigate('/login')
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Registration failed'
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg))
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <form onSubmit={handleSubmit} className="bg-white p-8 rounded shadow-md w-96">
        <h1 className="text-2xl font-bold mb-4">Register</h1>
        {error && <p className="mb-2 text-red-600 text-sm">{error}</p>}
        <input className="w-full mb-2 p-2 border rounded" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
        <input className="w-full mb-2 p-2 border rounded" type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} />
        <select className="w-full mb-4 p-2 border rounded" value={role} onChange={e => setRole(e.target.value)}>
          <option value="INVESTIGATOR">Investigator</option>
          <option value="REVIEWER">Reviewer</option>
          <option value="ADMIN">Admin</option>
        </select>
        <button className="w-full bg-green-600 text-white py-2 rounded" type="submit">Create Account</button>
        <p className="mt-4 text-center text-sm text-gray-600">
          Already have an account? <Link to="/login" className="text-blue-600 hover:underline">Login</Link>
        </p>
      </form>
    </div>
  )
}
