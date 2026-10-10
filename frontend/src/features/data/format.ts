import type { DataRecord, FieldType } from '../../api/types'

export function formatValue(value: unknown, type: FieldType): string {
  if (value === null || value === undefined) return '—'

  switch (type) {
    case 'datetime':
    case 'date': {
      const date = new Date(String(value))
      if (Number.isNaN(date.getTime())) return String(value)
      return type === 'date' ? date.toLocaleDateString() : date.toLocaleString()
    }
    case 'boolean':
      return value ? '✓' : '–'
    case 'double':
      return typeof value === 'number' ? value.toLocaleString() : String(value)
    default:
      return typeof value === 'object' ? JSON.stringify(value) : String(value)
  }
}

/** SQL models use `id`, MongoDB collections use `_id`. */
export function recordId(record: DataRecord): string | null {
  const id = record.id ?? record._id
  return id === undefined || id === null ? null : String(id)
}
