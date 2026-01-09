import Link from 'next/link'
import Sparkline from './Sparkline'

export default function CryptoCard({ coin }) {
  const isPositive = coin.priceChange24h >= 0

  return (
    <Link href={`/coin/${coin.symbol.toLowerCase()}`}>
      <div className="crypto-card">
        <div className="crypto-card-header">
          <div>
            <div className="crypto-symbol">{coin.symbol}</div>
            <div className="crypto-price">${coin.currentPrice?.toFixed(2)}</div>
          </div>
          <div className={`price-change ${isPositive ? 'up' : 'down'}`}>
            {isPositive ? '▲' : '▼'} {Math.abs(coin.priceChange24h)}%
          </div>
        </div>

        <div className="sparkline-container">
          <Sparkline data={coin.sparkline} color={isPositive ? '#4ade80' : '#f87171'} />
        </div>

        <div className="mt-4 space-y-2">
          <div className="metric-row">
            <span className="metric-label">24h Volume</span>
            <span className="metric-value">${(coin.volume24h / 1000000).toFixed(2)}M</span>
          </div>

          <div className="metric-row">
            <span className="metric-label">Liquidity Score</span>
            <span className="metric-value">{coin.liquidityScore?.toFixed(4)}%</span>
          </div>

          <div className="metric-row">
            <span className="metric-label">7D Range</span>
            <span className="metric-value text-xs">
              ${coin.week7Low?.toFixed(2)} - ${coin.week7High?.toFixed(2)}
            </span>
          </div>

          <div className="metric-row">
            <span className="metric-label">Volatility</span>
            <span className="metric-value">{coin.volatility?.toFixed(2)}</span>
          </div>

          <div className="metric-row">
            <span className="metric-label">ATH / ATL</span>
            <span className="metric-value text-xs">
              ${coin.ath?.toFixed(2)} / ${coin.atl?.toFixed(2)}
            </span>
          </div>
        </div>
      </div>
    </Link>
  )
}


