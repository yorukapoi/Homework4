import { ComposedChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function CandlestickChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-[400px] text-slate-500">
        No data available
      </div>
    )
  }

  const candleData = data.map(d => ({
    date: d.date,
    open: d.open,
    close: d.close,
    high: d.high,
    low: d.low,
    fill: d.close >= d.open ? '#4ade80' : '#f87171',
    candleHigh: Math.max(d.open, d.close),
    candleLow: Math.min(d.open, d.close),
  }))

  const CustomCandlestick = (props) => {
    const { x, width, fill, payload } = props

    if (!payload) return null

    const wickX = x + width / 2
    const wickWidth = 2
    const candleWidth = width * 0.6
    const candleX = x + (width - candleWidth) / 2

    return (
      <g>
        <line
          x1={wickX}
          y1={props.y}
          x2={wickX}
          y2={props.y + props.height}
          stroke={fill}
          strokeWidth={wickWidth}
        />
        <rect
          x={candleX}
          y={props.y}
          width={candleWidth}
          height={props.height || 1}
          fill={fill}
          stroke={fill}
        />
      </g>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={400}>
      <ComposedChart data={candleData}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
        <XAxis
          dataKey="date"
          tick={{ fill: '#94a3b8', fontSize: 12 }}
          interval={Math.floor(candleData.length / 8)}
        />
        <YAxis
          domain={['dataMin', 'dataMax']}
          tick={{ fill: '#94a3b8', fontSize: 12 }}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: 'rgba(30, 41, 59, 0.95)',
            border: '1px solid rgba(148, 163, 184, 0.2)',
            borderRadius: '8px',
            color: '#e2e8f0'
          }}
          formatter={(value, name) => {
            if (name === 'candleHigh' || name === 'candleLow') return null
            return [`$${parseFloat(value).toFixed(2)}`, name.toUpperCase()]
          }}
        />
        <Bar
          dataKey="candleLow"
          fill="#4ade80"
          shape={<CustomCandlestick />}
        />
      </ComposedChart>
    </ResponsiveContainer>
  )
}


