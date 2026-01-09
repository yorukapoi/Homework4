import { LineChart, Line, ResponsiveContainer } from 'recharts'

export default function Sparkline({ data, color = '#3b82f6' }) {
  if (!data || data.length === 0) {
    return <div className="flex items-center justify-center h-full text-slate-500 text-xs">No data</div>
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data}>
        <Line
          type="monotone"
          dataKey="price"
          stroke={color}
          strokeWidth={2}
          dot={false}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}


