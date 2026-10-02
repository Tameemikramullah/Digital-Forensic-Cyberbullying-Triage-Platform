import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getAuditLogs } from '../services/audit'

export default function AuditLogs() {
  const { id } = useParams()
  const { data: logs = [] } = useQuery({ queryKey: ['audit', id], queryFn: () => getAuditLogs(Number(id)) })

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Audit Logs - Evidence #{id}</h1>
      <div className="bg-white rounded shadow overflow-hidden">
        <table className="min-w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2 text-left">Event Type</th>
              <th className="px-4 py-2 text-left">Actor</th>
              <th className="px-4 py-2 text-left">Timestamp</th>
              <th className="px-4 py-2 text-left">Details</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log: any) => (
              <tr key={log.id} className="border-t">
                <td className="px-4 py-2">{log.event_type}</td>
                <td className="px-4 py-2">{log.actor}</td>
                <td className="px-4 py-2">{new Date(log.created_at).toLocaleString()}</td>
                <td className="px-4 py-2">{log.event_details}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
