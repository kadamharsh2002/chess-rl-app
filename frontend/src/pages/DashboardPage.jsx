import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, 
         Tooltip, ResponsiveContainer } from 'recharts'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// ── Training Panel Component ───────────────────────────
function TrainingPanel() {
  const [training, setTraining] = useState(null)

  useEffect(() => {
    const fetch_data = async () => {
      try {
        const res = await fetch(`${API_URL}/dashboard/training`)
        const data = await res.json()
        setTraining(data)
      } catch(e) {}
    }
    fetch_data()
    const interval = setInterval(fetch_data, 10000)
    return () => clearInterval(interval)
  }, [])

  if (!training) return (
    <div className="text-gray-500">Loading training stats...</div>
  )

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {/* Epsilon Bar */}
      <div>
        <div className="flex justify-between mb-2">
          <span className="text-gray-400 text-sm">
            Exploration Rate (Epsilon)
          </span>
          <span className="text-white font-bold">
            {training.exploration_pct}%
          </span>
        </div>
        <div className="w-full bg-gray-800 rounded-full h-3">
          <div
            className="bg-purple-500 h-3 rounded-full transition-all"
            style={{ width: `${training.exploration_pct}%` }}
          />
        </div>
        <p className="text-gray-500 text-xs mt-2">
          {training.exploration_pct > 50
            ? "🎲 Still exploring randomly — needs more games"
            : training.exploration_pct > 20
            ? "⚖️ Balancing exploration and strategy"
            : "🧠 Mostly using learned strategy!"}
        </p>

        {/* Loss History Graph */}
        {training.loss_history?.length > 1 && (
          <div className="mt-4">
            <p className="text-gray-400 text-sm mb-2">
              Training Loss Over Games
              <span className="text-xs text-gray-500 ml-2">
                (lower = better!)
              </span>
            </p>
            <ResponsiveContainer width="100%" height={150}>
              <LineChart data={training.loss_history.map((l, i) => ({
                game: i + 1, loss: l
              }))}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151"/>
                <XAxis dataKey="game" stroke="#6b7280" tick={{ fontSize: 10 }}/>
                <YAxis stroke="#6b7280" tick={{ fontSize: 10 }}/>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    fontSize: '12px'
                  }}
                  formatter={(value) => [value.toFixed(4), 'Loss']}
                />
                <Line
                  type="monotone"
                  dataKey="loss"
                  stroke="#a855f7"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Stats Panel */}
      <div className="flex flex-col gap-3">
        {[
          {
            label: 'Total Trained Games',
            value: training.total_games,
            color: 'text-white'
          },
          {
            label: 'AI Wins / Losses / Draws',
            value: `${training.wins} / ${training.losses} / ${training.draws}`,
            color: 'text-white'
          },
          {
            label: 'Current Epsilon',
            value: training.epsilon,
            color: 'text-purple-400'
          },
          {
            label: 'Is Loss Decreasing?',
            value: training.is_learning ? '✅ YES — Learning!' : '❌ Not yet',
            color: training.is_learning ? 'text-emerald-400' : 'text-red-400'
          },
        ].map((item) => (
          <div key={item.label}
               className="flex justify-between bg-gray-800
                          rounded-lg px-4 py-3">
            <span className="text-gray-400 text-sm">{item.label}</span>
            <span className={`font-bold text-sm ${item.color}`}>
              {item.value}
            </span>
          </div>
        ))}

        {/* Reward History */}
        {training.reward_history?.length > 1 && (
          <div className="mt-2">
            <p className="text-gray-400 text-sm mb-2">
              Avg Reward Per Game
              <span className="text-xs text-gray-500 ml-2">
                (higher = better!)
              </span>
            </p>
            <ResponsiveContainer width="100%" height={120}>
              <LineChart data={training.reward_history.map((r, i) => ({
                game: i + 1, reward: r
              }))}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151"/>
                <XAxis dataKey="game" stroke="#6b7280" tick={{ fontSize: 10 }}/>
                <YAxis stroke="#6b7280" tick={{ fontSize: 10 }}/>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    fontSize: '12px'
                  }}
                  formatter={(value) => [value.toFixed(2), 'Reward']}
                />
                <Line
                  type="monotone"
                  dataKey="reward"
                  stroke="#10b981"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  )
}

