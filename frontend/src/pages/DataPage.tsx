import { useCallback, useMemo, useState } from 'react'
import { dataApi } from '../api/endpoints'
import { ErrorMessage } from '../components/ErrorMessage'
import { DataTable } from '../features/data/DataTable'
import { FilterBar } from '../features/data/FilterBar'
import { Pagination } from '../features/data/Pagination'
import { RecordDetail } from '../features/data/RecordDetail'
import { useAsync } from '../hooks'

const SLUGS = ['users', 'user-permissions', 'products']

export function DataPage() {
  const [slug, setSlug] = useState(SLUGS[0] ?? '')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [filters, setFilters] = useState<Record<string, string>>({})
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const loadSchema = useCallback(() => dataApi.describe(slug), [slug])
  const schema = useAsync(loadSchema)

  const schemaReady = schema.status === 'success'
  const loadRecords = useMemo(
    () => (schemaReady ? () => dataApi.list(slug, { page, pageSize, filters }) : null),
    [schemaReady, slug, page, pageSize, filters],
  )
  const records = useAsync(loadRecords)

  function changeSlug(next: string) {
    setSlug(next)
    setPage(1)
    setFilters({})
    setSelectedId(null)
  }

  function changeFilters(next: Record<string, string>) {
    setFilters(next)
    setPage(1)
  }

  function changePageSize(next: number) {
    setPageSize(next)
    setPage(1)
  }

  return (
    <div className="data-page">
      <section className="card">
        <div className="data-header">
          <h1>Data browser</h1>
          <label className="inline">
            Model
            <select value={slug} onChange={(event) => changeSlug(event.target.value)}>
              {SLUGS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
        </div>

        {schema.status === 'loading' && <p className="muted">Loading schema…</p>}
        {schema.status === 'error' && <ErrorMessage error={schema.error} />}
        {schema.status === 'success' && (
          <>
            <p className="muted">
              Columns come from the <code>{schema.data.name}</code> schema ({schema.data.fields.length} fields).
            </p>
            {/* Keyed by slug so the field picker resets to the new model's first field. */}
            <FilterBar key={slug} fields={schema.data.fields} filters={filters} onChange={changeFilters} />

            {records.status === 'loading' && <p className="muted">Loading records…</p>}
            {records.status === 'error' && <ErrorMessage error={records.error} />}
            {records.status === 'success' && (
              <>
                <DataTable
                  fields={schema.data.fields}
                  records={records.data.data}
                  selectedId={selectedId}
                  onSelect={setSelectedId}
                />
                <Pagination
                  page={records.data.page}
                  totalPages={records.data.total_page}
                  totalRecords={records.data.total_data}
                  pageSize={pageSize}
                  onPageChange={setPage}
                  onPageSizeChange={changePageSize}
                />
              </>
            )}
          </>
        )}
      </section>

      {selectedId && <RecordDetail slug={slug} id={selectedId} onClose={() => setSelectedId(null)} />}
    </div>
  )
}
