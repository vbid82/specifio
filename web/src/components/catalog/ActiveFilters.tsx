import { X } from 'lucide-react'
import type { CatalogFilters } from '../../hooks/useCatalogFilters'

interface ActiveFiltersProps {
  filters: CatalogFilters
  onRemoveFilter: (key: keyof CatalogFilters) => void
  onClearAll: () => void
}

export function ActiveFilters({ filters, onRemoveFilter, onClearAll }: ActiveFiltersProps) {
  const hasActiveFilters = Object.values(filters).some(v => v !== undefined && v !== null && v !== false)

  if (!hasActiveFilters) {
    return null
  }

  const formatLabel = (key: keyof CatalogFilters, value: any): string | null => {
    switch (key) {
      case 'category':
        return value.replace(/_/g, ' ').split(' ').map((w: string) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
      case 'fire_class_eu':
        return `Fire class: ${value}`
      case 'commercial_grade':
        const gradeMap: Record<string, string> = {
          type_i: 'Type I',
          type_ii: 'Type II',
          type_iii: 'Type III',
          contract_grade: 'Contract',
          residential_grade: 'Residential',
          marine_grade: 'Marine',
          exterior_grade: 'Exterior',
        }
        return `Commercial: ${gradeMap[value] || value}`
      case 'min_nrc':
        return `Min NRC: ${value}`
      case 'max_nrc':
        return `Max NRC: ${value}`
      case 'min_lead_time':
        return `Min lead: ${value}w`
      case 'max_lead_time':
        return `Max lead: ${value}w`
      case 'sample_available':
        return 'Sample available'
      case 'custom_colorway':
        return 'Custom colorway'
      default:
        return null
    }
  }

  return (
    <div className="mb-4 flex flex-wrap items-center gap-2 rounded bg-blue-50 p-3">
      {Object.entries(filters).map(([key, value]) => {
        if (value === undefined || value === null || value === false) return null
        const label = formatLabel(key as keyof CatalogFilters, value)
        if (!label) return null

        return (
          <button
            key={key}
            onClick={() => onRemoveFilter(key as keyof CatalogFilters)}
            className="inline-flex items-center gap-1 rounded bg-white px-2 py-1 text-xs text-specifio-blue transition-colors hover:bg-gray-50"
          >
            {label}
            <X size={14} />
          </button>
        )
      })}

      <button
        onClick={onClearAll}
        className="ml-auto text-xs text-specifio-blue underline transition-colors hover:no-underline"
      >
        Clear all
      </button>
    </div>
  )
}
