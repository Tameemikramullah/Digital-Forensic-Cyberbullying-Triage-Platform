import { useQuery } from '@tanstack/react-query'
import { getEvidence } from '../services/evidence'
import { Link } from 'react-router-dom'

export default function EvidenceQueue() {
  const { data: evidence = [] } = useQuery({ queryKey: ['evidence'], queryFn: getEvidence })

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Evidence Queue</h1>
        <div className="flex gap-2">
          <Link to="/evidence/upload" className="bg-blue-600 text-white px-4 py-2 rounded">Upload Evidence</Link>
          <Link to="/evidence/bulk-upload" className="bg-gray-600 text-white px-4 py-2 rounded">Bulk Upload</Link>
        </div>
      </div>
      <div className="bg-white rounded shadow overflow-hidden">
        <table className="min-w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2 text-left">Case ID</th>
              <th className="px-4 py-2 text-left">Platform</th>
              <th className="px-4 py-2 text-left">Status</th>
              <th className="px-4 py-2 text-left">Date</th>
              <th className="px-4 py-2 text-left">Actions</th>
            </tr>
          </thead>
          <tbody>
            {evidence.map((item: any) => (
              <tr key={item.id} className="border-t">
                <td className="px-4 py-2">{item.id}</td>
                <td className="px-4 py-2">{item.source_platform}</td>
                <td className="px-4 py-2">
                  <span className={`px-2 py-1 rounded text-xs ${item.status === 'PENDING' ? 'bg-yellow-100 text-yellow-800' : item.status === 'TRIAGED' ? 'bg-orange-100 text-orange-800' : item.status === 'REVIEWED' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                    {item.status}
                  </span>
                </td>
                <td className="px-4 py-2">{new Date(item.created_at).toLocaleDateString()}</td>
                <td className="px-4 py-2">
                  <Link to={`/evidence/${item.id}`} className="text-blue-600 hover:underline mr-2">View</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
