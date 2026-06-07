import { Link, useLocation } from 'react-router-dom'

export default function Navbar() {
  const location = useLocation()

  const navLink = (path, label) => (
    <Link
      to={path}
      className={`px-4 py-2 rounded-lg font-medium transition-all duration-200
        ${location.pathname === path
          ? 'bg-emerald-500 text-white'
          : 'text-gray-400 hover:text-white hover:bg-gray-800'
        }`}
    >
      {label}
    </Link>
  )

  return (
    <nav className="border-b border-gray-800 bg-gray-900 px-6 py-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">♟️</span>
          <span className="text-xl font-bold text-white">Chess RL</span>
          <span className="text-xs bg-emerald-500/20 text-emerald-400 
                           px-2 py-1 rounded-full border border-emerald-500/30">
            AI Learning
          </span>
        </div>
        <div className="flex items-center gap-2">
          {navLink('/', 'Home')}
          {navLink('/game', 'Play')}
          {navLink('/dashboard', 'Dashboard')}
        </div>
      </div>
    </nav>
  )
}