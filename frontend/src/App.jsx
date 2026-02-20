import { useState, useEffect } from 'react'
import { Routes, Route, Link, useLocation } from 'react-router-dom'
import api from './api/client'
import Dashboard from './pages/Dashboard'
import Settings from './pages/Settings'
import ThemeToggle from './components/ThemeToggle'

function App() {
  const [loading, setLoading] = useState(true)
  const location = useLocation();

  // Apply dark class before first paint to prevent flash
  useEffect(() => {
    const stored = localStorage.getItem('theme');
    const isDark = stored ? stored === 'dark' : true;
    document.documentElement.classList.toggle('dark', isDark);
  }, []);

  useEffect(() => {
    // Health check
    api.get('/')
      .then(res => console.log('Backend connected:', res.data))
      .catch(err => console.error('Backend connection error:', err))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-white font-sans transition-colors duration-200">
      {/* Navigation */}
      <nav className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-3 sm:p-4 sticky top-0 z-10 transition-colors duration-200">
        <div className="w-full sm:px-6 flex justify-between items-center">
          <Link to="/" className="text-lg sm:text-xl font-bold bg-gradient-to-r from-blue-500 to-purple-600 dark:from-blue-400 dark:to-purple-500 bg-clip-text text-transparent">
            Personal Trainer
          </Link>
          <div className="flex items-center space-x-3 sm:space-x-4 text-sm font-medium">
            <ThemeToggle />
            <Link to="/" className={`transition ${location.pathname === '/' ? 'text-blue-600 dark:text-blue-400' : 'text-gray-600 dark:text-gray-300 hover:text-blue-500 dark:hover:text-blue-300'}`}>Dashboard</Link>
            <Link to="/settings" className={`transition ${location.pathname === '/settings' ? 'text-blue-600 dark:text-blue-400' : 'text-gray-600 dark:text-gray-300 hover:text-blue-500 dark:hover:text-blue-300'}`}>Settings</Link>
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

