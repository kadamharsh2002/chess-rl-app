import { Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Game from './pages/Game'
import DashboardPage from './pages/DashboardPage'
import Navbar from './components/Navbar'

function App() {
  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/game" element={<Game />} />
        <Route path="/dashboard" element={<DashboardPage />} />
      </Routes>
    </div>
  )
}

export default App