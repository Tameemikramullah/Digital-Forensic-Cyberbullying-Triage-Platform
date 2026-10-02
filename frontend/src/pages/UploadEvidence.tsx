import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { uploadEvidence } from '../services/evidence'

export default function UploadEvidence() {
  const [sourcePlatform, setSourcePlatform] = useState('')
  const [sourcePostId, setSourcePostId] = useState('')
  const [content, setContent] = useState('')
  const [authorName, setAuthorName] = useState('')
  const [sourceUrl, setSourceUrl] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    setIsSubmitting(true)
    try {
      const formData = new FormData()
      formData.append('source_platform', sourcePlatform)
      formData.append('source_post_id', sourcePostId)
      formData.append('content', content)
      formData.append('acquisition_date', new Date().toISOString())
      if (authorName) formData.append('author_name', authorName)
      if (sourceUrl) formData.append('source_url', sourceUrl)
      if (file) {
        formData.append('file', file)
        formData.append('filename', file.name)
        formData.append('filesize', String(file.size))
      }

      const evidence = await uploadEvidence(formData)
      setSuccess(`Evidence uploaded successfully. Case ID: ${evidence.id}`)
      setTimeout(() => navigate(`/evidence/${evidence.id}`), 1000)
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Upload failed'
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Upload Evidence</h1>
      {error && <p className="mb-4 text-red-600 text-sm">{error}</p>}
      {success && <p className="mb-4 text-green-600 text-sm">{success}</p>}
      <form onSubmit={handleSubmit} className="bg-white p-6 rounded shadow space-y-4">
        <div>
          <label className="block mb-1 font-bold">Source Platform</label>
          <input className="w-full p-2 border rounded" placeholder="e.g. Twitter, Facebook" value={sourcePlatform} onChange={e => setSourcePlatform(e.target.value)} required />
        </div>
        <div>
          <label className="block mb-1 font-bold">Source Post ID</label>
          <input className="w-full p-2 border rounded" placeholder="Post ID or URL" value={sourcePostId} onChange={e => setSourcePostId(e.target.value)} required />
        </div>
        <div>
          <label className="block mb-1 font-bold">Content</label>
          <textarea className="w-full p-2 border rounded" rows={6} placeholder="Paste the post content here" value={content} onChange={e => setContent(e.target.value)} required />
        </div>
        <div>
          <label className="block mb-1 font-bold">Original File (optional)</label>
          <input
            ref={fileInputRef}
            type="file"
            className="w-full p-2 border rounded"
            onChange={e => setFile(e.target.files?.[0] || null)}
          />
          <p className="text-xs text-gray-500 mt-1">Upload the original evidence file (image, screenshot, video, etc.). If provided, the system will hash the original file bytes for forensic integrity.</p>
        </div>
        <div>
          <label className="block mb-1 font-bold">Author Name (optional)</label>
          <input className="w-full p-2 border rounded" placeholder="@username" value={authorName} onChange={e => setAuthorName(e.target.value)} />
        </div>
        <div>
          <label className="block mb-1 font-bold">Source URL (optional)</label>
          <input className="w-full p-2 border rounded" placeholder="https://..." value={sourceUrl} onChange={e => setSourceUrl(e.target.value)} />
        </div>
        <button type="submit" disabled={isSubmitting} className="bg-blue-600 text-white px-4 py-2 rounded disabled:bg-gray-400">
          {isSubmitting ? 'Uploading...' : 'Upload Evidence'}
        </button>
      </form>
    </div>
  )
}
