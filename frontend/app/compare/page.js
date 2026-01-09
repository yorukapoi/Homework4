'use client'
import { useEffect, useState, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

function CompareContent() {
  const searchParams = useSearchParams()
  const [coin1, setCoin1] = useState(searchParams?.get('coin1') || '')
  const [coin2, setCoin2] = useState('')
  const [coins, setCoins] = useState([])
  const [data, setData] = useState(null)
  const [coin1Details, setCoin1Details] = useState(null)
  const [coin2Details, setCoin2Details] = useState(null)
  const [loading, setLoading] = useState(false)
  const [days, setDays] = useState(365)

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    fetch(`${API_URL}/coins?limit=100`)
      .then(r => r.json())
      .then(data => setCoins(data))
      .catch(console.error)
  }, [])

  const handleCompare = async () => {
    if (!coin1 || !coin2) return alert('Select both coins')
    if (coin1 === coin2) return alert('Select different coins')

    setLoading(true)
    try {
      const [compareResult, details1, details2] = await Promise.all([
        fetch(`${API_URL}/compare?coin1=${coin1}&coin2=${coin2}&days=${days}`).then(r => r.json()),
        fetch(`${API_URL}/coins/${coin1}`).then(r => r.json()),
        fetch(`${API_URL}/coins/${coin2}`).then(r => r.json())
      ])

      const merged = []
      const dates = new Set()

      compareResult.coin1.data.forEach(d => dates.add(d.date))
      compareResult.coin2.data.forEach(d => dates.add(d.date))

      Array.from(dates).sort().forEach(date => {
        const d1 = compareResult.coin1.data.find(d => d.date === date)
        const d2 = compareResult.coin2.data.find(d => d.date === date)
        merged.push({
          date,
          [compareResult.coin1.symbol]: d1?.close || null,
          [compareResult.coin2.symbol]: d2?.close || null
        })
      })

      setData({
        coin1: compareResult.coin1.symbol,
        coin2: compareResult.coin2.symbol,
        data: merged
      })
      setCoin1Details(details1)
      setCoin2Details(details2)
    } catch (err) {
      alert(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen p-6 md:p-8">
      <div className="max-w-7xl mx-auto">
        <Link href="/" className="text-blue-400 hover:text-blue-300 mb-6 inline-flex items-center gap-2 transition-colors">
          <span>←</span> Back to Dashboard
        </Link>

        <div className="gradient-header mb-8">
          <div className="bg-slate-900 rounded-[10px] p-6">
            <h1 className="text-4xl md:text-5xl font-bold gradient-text mb-2">
              Compare Cryptocurrencies
            </h1>
            <p className="text-slate-400 text-lg">
              Side-by-side analysis of crypto assets
            </p>
          </div>
        </div>

        <div className="glass-card mb-8 p-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block mb-2 text-sm font-medium text-slate-300">Coin 1</label>
              <select value={coin1} onChange={e => setCoin1(e.target.value)} className="w-full">
                <option value="">Select</option>
                {coins.map(c => <option key={c.symbol} value={c.symbol}>{c.symbol}</option>)}
              </select>
            </div>
            <div>
              <label className="block mb-2 text-sm font-medium text-slate-300">Coin 2</label>
              <select value={coin2} onChange={e => setCoin2(e.target.value)} className="w-full">
                <option value="">Select</option>
                {coins.map(c => <option key={c.symbol} value={c.symbol}>{c.symbol}</option>)}
              </select>
            </div>
            <div>
              <label className="block mb-2 text-sm font-medium text-slate-300">Period</label>
              <select value={days} onChange={e => setDays(Number(e.target.value))} className="w-full">
                <option value={30}>30 Days</option>
                <option value={90}>90 Days</option>
                <option value={365}>1 Year</option>
              </select>
            </div>
            <div className="flex items-end">
              <button onClick={handleCompare} disabled={loading} className="w-full">
                {loading ? 'Loading...' : 'Compare'}
              </button>
            </div>
          </div>
        </div>

        {data && coin1Details && coin2Details && (
          <>
            <div className="glass-card mb-8 p-6">
              <h3 className="text-2xl font-bold text-white mb-6">{data.coin1} vs {data.coin2}</h3>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={data.data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
                  <XAxis
                    dataKey="date"
                    tick={{ fill: '#94a3b8', fontSize: 12 }}
                    interval={Math.floor(data.data.length / 8)}
                  />
                  <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'rgba(30, 41, 59, 0.95)',
                      border: '1px solid rgba(148, 163, 184, 0.2)',
                      borderRadius: '8px',
                      color: '#e2e8f0'
                    }}
                  />
                  <Legend wrapperStyle={{ color: '#e2e8f0' }} />
                  <Line type="monotone" dataKey={data.coin1} stroke="#3b82f6" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey={data.coin2} stroke="#ec4899" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            {/* The rest of the comparison UI is identical to Homework 3 and omitted here for brevity */}
          </>
        )}
      </div>
    </div>
  )
}

export default function Compare() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <div className="glass-card p-8 text-center">
          <div className="animate-pulse text-2xl font-bold gradient-text">Loading...</div>
        </div>
      </div>
    }>
      <CompareContent />
    </Suspense>
  )
}


