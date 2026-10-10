import type { DataRecord, SchemaField } from '../../api/types'
import { formatValue, recordId } from './format'

interface DataTableProps {
  fields: SchemaField[]
  records: DataRecord[]
  selectedId: string | null
  onSelect: (id: string) => void
}

export function DataTable({ fields, records, selectedId, onSelect }: DataTableProps) {
  if (records.length === 0) return <p className="muted">No records match.</p>

  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            {fields.map((field) => (
              <th key={field.name} scope="col">
                {field.name}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {records.map((record, index) => {
            const id = recordId(record)
            const select = () => id && onSelect(id)
            return (
              <tr
                key={id ?? index}
                className={id === selectedId ? 'selected' : undefined}
                tabIndex={id ? 0 : undefined}
                onClick={select}
                onKeyDown={(event) => event.key === 'Enter' && select()}
              >
                {fields.map((field) => (
                  <td key={field.name} className={`type-${field.type}`}>
                    {formatValue(record[field.name], field.type)}
                  </td>
                ))}
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
