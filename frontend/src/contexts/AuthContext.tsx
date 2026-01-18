import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

interface AuthContextType {
  token: string | null
  username: string | null
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null)
  const [username, setUsername] = useState<string | null>(null)

  useEffect(() => {
    // Load token from localStorage on mount
    const savedToken = localStorage.getItem('auth_token')
    const savedUsername = localStorage.getItem('username')
    if (savedToken) {
      setToken(savedToken)
      setUsername(savedUsername)
    }
  }, [])

  const login = async (username: string, password: string) => {
    try {
      // Try to login first
      const loginResponse = await fetch('http://localhost:8000/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      })

      if (loginResponse.ok) {
        const data = await loginResponse.json()
        setToken(data.access_token)
        setUsername(username)
        localStorage.setItem('auth_token', data.access_token)
        localStorage.setItem('username', username)
        return
      }

      // If login fails, try to register
      const registerResponse = await fetch('http://localhost:8000/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username,
          password,
          email: `${username}@example.com`,
          full_name: username
        })
      })

      if (!registerResponse.ok) {
        throw new Error('Failed to register')
      }

      // After successful registration, login
      const retryLoginResponse = await fetch('http://localhost:8000/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      })

      if (!retryLoginResponse.ok) {
        throw new Error('Failed to login after registration')
      }

      const data = await retryLoginResponse.json()
      setToken(data.access_token)
      setUsername(username)
      localStorage.setItem('auth_token', data.access_token)
      localStorage.setItem('username', username)
    } catch (error) {
      console.error('Authentication error:', error)
      throw error
    }
  }

  const logout = () => {
    setToken(null)
    setUsername(null)
    localStorage.removeItem('auth_token')
    localStorage.removeItem('username')
  }

  return (
    <AuthContext.Provider value={{
      token,
      username,
      login,
      logout,
      isAuthenticated: !!token
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
