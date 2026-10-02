import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { createReview } from '../services/reviews'

export default function ReviewPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [decision, setDecision] = useState('')
  const [notes, setNotes] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await createReview(Number(id), { decision, notes })
      navigate(`/evidence/${id}`)
    } catch (err) {
      alert('Review failed')
    }
  }

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Review Evidence #{id}</h1>
      <form onSubmit={handleSubmit} className="bg-white p-6 rounded shadow max-w-lg">
        <div className="mb-4">
          <label className="block mb-2 font-bold">Decision</label>
          <select className="w-full p-2 border rounded" value={decision} onChange={e => setDecision(e.target.value)} required>
            <option value="">Select</option>
            <option value="CONFIRMED">Confirmed</option>
            <option value="REJECTED">Rejected</option>
            <option value="NEEDS_MORE_REVIEW">Needs More Review</option>
          </select>
        </div>
        <div className="mb-4">
          <label className="block mb-2 font-bold">Notes</label>
          <textarea className="w-full p-2 border rounded" rows={4} value={notes} onChange={e => setNotes(e.target.value)} />
        </div>
        <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded">Submit Review</button>
      </form>
    </div>
  )
}
