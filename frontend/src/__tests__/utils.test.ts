import { describe, expect, it } from 'vitest'
import { formatBytes, normalizeEntity, normalizeId } from '@/lib/utils'

describe('ID normalization utility', () => {
  it('normalizes MongoDB _id to string id', () => {
    const raw = { _id: '67b93198a28e932b10', name: 'Test Doc' }
    expect(normalizeId(raw)).toBe('67b93198a28e932b10')
  })

  it('preserves existing id if present', () => {
    const raw = { id: 'doc-123', _id: '67b93198a28e932b10' }
    expect(normalizeId(raw)).toBe('doc-123')
  })

  it('normalizes an entire entity object', () => {
    const raw = { _id: '67b93198a28e932b10', title: 'Invoice.pdf' }
    const normalized = normalizeEntity(raw)
    expect(normalized.id).toBe('67b93198a28e932b10')
    expect(normalized.title).toBe('Invoice.pdf')
  })

  it('formats byte sizes accurately', () => {
    expect(formatBytes(0)).toBe('0 Bytes')
    expect(formatBytes(1024)).toBe('1 KB')
    expect(formatBytes(1048576 * 5)).toBe('5 MB')
  })
})
