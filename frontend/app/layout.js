import './globals.css'

export const metadata = {
  title: 'Crypto Analytics - HW4',
  description: 'Cryptocurrency analytics with microservices and FastAPI gateway',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <nav className="bg-gray-900 text-white p-4">
          <div className="container mx-auto flex justify-between items-center">
            <h1 className="text-2xl font-bold">💰 Crypto Analytics</h1>
            <div className="space-x-4">
              <a href="/" className="hover:text-blue-400">Dashboard</a>
              <a href="/compare" className="hover:text-blue-400">Compare</a>
            </div>
          </div>
        </nav>
        <main className="container mx-auto p-6">
          {children}
        </main>
        <footer className="bg-gray-900 text-white text-center p-4 mt-8">
          <p>HW4 Crypto Analytics • FastAPI Microservices + Next.js + SQLite</p>
        </footer>
      </body>
    </html>
  )
}


