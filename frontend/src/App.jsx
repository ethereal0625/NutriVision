import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar.jsx'
import Footer from './components/Footer.jsx'
import Home from './pages/Home.jsx'
import Login from './pages/Login.jsx'
import Register from './pages/Register.jsx'
import Analyze from './pages/Analyze.jsx'
import Plan from './pages/Plan.jsx'
import History from './pages/History.jsx'
import About from './pages/About.jsx'
import Tips from './pages/Tips.jsx'
import Profile from './pages/Profile.jsx'

export default function App() {
  return (
    <div className="min-h-screen flex flex-col bg-mesh">
      <Navbar />
      <main className="flex-1 pb-16 md:pb-0">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/analyze" element={<Analyze />} />
          <Route path="/plan" element={<Plan />} />
          <Route path="/history" element={<History />} />
          <Route path="/about" element={<About />} />
          <Route path="/tips" element={<Tips />} />
          <Route path="/profile" element={<Profile />} />
        </Routes>
      </main>
      <Footer />
    </div>
  )
}
