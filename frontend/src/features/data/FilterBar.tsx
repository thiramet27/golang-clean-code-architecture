import { useState, type FormEvent } from 'react'
import type { SchemaField } from '../../api/types'

interface FilterBarProps {
  fields: SchemaField[]
  filters: Record<string, string>
  onChange: (filters: Record<string, string>) => void
}

export function FilterBar({ fields, filters, onChange }: FilterBarProps) {
  const [field, setField] = useState(fields[0]?.name ?? '')
  const [value, setValue] = useState('')

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!field || !value.trim()) return
    onChange({ ...filters, [field]: value.trim() })
    setValue('')
  }

  function remove(name: string) {
    onChange(Object.fromEntries(Object.entries(filters).filter(([key]) => key !== name)))
  }

  return (
    <div className="filters">
      <form onSubmit={handleSubmit} className="row" aria-label="Add filter">
        <label className="field">
          <span>Field</span>
          <select value={field} onChange={(event) => setField(event.target.value)}>
            {fields.map((f) => (
              <option key={f.name} value={f.name}>
                {f.name}
              </option>
            ))}
          </select>
        </label>
        <label className="field grow">
          <span>Equals</span>
          <input value={value} onChange={(event) => setValue(event.target.value)} placeholder="exact value" />
        </label>
        <button type="submit" className="secondary">
          Add filter
        </button>
      </form>
      {Object.keys(filters).length > 0 && (
        <ul className="chips" aria-label="Active filters">
          {Object.entries(filters).map(([name, filterValue]) => (
            <li key={name}>
              <code>
                {name}={filterValue}
              </code>
              <button type="button" className="link" aria-label={`Remove filter ${name}`} onClick={() => remove(name)}>
                ×
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
