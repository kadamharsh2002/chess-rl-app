const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = {
  // Start a new game
  startGame: async (playerName = 'Anonymous') => {
    const res = await fetch(
      `${API_URL}/game/start?player_name=${playerName}`,
      { method: 'POST' }
    )
    return res.json()
  },

  // Make a move
  makeMove: async (sessionId, moveUci) => {
    const res = await fetch(
      `${API_URL}/game/move?session_id=${sessionId}&move_uci=${moveUci}`,
      { method: 'POST' }
    )
    return res.json()
  },

  // Get game state
  getGameState: async (sessionId) => {
    const res = await fetch(`${API_URL}/game/state/${sessionId}`)
    return res.json()
  },

  // Get dashboard data
  getDashboard: async () => {
    const res = await fetch(`${API_URL}/dashboard`)
    return res.json()
  }
}