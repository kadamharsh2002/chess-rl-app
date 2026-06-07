import { useNavigate } from 'react-router-dom'

export default function Home() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col items-center 
                    justify-center px-6 text-center">
      {/* Hero */}
      <div className="mb-8">
        <span className="text-8xl mb-6 block">♟️</span>
        <h1 className="text-5xl font-bold text-white mb-4">
          Chess <span className="text-emerald-400">RL</span>
        </h1>
        <p className="text-xl text-gray-400 max-w-lg mx-auto">
          Play against an AI that learns from every game. 
          The more you play, the smarter it gets.
        </p>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-3 gap-6 mb-10 w-full max-w-lg">
        {[
          { icon: '🧠', label: 'Self Learning', desc: 'Improves after every game' },
          { icon: '📊', label: 'Live Dashboard', desc: 'Track AI intelligence' },
          { icon: '⚡', label: 'Real-time', desc: 'Instant AI responses' },
        ].map((item) => (
          <div key={item.label}
               className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="text-3xl mb-2">{item.icon}</div>
            <div className="text-sm font-semibold text-white">{item.label}</div>
            <div className="text-xs text-gray-500 mt-1">{item.desc}</div>
          </div>
        ))}
      </div>

      {/* Buttons */}
      <div className="flex gap-4">
        <button
          onClick={() => navigate('/game')}
          className="px-8 py-4 bg-emerald-500 hover:bg-emerald-400 
                     text-white font-bold rounded-xl text-lg
                     transition-all duration-200 shadow-lg 
                     shadow-emerald-500/25 hover:shadow-emerald-500/40"
        >
          Play Now
        </button>
        <button
          onClick={() => navigate('/dashboard')}
          className="px-8 py-4 bg-gray-800 hover:bg-gray-700
                     text-white font-bold rounded-xl text-lg
                     transition-all duration-200 border border-gray-700"
        >
          View Dashboard
        </button>
      </div>
    </div>
  )
}