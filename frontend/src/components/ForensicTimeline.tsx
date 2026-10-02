import { useMemo } from 'react'

interface TimelineEntry {
  id: number
  created_at: string
  event_type: string
  actor: string
  event_details?: string
}

interface ForensicTimelineProps {
  events: TimelineEntry[]
}

export default function ForensicTimeline({ events }: ForensicTimelineProps) {
  const sorted = useMemo(() => {
    return [...events].sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
  }, [events])

  return (
    <div className="relative border-l-2 border-gray-200 ml-4">
      {sorted.map((event) => (
        <div key={event.id} className="mb-6 ml-6">
          <div className="absolute -left-2 w-4 h-4 rounded-full bg-blue-500 border-4 border-white" />
          <div className="bg-white p-4 rounded shadow">
            <p className="text-xs text-gray-500">{new Date(event.created_at).toLocaleString()}</p>
            <p className="font-bold">{event.event_type}</p>
            <p className="text-sm text-gray-700">Actor: {event.actor}</p>
            {event.event_details && (
              <pre className="text-xs bg-gray-100 p-2 rounded mt-1 overflow-auto">
                {typeof event.event_details === 'string' ? event.event_details : JSON.stringify(event.event_details, null, 2)}
              </pre>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
