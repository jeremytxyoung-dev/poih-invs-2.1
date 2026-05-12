import axios from 'axios'
import { useQuery } from 'react-query'

const venueId = '00000000-0000-0000-0000-000000000001'

export default function Dashboard() {
  const { data, isLoading } = useQuery(['dashboard', venueId], async () => {
    const response = await axios.get(`/api/v1/reports/dashboard/${venueId}`)
    return response.data
  })

  if (isLoading) {
    return <div className="p-4 pb-20">Loading dashboard...</div>
  }

  return (
    <div className="space-y-4 p-4 pb-20">
      <h1 className="text-2xl font-semibold">Dashboard</h1>

      <div className="grid grid-cols-2 gap-4">
        <div className="card border-gray-700">
          <p className="text-sm text-gray-400">Latest Variance</p>
          <p className="mt-2 text-2xl font-bold">${Number(data?.latest_variance || 0).toFixed(2)}</p>
        </div>
        <div className="card border-gray-700">
          <p className="text-sm text-gray-400">Flagged Items</p>
          <p className="mt-2 text-2xl font-bold">{data?.flagged_count || 0}</p>
        </div>
      </div>

      <section className="card border-gray-700">
        <h2 className="mb-3 text-lg font-semibold">Shrinkage Hotspots</h2>
        <div className="space-y-3">
          {(data?.shrinkage_hotspots || []).map((item) => (
            <div key={item.name} className="flex items-center justify-between border-b border-gray-700 pb-2 last:border-b-0">
              <div>
                <p className="font-medium">{item.name}</p>
                <p className="text-sm text-gray-400">{item.category}</p>
              </div>
              <p className="font-semibold text-red-400">${Math.abs(item.loss_amount).toFixed(2)}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="card border-gray-700">
        <h2 className="mb-3 text-lg font-semibold">Top Movers</h2>
        <div className="space-y-3">
          {(data?.top_movers || []).map((item) => (
            <div key={item.name} className="flex items-center justify-between border-b border-gray-700 pb-2 last:border-b-0">
              <div>
                <p className="font-medium">{item.name}</p>
                <p className="text-sm text-gray-400">Qty {item.qty}</p>
              </div>
              <p className="font-semibold text-green-400">${Number(item.revenue || 0).toFixed(2)}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
