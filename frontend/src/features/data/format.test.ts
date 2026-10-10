import { describe, expect, it } from 'vitest'
import { formatValue, recordId } from './format'

describe('formatValue', () => {
  it('formats by schema type', () => {
    expect(formatValue(true, 'boolean')).toBe('✓')
    expect(formatValue(false, 'boolean')).toBe('–')
    expect(formatValue(null, 'string')).toBe('—')
    expect(formatValue('2024-01-02T03:04:05Z', 'datetime')).toBe(new Date('2024-01-02T03:04:05Z').toLocaleString())
    expect(formatValue('not a date', 'datetime')).toBe('not a date')
    expect(formatValue({ a: 1 }, 'map')).toBe('{"a":1}')
  })
})

describe('recordId', () => {
  it('supports SQL and Mongo ids', () => {
    expect(recordId({ id: 7 })).toBe('7')
    expect(recordId({ _id: 'abc' })).toBe('abc')
    expect(recordId({ name: 'x' })).toBeNull()
  })
})
