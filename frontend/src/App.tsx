import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './auth/AuthContext'
import { RequireAuth } from './auth/RequireAuth'
import { Footer } from './components/Footer'
import { NavBar } from './components/NavBar'
import { DataPage } from './pages/DataPage'
import { LoginPage } from './pages/LoginPage'
import { ProfilePage } from './pages/ProfilePage'
import { RegisterPage } from './pages/RegisterPage'

export function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <NavBar />
        <main className="container">
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/profile" element={<RequireAuth><ProfilePage /></RequireAuth>} />
            <Route path="/data" element={<RequireAuth><DataPage /></RequireAuth>} />
            <Route path="*" element={<Navigate to="/profile" replace />} />
          </Routes>
        </main>
        <Footer />
      </AuthProvider>
    </BrowserRouter>
  )
}
