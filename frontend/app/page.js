'use client'
import { useEffect, useState } from 'react'
import CryptoCard from './components/CryptoCard'

export default function Dashboard() {
  const [coins, setCoins] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [sortBy, setSortBy] = useState('symbol')

  // All frontend calls go through the API Gateway
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    fetch(`${API_URL}/coins?limit=100`)
      .then(res => res.json())
      .then(data => {
        setCoins(Array.isArray(data) ? data : [])
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  const sortedCoins = [...coins].sort((a, b) => {
    switch (sortBy) {
      case 'symbol':
        return a.symbol.localeCompare(b.symbol)
      case 'price':
        return (b.currentPrice || 0) - (a.currentPrice || 0)
      case 'change':
        return (b.priceChange24h || 0) - (a.priceChange24h || 0)
      case 'volume':
        return (b.volume24h || 0) - (a.volume24h || 0)
      case 'volatility':
        return (b.volatility || 0) - (a.volatility || 0)
      default:
        return 0
    }
  })

  const topMovers = [...coins]
    .sort((a, b) => Math.abs(b.priceChange24h || 0) - Math.abs(a.priceChange24h || 0))
    .slice(0, 5)

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="glass-card p-8 text-center">
          <div className="animate-pulse text-2xl font-bold gradient-text">Loading...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="glass-card p-8 text-center">
          <div className="text-red-400 text-xl">Error: {error}</div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen p-6 md:p-8">
      <div className="max-w-7xl mx-auto">
        <div className="gradient-header mb-8">
          <div className="bg-slate-900 rounded-[10px] p-6">
            <h1 className="text-4xl md:text-5xl font-bold gradient-text mb-2">
              Crypto Analytics
            </h1>
            <p className="text-slate-400 text-lg">
              Real-time market data and insights for top cryptocurrencies
            </p>
          </div>
        </div>

        {coins.length === 0 ? (
          <div className="glass-card p-8 text-center">
            <p className="text-slate-300 text-lg mb-2">No data available</p>
            <p className="text-slate-500">
              Run: <code className="bg-slate-800 px-2 py-1 rounded">python main.py</code>
            </p>
          </div>
        ) : (
          <>
            {topMovers.length > 0 && (
              <div className="mb-8">
                <h2 className="text-2xl font-bold text-white mb-4">Top Movers</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                  {topMovers.map(coin => (
                    <div key={coin.symbol} className="glass-card p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-lg font-bold text-white">{coin.symbol}</span>
                        <span className={`price-change text-xs ${coin.priceChange24h >= 0 ? 'up' : 'down'}`}>
                          {coin.priceChange24h >= 0 ? '▲' : '▼'} {Math.abs(coin.priceChange24h)}%
                        </span>
                      </div>
                      <div className="text-xl font-bold text-white">${coin.currentPrice?.toFixed(2)}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-white">All Cryptocurrencies</h2>
              <div className="flex items-center gap-3">
                <label className="text-slate-300 text-sm font-medium">Sort by:</label>
                <select value={sortBy} onChange={e => setSortBy(e.target.value)} className="w-40">
                  <option value="symbol">Name</option>
                  <option value="price">Price</option>
                  <option value="change">24h Change</option>
                  <option value="volume">Volume</option>
                  <option value="volatility">Volatility</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {sortedCoins.map(coin => (
                <CryptoCard key={coin.symbol} coin={coin} />
              ))}
            </div>

            <div className="mt-8 text-center">
              <p className="text-slate-400">Showing {coins.length} cryptocurrencies</p>
            </div>
          </>
        )}
      </div>
    </div>
  )
}


