import { DOCS_URL } from '../api/client'
import { getAppInfo } from '../api/endpoints'
import { useAsync } from '../hooks'

export function Footer() {
  const info = useAsync(getAppInfo)

  return (
    <footer className="footer muted">
      {info.status === 'success' && `API: ${info.data.name} v${info.data.version}`}
      {info.status === 'error' && 'API unavailable'}
      {' · '}
      <a href={DOCS_URL}>API docs (Swagger)</a>
    </footer>
  )
}
