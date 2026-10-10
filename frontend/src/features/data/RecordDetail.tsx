import { useCallback } from 'react'
import { dataApi } from '../../api/endpoints'
import { ErrorMessage } from '../../components/ErrorMessage'
import { useAsync } from '../../hooks'
import { formatValue } from './format'

interface RecordDetailProps {
  slug: string
  id: string
  onClose: () => void
}

export function RecordDetail({ slug, id, onClose }: RecordDetailProps) {
  const load = useCallback(() => dataApi.get(slug, id), [slug, id])
  const result = useAsync(load)

  return (
    <aside className="card detail" aria-label="Record detail">
      <div className="detail-header">
        <h2>Record {id}</h2>
        <button type="button" className="link" onClick={onClose} aria-label="Close detail">
          ×
        </button>
      </div>
      {result.status === 'loading' && <p className="muted">Loading…</p>}
      {result.status === 'error' && <ErrorMessage error={result.error} />}
      {result.status === 'success' && (
        <dl className="details">
          {result.data.data_schema.fields.map((field) => (
            <div key={field.name} className="detail-row">
              <dt>
                {field.name} <span className="muted">{field.type}</span>
              </dt>
              <dd>{formatValue(result.data.data[field.name], field.type)}</dd>
            </div>
          ))}
        </dl>
      )}
    </aside>
  )
}
