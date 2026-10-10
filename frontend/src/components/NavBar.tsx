import { NavLink } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export function NavBar() {
  const { state } = useAuth()

  return (
    <header className="navbar">
      <span className="brand">Khaojai</span>
      {state.status === 'authenticated' && (
        <>
          <nav aria-label="Main">
            <NavLink to="/profile">Profile</NavLink>
            <NavLink to="/data">Data</NavLink>
          </nav>
          <span className="navbar-user" title={state.user.email}>
            {state.user.email}
          </span>
        </>
      )}
    </header>
  )
}
