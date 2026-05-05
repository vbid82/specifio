import { useState, useEffect, useCallback, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../lib/api'
import type { Product } from '../types'

export interface CatalogFilters {
  category?: string
  fire_class_eu?: string
  min_nrc?: number | null
  max_nrc?: number | null
  commercial_grade?: string
  min_lead_time?: number | null
  max_lead_time?: number | null
  sample_available?: boolean
  custom_colorway?: boolean
}

interface ApiResponse {
  items: Product[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

const DEFAULT_LIMIT = 20

export function useCatalogFilters() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [filters, setFilters] = useState<CatalogFilters>({})
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({ offset: 0, limit: DEFAULT_LIMIT, total: 0 })
  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Initialize filters from URL params on mount
  useEffect(() => {
    const newFilters: CatalogFilters = {}
    const category = searchParams.get('category')
    const fireClass = searchParams.get('fire_class_eu')
    const minNrc = searchParams.get('min_nrc')
    const maxNrc = searchParams.get('max_nrc')
    const commercialGrade = searchParams.get('commercial_grade')
    const minLeadTime = searchParams.get('min_lead_time')
    const maxLeadTime = searchParams.get('max_lead_time')
    const sampleAvailable = searchParams.get('sample_available')
    const customColorway = searchParams.get('custom_colorway')
    const offset = searchParams.get('offset')

    if (category) newFilters.category = category
    if (fireClass) newFilters.fire_class_eu = fireClass
    if (minNrc) newFilters.min_nrc = parseFloat(minNrc)
    if (maxNrc) newFilters.max_nrc = parseFloat(maxNrc)
    if (commercialGrade) newFilters.commercial_grade = commercialGrade
    if (minLeadTime) newFilters.min_lead_time = parseInt(minLeadTime)
    if (maxLeadTime) newFilters.max_lead_time = parseInt(maxLeadTime)
    if (sampleAvailable) newFilters.sample_available = sampleAvailable === 'true'
    if (customColorway) newFilters.custom_colorway = customColorway === 'true'

    setFilters(newFilters)
    if (offset) {
      setPagination(p => ({ ...p, offset: parseInt(offset) }))
    } else {
      setPagination(p => ({ ...p, offset: 0 }))
    }
  }, [])

  const fetchProducts = useCallback(async (filtersToUse: CatalogFilters, offset: number) => {
    setLoading(true)
    try {
      const params = new URLSearchParams()

      if (filtersToUse.category) params.set('category', filtersToUse.category)
      if (filtersToUse.fire_class_eu) params.set('fire_class_eu', filtersToUse.fire_class_eu)
      if (filtersToUse.min_nrc !== null && filtersToUse.min_nrc !== undefined) {
        params.set('min_nrc', String(filtersToUse.min_nrc))
      }
      if (filtersToUse.max_nrc !== null && filtersToUse.max_nrc !== undefined) {
        params.set('max_nrc', String(filtersToUse.max_nrc))
      }
      if (filtersToUse.commercial_grade) params.set('commercial_grade', filtersToUse.commercial_grade)
      if (filtersToUse.min_lead_time !== null && filtersToUse.min_lead_time !== undefined) {
        params.set('min_lead_time', String(filtersToUse.min_lead_time))
      }
      if (filtersToUse.max_lead_time !== null && filtersToUse.max_lead_time !== undefined) {
        params.set('max_lead_time', String(filtersToUse.max_lead_time))
      }
      if (filtersToUse.sample_available) params.set('sample_available', 'true')
      if (filtersToUse.custom_colorway) params.set('custom_colorway', 'true')

      params.set('skip', String(offset))
      params.set('limit', String(DEFAULT_LIMIT))

      const response = await api.get<ApiResponse>(`/products?${params.toString()}`)
      setProducts(response.items)
      setPagination({
        offset,
        limit: DEFAULT_LIMIT,
        total: response.total,
      })
    } catch (error) {
      console.error('Failed to fetch products:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  // Load products on component mount
  useEffect(() => {
    fetchProducts(filters, pagination.offset)
  }, [])

  const updateFilters = useCallback((newFilters: CatalogFilters) => {
    setFilters(newFilters)
    setPagination(p => ({ ...p, offset: 0 }))

    // Update URL params
    const newParams = new URLSearchParams()
    if (newFilters.category) newParams.set('category', newFilters.category)
    if (newFilters.fire_class_eu) newParams.set('fire_class_eu', newFilters.fire_class_eu)
    if (newFilters.min_nrc !== null && newFilters.min_nrc !== undefined) {
      newParams.set('min_nrc', String(newFilters.min_nrc))
    }
    if (newFilters.max_nrc !== null && newFilters.max_nrc !== undefined) {
      newParams.set('max_nrc', String(newFilters.max_nrc))
    }
    if (newFilters.commercial_grade) newParams.set('commercial_grade', newFilters.commercial_grade)
    if (newFilters.min_lead_time !== null && newFilters.min_lead_time !== undefined) {
      newParams.set('min_lead_time', String(newFilters.min_lead_time))
    }
    if (newFilters.max_lead_time !== null && newFilters.max_lead_time !== undefined) {
      newParams.set('max_lead_time', String(newFilters.max_lead_time))
    }
    if (newFilters.sample_available) newParams.set('sample_available', 'true')
    if (newFilters.custom_colorway) newParams.set('custom_colorway', 'true')

    setSearchParams(newParams)

    // Debounce the API call
    if (debounceTimer.current !== null) clearTimeout(debounceTimer.current)
    debounceTimer.current = setTimeout(() => {
      fetchProducts(newFilters, 0)
    }, 300)
  }, [fetchProducts, setSearchParams])

  const setFilter = useCallback((key: keyof CatalogFilters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }, [])

  const removeFilter = useCallback((key: keyof CatalogFilters) => {
    setFilters(prev => {
      const updated = { ...prev }
      delete updated[key]
      return updated
    })
  }, [])

  const clearAll = useCallback(() => {
    setFilters({})
    setPagination(p => ({ ...p, offset: 0 }))
    setSearchParams(new URLSearchParams())
    fetchProducts({}, 0)
  }, [fetchProducts, setSearchParams])

  const loadMore = useCallback(() => {
    const newOffset = pagination.offset + DEFAULT_LIMIT
    setPagination(p => ({ ...p, offset: newOffset }))
    fetchProducts(filters, newOffset)
  }, [filters, pagination.offset, fetchProducts])

  return {
    filters,
    products,
    loading,
    pagination,
    updateFilters,
    setFilter,
    removeFilter,
    clearAll,
    loadMore,
  }
}
