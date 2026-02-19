import { useState, useEffect } from 'react'
import { Routes, Route, Link, useLocation } from 'react-router-dom'
import api from './api/client'
import Dashboard from './pages/Dashboard'
import Settings from './pages/Settings'

function App() {
  const [loading, setLoading] = useState(true)
  const location = useLocation();

  useEffect(() => {
    // Health check
    api.get('/')
      .then(res => console.log('Backend connected:', res.data))
      .catch(err => console.error('Backend connection error:', err))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="min-h-screen bg-gray-900 text-white font-sans">
      {/* Navigation */}
      <nav className="bg-gray-800 border-b border-gray-700 p-4 sticky top-0 z-10">
        <div className="w-full px-6 flex justify-between items-center">
          <Link to="/" className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            Personal Trainer
          </Link>
          <div className="space-x-4 text-sm font-medium">
            <Link to="/" className={`transition ${location.pathname === '/' ? 'text-blue-400' : 'text-gray-300 hover:text-blue-300'}`}>Dashboard</Link>
            <Link to="/settings" className={`transition ${location.pathname === '/settings' ? 'text-blue-400' : 'text-gray-300 hover:text-blue-300'}`}>Settings</Link>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="w-full p-4 md:p-6">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