// ── Main Dashboard Page ────────────────────────────────
export default function DashboardPage() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_URL}/dashboard/stats`)
      const data = await res.json()
      setStats(data)
      setLastUpdated(new Date().toLocaleTimeString())
    } catch (err) {
      console.error('Failed to fetch dashboard stats')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStats()
    const interval = setInterval(fetchStats, 10000)
    return () => clearInterval(interval)
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-gray-400 text-lg">Loading dashboard...</div>
    </div>
  )

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">

      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white">AI Dashboard</h1>
          <p className="text-gray-400 mt-1">
            Real-time AI intelligence tracker
          </p>
        </div>
        <div className="text-right">
          <div className="flex items-center gap-2 text-emerald-400">
            <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"/>
            <span className="text-sm">Live</span>
          </div>
          <p className="text-gray-500 text-xs mt-1">
            Updated: {lastUpdated}
          </p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {[
          { label: 'Total Games', value: stats?.total_games || 0,
            icon: '🎮', color: 'text-blue-400' },
          { label: 'AI Win Rate', value: `${stats?.win_rate || 0}%`,
            icon: '📈', color: 'text-emerald-400' },
          { label: 'AI Version', value: `v${stats?.ai_version || 1}`,
            icon: '🤖', color: 'text-purple-400' },
          { label: 'Active Players', value: stats?.active_players || 0,
            icon: '👥', color: 'text-yellow-400' },
        ].map((stat) => (
          <div key={stat.label}
               className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
            <div className="text-3xl mb-2">{stat.icon}</div>
            <div className={`text-3xl font-bold ${stat.color}`}>
              {stat.value}
            </div>
            <div className="text-gray-500 text-sm mt-1">{stat.label}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">

        {/* Win Rate Graph */}
        <div className="lg:col-span-2 bg-gray-900 border border-gray-800
                        rounded-2xl p-6">
          <h2 className="text-white font-bold text-lg mb-4">
            📈 AI Win Rate Over Time
          </h2>
          {stats?.win_rate_history?.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={stats.win_rate_history}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151"/>
                <XAxis dataKey="game" stroke="#6b7280"
                       label={{ value: 'Games Played',
                                position: 'insideBottom',
                                offset: -5, fill: '#6b7280' }}/>
                <YAxis stroke="#6b7280" domain={[0, 100]}
                       label={{ value: 'Win Rate %', angle: -90,
                                position: 'insideLeft', fill: '#6b7280' }}/>
                <Tooltip
                  contentStyle={{ backgroundColor: '#1f2937',
                                  border: '1px solid #374151',
                                  borderRadius: '8px' }}
                  labelStyle={{ color: '#fff' }}
                  formatter={(value) => [`${value}%`, 'Win Rate']}
                />
                <Line type="monotone" dataKey="win_rate"
                      stroke="#10b981" strokeWidth={2}
                      dot={{ fill: '#10b981', r: 3 }}/>
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-64
                            text-gray-500">
              Play some games to see the AI learning graph! 🎮
            </div>
          )}
        </div>

        {/* Game Stats */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
          <h2 className="text-white font-bold text-lg mb-4">
            🏆 Game Results
          </h2>
          <div className="space-y-4">
            {[
              { label: 'AI Wins', value: stats?.ai_wins || 0,
                color: 'bg-emerald-500', text: 'text-emerald-400' },
              { label: 'Human Wins', value: stats?.ai_losses || 0,
                color: 'bg-blue-500', text: 'text-blue-400' },
              { label: 'Draws', value: stats?.ai_draws || 0,
                color: 'bg-yellow-500', text: 'text-yellow-400' },
            ].map((item) => (
              <div key={item.label}>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-400 text-sm">{item.label}</span>
                  <span className={`font-bold ${item.text}`}>
                    {item.value}
                  </span>
                </div>
                <div className="w-full bg-gray-800 rounded-full h-2">
                  <div
                    className={`${item.color} h-2 rounded-full transition-all`}
                    style={{
                      width: stats?.total_games > 0
                        ? `${(item.value / stats.total_games * 100)}%`
                        : '0%'
                    }}
                  />
                </div>
              </div>
            ))}
            <div className="pt-2 border-t border-gray-800">
              <div className="flex justify-between">
                <span className="text-gray-400 text-sm">Avg Game Length</span>
                <span className="text-white font-bold">
                  {stats?.avg_game_length || 0} moves
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Active Players + Recent Games */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
          <h2 className="text-white font-bold text-lg mb-4">
            👥 Active Players Right Now
          </h2>
          {stats?.active_sessions?.length > 0 ? (
            <div className="space-y-3">
              {stats.active_sessions.map((s, i) => (
                <div key={i}
                     className="flex items-center justify-between
                                bg-gray-800 rounded-xl px-4 py-3">
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 bg-emerald-400
                                    rounded-full animate-pulse"/>
                    <span className="text-white font-medium">
                      {s.player_name}
                    </span>
                  </div>
                  <span className="text-gray-400 text-sm">
                    Move {s.current_move}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-gray-500 text-center py-8">
              No active games right now
            </div>
          )}
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
          <h2 className="text-white font-bold text-lg mb-4">
            🕹️ Recent Games
          </h2>
          <div className="space-y-2">
            {stats?.recent_games?.length > 0 ? (
              stats.recent_games.map((g, i) => (
                <div key={i}
                     className="flex items-center justify-between
                                bg-gray-800 rounded-xl px-4 py-3">
                  <div className="flex items-center gap-3">
                    <span className="text-gray-500 text-sm">#{g.id}</span>
                    <span className={`font-medium text-sm
                      ${g.winner === 'ai' ? 'text-red-400' :
                        g.winner === 'human' ? 'text-emerald-400' :
                        'text-yellow-400'}`}>
                      {g.winner === 'ai' ? '🤖 AI Won' :
                       g.winner === 'human' ? '🎉 You Won' : '🤝 Draw'}
                    </span>
                  </div>
                  <span className="text-gray-500 text-xs">
                    {g.total_moves} moves
                  </span>
                </div>
              ))
            ) : (
              <div className="text-gray-500 text-center py-8">
                No games played yet
              </div>
            )}
          </div>
        </div>
      </div>

      {/* How AI Learns */}
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 mb-6">
        <h2 className="text-white font-bold text-lg mb-4">
          🧠 How the AI is Learning
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { step: '1', title: 'Piece Rewards',
              desc: 'Pawn +1, Knight/Bishop +3, Rook +5, Queen +9. Every capture gives instant reward signal.' },
            { step: '2', title: 'Game Outcome',
              desc: 'Win = +100 points. Loss = -100 points. Draw = +10 points. Biggest learning signal!' },
            { step: '3', title: 'Neural Network Updates',
              desc: 'After every game, PyTorch trains for 50 epochs on all moves. Epsilon decays so AI explores less over time.' },
          ].map((item) => (
            <div key={item.step}
                 className="bg-gray-800 rounded-xl p-4 border border-gray-700">
              <div className="w-8 h-8 bg-emerald-500 rounded-full
                              flex items-center justify-center
                              text-white font-bold mb-3 text-sm">
                {item.step}
              </div>
              <h3 className="text-white font-semibold mb-2">{item.title}</h3>
              <p className="text-gray-400 text-sm">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Training Intelligence Panel */}
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
        <h2 className="text-white font-bold text-lg mb-6">
          🧬 Is The AI Actually Learning?
        </h2>
        <TrainingPanel />
      </div>

    </div>
  )
}