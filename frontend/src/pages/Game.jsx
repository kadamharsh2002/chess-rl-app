import { useState, useCallback, useRef } from 'react'
import { Chessboard } from 'react-chessboard'
import { Chess } from 'chess.js'
import { api } from '../utils/api'

export default function Game() {
  const [game, setGame] = useState(new Chess())
  const [sessionId, setSessionId] = useState(null)
  const [status, setStatus] = useState('idle')
  const [message, setMessage] = useState('Start a new game to play!')
  const [moveHistory, setMoveHistory] = useState([])
  const [playerName, setPlayerName] = useState('')
  const [lastAiReward, setLastAiReward] = useState(null)
  const [gameOver, setGameOver] = useState(false)
  const [winner, setWinner] = useState(null)

  // Use refs to avoid stale closures
  const statusRef = useRef('idle')
  const sessionIdRef = useRef(null)
  const gameRef = useRef(new Chess())
  const gameOverRef = useRef(false)

  const updateStatus = (s) => { statusRef.current = s; setStatus(s) }
  const updateGame = (g) => { gameRef.current = g; setGame(g) }
  const updateSessionId = (id) => { sessionIdRef.current = id; setSessionId(id) }
  const updateGameOver = (v) => { gameOverRef.current = v; setGameOver(v) }

  const startGame = async () => {
    updateStatus('loading')
    setMessage('Starting game...')
    try {
      const name = playerName || 'Anonymous'
      const data = await api.startGame(name)
      if (data.session_id) {
        updateSessionId(data.session_id)
        const newGame = new Chess()
        updateGame(newGame)
        setMoveHistory([])
        updateGameOver(false)
        setWinner(null)
        setLastAiReward(null)
        updateStatus('playing')
        setMessage("You play as White ♟️ — make your move!")
      }
    } catch (err) {
      setMessage('Failed to start game. Is the backend running?')
      updateStatus('idle')
    }
  }

  const onDrop = useCallback((sourceSquare, targetSquare) => {
    // Use refs — always get fresh values!
    if (statusRef.current !== 'playing' || gameOverRef.current) return false

    const gameCopy = new Chess(gameRef.current.fen())
    const result = gameCopy.move({
      from: sourceSquare,
      to: targetSquare,
      promotion: 'q'
    })

    if (!result) return false

    // Update board immediately
    updateGame(gameCopy)
    updateStatus('waiting')
    setMessage('AI is thinking... 🤖')

    const moveUci = sourceSquare + targetSquare
    const finalMove = result.promotion ? moveUci + 'q' : moveUci
    const currentSessionId = sessionIdRef.current

    // Make API call
    api.makeMove(currentSessionId, finalMove).then(data => {
      if (data.error) {
        updateGame(new Chess(gameRef.current.fen()))
        setMessage(`Error: ${data.error}`)
        updateStatus('playing')
        return
      }

      updateGame(new Chess(data.fen))

      setMoveHistory(prev => [...prev,
        { move: finalMove, player: 'You', reward: null },
        ...(data.ai_move ? [{
          move: data.ai_move,
          player: 'AI',
          reward: data.ai_reward
        }] : [])
      ])

      if (data.ai_reward !== undefined) {
        setLastAiReward(data.ai_reward)
      }

      if (data.game_over) {
        updateGameOver(true)
        setWinner(data.winner)
        updateStatus('idle')
        setMessage(
          data.winner === 'human' ? '🎉 You won!' :
          data.winner === 'ai' ? '🤖 AI won!' : '🤝 Draw!'
        )
      } else {
        updateStatus('playing')
        setMessage(
          data.is_check
            ? '⚠️ Check! Your king is under attack!'
            : `Your turn! AI played ${data.ai_move}`
        )
      }
    }).catch(() => {
      setMessage('Connection error. Try again.')
      updateStatus('playing')
    })

    return true
  }, [])

  const resetGame = () => {
    const newGame = new Chess()
    updateGame(newGame)
    updateSessionId(null)
    updateStatus('idle')
    setMessage('Start a new game to play!')
    setMoveHistory([])
    updateGameOver(false)
    setWinner(null)
    setLastAiReward(null)
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

        {/* Chess Board */}
        <div className="lg:col-span-2">
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">

            {/* Status Bar */}
            <div className={`mb-4 px-4 py-3 rounded-xl text-center font-medium
              ${gameOver
                ? winner === 'human'
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : winner === 'ai'
                  ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                  : 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
                : status === 'waiting'
                ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                : 'bg-gray-800 text-gray-300 border border-gray-700'
              }`}>
              {message}
            </div>

            {/* Board */}
            <div className="flex justify-center">
              <div style={{ width: '100%', maxWidth: '560px' }}>
                <Chessboard
                  position={game.fen()}
                  onPieceDrop={onDrop}
                  boardOrientation="white"
                  arePiecesDraggable={true}
                  customBoardStyle={{
                    borderRadius: '8px',
                    boxShadow: '0 4px 24px rgba(0,0,0,0.4)'
                  }}
                  customDarkSquareStyle={{ backgroundColor: '#2d4a2d' }}
                  customLightSquareStyle={{ backgroundColor: '#90b890' }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Side Panel */}
        <div className="flex flex-col gap-4">

          {/* Player Setup */}
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
            <h3 className="text-white font-bold mb-3">Player</h3>
            <input
              type="text"
              placeholder="Your name (optional)"
              value={playerName}
              onChange={(e) => setPlayerName(e.target.value)}
              disabled={status === 'playing' || status === 'waiting'}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg
                         px-3 py-2 text-white placeholder-gray-500 mb-3
                         focus:outline-none focus:border-emerald-500
                         disabled:opacity-50"
            />
            {status === 'idle' ? (
              <button
                onClick={startGame}
                className="w-full py-3 bg-emerald-500 hover:bg-emerald-400
                           text-white font-bold rounded-xl transition-all"
              >
                Start Game
              </button>
            ) : (
              <button
                onClick={resetGame}
                className="w-full py-3 bg-gray-700 hover:bg-gray-600
                           text-white font-bold rounded-xl transition-all"
              >
                New Game
              </button>
            )}
          </div>

          {/* AI Reward Display */}
          {lastAiReward !== null && (
            <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
              <h3 className="text-white font-bold mb-2">Last AI Reward</h3>
              <div className={`text-3xl font-bold text-center py-2
                ${lastAiReward > 0 ? 'text-emerald-400' :
                  lastAiReward < 0 ? 'text-red-400' : 'text-gray-400'}`}>
                {lastAiReward > 0 ? '+' : ''}{lastAiReward}
              </div>
              <p className="text-xs text-gray-500 text-center mt-1">
                {lastAiReward > 0 ? 'AI captured a piece! 😈' :
                 lastAiReward < 0 ? 'You captured AI piece! 💪' :
                 'Normal move'}
              </p>
            </div>
          )}

          {/* Move History */}
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 flex-1">
            <h3 className="text-white font-bold mb-3">
              Move History
              <span className="text-gray-500 font-normal text-sm ml-2">
                ({moveHistory.length} moves)
              </span>
            </h3>
            <div className="space-y-1 max-h-64 overflow-y-auto">
              {moveHistory.length === 0 ? (
                <p className="text-gray-500 text-sm">No moves yet</p>
              ) : (
                [...moveHistory].reverse().map((m, i) => (
                  <div key={i}
                       className="flex items-center justify-between
                                  px-3 py-2 rounded-lg bg-gray-800">
                    <span className="text-sm">
                      <span className={m.player === 'You'
                        ? 'text-emerald-400' : 'text-blue-400'}>
                        {m.player}
                      </span>
                      <span className="text-white ml-2 font-mono">
                        {m.move}
                      </span>
                    </span>
                    {m.reward !== null && m.reward !== 0 && (
                      <span className={`text-xs font-bold
                        ${m.reward > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {m.reward > 0 ? '+' : ''}{m.reward}
                      </span>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}