const PAGE_SIZES = [10, 25, 50]

interface PaginationProps {
  page: number
  totalPages: number
  totalRecords: number
  pageSize: number
  onPageChange: (page: number) => void
  onPageSizeChange: (pageSize: number) => void
}

export function Pagination({
  page,
  totalPages,
  totalRecords,
  pageSize,
  onPageChange,
  onPageSizeChange,
}: PaginationProps) {
  const lastPage = Math.max(totalPages, 1)

  return (
    <div className="pagination">
      <button type="button" className="secondary" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
        ← Prev
      </button>
      <span aria-live="polite">
        Page {page} of {lastPage}, {totalRecords} {totalRecords === 1 ? 'record' : 'records'}
      </span>
      <button type="button" className="secondary" disabled={page >= lastPage} onClick={() => onPageChange(page + 1)}>
        Next →
      </button>
      <label className="inline">
        Per page
        <select value={pageSize} onChange={(event) => onPageSizeChange(Number(event.target.value))}>
          {PAGE_SIZES.map((size) => (
            <option key={size} value={size}>
              {size}
            </option>
          ))}
        </select>
      </label>
    </div>
  )
}
