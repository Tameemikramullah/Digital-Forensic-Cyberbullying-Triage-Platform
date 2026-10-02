import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { bulkUploadEvidence } from '../services/evidence'

interface BulkItem {
  source_platform: string
  source_post_id: string
  content: string
  acquisition_date: string
  metadata?: { author_name?: string; source_url?: string }
}

export default function BulkUploadEvidence() {
  const [items, setItems] = useState<BulkItem[]>([
    { source_platform: '', source_post_id: '', content: '', acquisition_date: new Date().toISOString() },
  ])
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const updateItem = (index: number, field: keyof BulkItem, value: string) => {
    setItems(prev => prev.map((item, i) => i === index ? { ...item, [field]: value } : item))
  }

  const updateMetadata = (index: number, value: { author_name?: string }) => {
    setItems(prev => prev.map((item, i) => i === index ? { ...item, metadata: value } : item))
  }

  const addRow = () => {
    setItems(prev => [...prev, { source_platform: '', source_post_id: '', content: '', acquisition_date: new Date().toISOString() }])
  }

  const removeRow = (index: number) => {
    setItems(prev => prev.filter((_, i) => i !== index))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    setLoading(true)
    try {
      const validItems = items.filter(item => item.source_platform && item.source_post_id && item.content)
      if (validItems.length === 0) {
        setError('Please fill in at least one complete evidence item.')
        return
      }
      const result = await bulkUploadEvidence(validItems)
      const createdCount = result.created?.length || 0
      const skippedCount = result.skipped?.length || 0
      const errorCount = result.errors?.length || 0
      setSuccess(`Bulk upload completed. Created: ${createdCount}, Skipped: ${skippedCount}, Errors: ${errorCount}`)
      if (createdCount > 0) {
        setTimeout(() => navigate('/evidence'), 1500)
      }
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Bulk upload failed'
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Bulk Evidence Upload</h1>
      {error && <p className="mb-4 text-red-600 text-sm">{error}</p>}
      {success && <p className="mb-4 text-green-600 text-sm">{success}</p>}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="bg-white rounded shadow overflow-hidden">
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left">Source Platform</th>
                <th className="px-4 py-2 text-left">Source Post ID</th>
                <th className="px-4 py-2 text-left">Content</th>
                <th className="px-4 py-2 text-left">Author (optional)</th>
                <th className="px-4 py-2 text-left">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item, index) => (
                <tr key={index} className="border-t">
                  <td className="px-4 py-2">
                    <input className="w-full p-2 border rounded" placeholder="Twitter, Facebook..." value={item.source_platform} onChange={e => updateItem(index, 'source_platform', e.target.value)} required />
                  </td>
                  <td className="px-4 py-2">
                    <input className="w-full p-2 border rounded" placeholder="Post ID" value={item.source_post_id} onChange={e => updateItem(index, 'source_post_id', e.target.value)} required />
                  </td>
                  <td className="px-4 py-2">
                    <textarea className="w-full p-2 border rounded" rows={3} placeholder="Post content" value={item.content} onChange={e => updateItem(index, 'content', e.target.value)} required />
                  </td>
                  <td className="px-4 py-2">
                    <input className="w-full p-2 border rounded" placeholder="@username" value={item.metadata?.author_name || ''} onChange={e => updateMetadata(index, { author_name: e.target.value })} />
                  </td>
                  <td className="px-4 py-2">
                    <button type="button" onClick={() => removeRow(index)} className="text-red-600 hover:underline text-sm">Remove</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={addRow} className="bg-gray-600 text-white px-4 py-2 rounded">Add Row</button>
          <button type="submit" disabled={loading} className="bg-blue-600 text-white px-4 py-2 rounded disabled:bg-gray-400">
            {loading ? 'Uploading...' : `Upload ${items.length} Items`}
          </button>
        </div>
      </form>
    </div>
  )
}