import type { TokenPair } from './types'

const STORAGE_KEY = 'khaojai.tokens'

// localStorage can throw (private mode, blocked storage), so the in-memory copy is the source of truth.
function readStored(): TokenPair | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as TokenPair) : null
  } catch {
    return null
  }
}

function writeStored(tokens: TokenPair | null): void {
  try {
    if (tokens) localStorage.setItem(STORAGE_KEY, JSON.stringify(tokens))
    else localStorage.removeItem(STORAGE_KEY)
  } catch {
    // Storage unavailable: the session simply won't survive a reload.
  }
}

let current: TokenPair | null = readStored()

export const tokenStore = {
  get: (): TokenPair | null => current,
  set(tokens: TokenPair): void {
    current = tokens
    writeStored(tokens)
  },
  clear(): void {
    current = null
    writeStored(null)
  },
}
