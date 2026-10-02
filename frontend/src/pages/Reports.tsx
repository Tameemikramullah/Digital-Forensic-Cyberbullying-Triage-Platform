import { useQuery } from '@tanstack/react-query'
import { getEvidence } from '../services/evidence'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function Reports() {
  const { data: evidence = [] } = useQuery({ queryKey: ['evidence'], queryFn: getEvidence })

  const statusCounts = evidence.reduce((acc: any, item: any) => {
    acc[item.status] = (acc[item.status] || 0) + 1
    return acc
  }, {})

  const chartData = Object.entries(statusCounts).map(([name, value]) => ({ name, value }))

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Reports</h1>
      <div className="bg-white p-6 rounded shadow">
        <h2 className="text-xl font-bold mb-4">Evidence by Status</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="value" fill="#3b82f6" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
