'use client'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import CandlestickChart from '../../components/CandlestickChart'

export default function CoinDetail() {
  const params = useParams()
  const coinId = params?.id?.toUpperCase()

  const [details, setDetails] = useState(null)
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [days, setDays] = useState(365)
  const [activeTab, setActiveTab] = useState('overview')
  const [technicalData, setTechnicalData] = useState(null)
  const [predictionData, setPredictionData] = useState(null)
  const [onchainData, setOnchainData] = useState(null)
  const [timeframe, setTimeframe] = useState('1m')
  const [loadingTA, setLoadingTA] = useState(false)
  const [loadingPred, setLoadingPred] = useState(false)
  const [loadingOnchain, setLoadingOnchain] = useState(false)

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    if (!coinId) return

    Promise.all([
      fetch(`${API_URL}/coins/${coinId}`).then(r => r.json()),
      fetch(`${API_URL}/coins/${coinId}/history?days=${days}`).then(r => r.json())
    ])
    .then(([detailsData, historyData]) => {
      setDetails(detailsData)
      setHistory(historyData.data || [])
      setLoading(false)
    })
    .catch(err => {
      console.error(err)
      setLoading(false)
    })
  }, [coinId, days])

  useEffect(() => {
    if (!coinId || activeTab !== 'technical') return
    setLoadingTA(true)
    fetch(`${API_URL}/coins/${coinId}/technical?timeframe=${timeframe}`)
      .then(r => r.json())
      .then(data => {
        setTechnicalData(data)
        setLoadingTA(false)
      })
      .catch(err => {
        console.error(err)
        setLoadingTA(false)
      })
  }, [coinId, activeTab, timeframe])

  useEffect(() => {
    if (!coinId || activeTab !== 'prediction') return
    setLoadingPred(true)
    fetch(`${API_URL}/coins/${coinId}/predict?lookback=30&epochs=15`)
      .then(r => r.json())
      .then(data => {
        setPredictionData(data)
        setLoadingPred(false)
      })
      .catch(err => {
        console.error(err)
        setLoadingPred(false)
      })
  }, [coinId, activeTab])

  useEffect(() => {
    if (!coinId || activeTab !== 'onchain') return
    setLoadingOnchain(true)
    fetch(`${API_URL}/coins/${coinId}/onchain-sentiment`)
      .then(r => r.json())
      .then(data => {
        setOnchainData(data)
        setLoadingOnchain(false)
      })
      .catch(err => {
        console.error(err)
        setLoadingOnchain(false)
      })
  }, [coinId, activeTab])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="glass-card p-8 text-center">
          <div className="animate-pulse text-2xl font-bold gradient-text">Loading...</div>
        </div>
      </div>
    )
  }

  if (!details) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="glass-card p-8 text-center">
          <div className="text-red-400 text-xl">Coin not found</div>
        </div>
      </div>
    )
  }

  const isPositive = details.priceChange24h >= 0

  return (
    <div className="min-h-screen p-6 md:p-8">
      <div className="max-w-7xl mx-auto">
        <Link href="/" className="text-blue-400 hover:text-blue-300 mb-6 inline-flex items-center gap-2 transition-colors">
          <span>←</span> Back to Dashboard
        </Link>

        <div className="gradient-header mb-8">
          <div className="bg-slate-900 rounded-[10px] p-6">
            <div className="flex items-start justify-between flex-wrap gap-4">
              <div>
                <h1 className="text-4xl md:text-5xl font-bold text-white mb-2">{details.symbol}</h1>
                <div className="flex items-center gap-3">
                  <span className="text-3xl font-bold text-white">${details.currentPrice?.toFixed(2)}</span>
                  <span className={`price-change ${isPositive ? 'up' : 'down'} text-lg`}>
                    {isPositive ? '▲' : '▼'} {Math.abs(details.priceChange24h)}%
                  </span>
                </div>
              </div>
              <Link href={`/compare?coin1=${details.symbol}`}>
                <button>Compare Coin</button>
              </Link>
            </div>
          </div>
        </div>

        {/* KPI cards and tabbed analytics UI are identical to Homework 3 implementation */}
        {/* They are omitted for brevity but rely on the same /coins, /history, /technical, /predict, /onchain-sentiment endpoints. */}

        {history.length > 0 && (
          <div className="glass-card p-6">
            <h3 className="text-2xl font-bold text-white mb-4">Recent Price Action</h3>
            <CandlestickChart data={history.slice(-60)} />
          </div>
        )}
      </div>
    </div>
  )
}


