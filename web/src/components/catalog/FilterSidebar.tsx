import { useState } from 'react'
import type { CatalogFilters } from '../../hooks/useCatalogFilters'
import { FilterSection } from './FilterSection'

interface FilterSidebarProps {
  filters: CatalogFilters
  onFiltersChange: (filters: CatalogFilters) => void
}

const CATEGORIES = [
  'wallcovering',
  'surface_panel',
  'acoustic_panel',
  'ceiling_tile',
  'ceiling_system',
  'textile',
  'mural',
  'decorative_paint',
  'liquid_metal',
  'bespoke_finish',
  'decorative_mesh',
  'composite_surface',
]

const FIRE_CLASSES = ['A1', 'A2', 'B', 'C', 'D', 'E', 'F']

const COMMERCIAL_GRADES = [
  { value: 'type_i', label: 'Type I' },
  { value: 'type_ii', label: 'Type II' },
  { value: 'type_iii', label: 'Type III' },
  { value: 'contract_grade', label: 'Contract' },
  { value: 'residential_grade', label: 'Residential' },
  { value: 'marine_grade', label: 'Marine' },
  { value: 'exterior_grade', label: 'Exterior' },
]

function formatCategory(slug: string) {
  return slug
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

export function FilterSidebar({ filters, onFiltersChange }: FilterSidebarProps) {
  const [minNrc, setMinNrc] = useState(filters.min_nrc?.toString() || '')
  const [maxNrc, setMaxNrc] = useState(filters.max_nrc?.toString() || '')
  const [minLeadTime, setMinLeadTime] = useState(filters.min_lead_time?.toString() || '')
  const [maxLeadTime, setMaxLeadTime] = useState(filters.max_lead_time?.toString() || '')

  const handleNrcChange = (type: 'min' | 'max', value: string) => {
    if (type === 'min') {
      setMinNrc(value)
      const newFilters = { ...filters, min_nrc: value ? parseFloat(value) : null }
      onFiltersChange(newFilters)
    } else {
      setMaxNrc(value)
      const newFilters = { ...filters, max_nrc: value ? parseFloat(value) : null }
      onFiltersChange(newFilters)
    }
  }

  const handleLeadTimeChange = (type: 'min' | 'max', value: string) => {
    if (type === 'min') {
      setMinLeadTime(value)
      const newFilters = { ...filters, min_lead_time: value ? parseInt(value) : null }
      onFiltersChange(newFilters)
    } else {
      setMaxLeadTime(value)
      const newFilters = { ...filters, max_lead_time: value ? parseInt(value) : null }
      onFiltersChange(newFilters)
    }
  }

  return (
    <div className="w-64 space-y-1">
      {/* Category */}
      <FilterSection title="Category" defaultExpanded>
        <div className="space-y-2">
          {CATEGORIES.map(cat => (
            <label key={cat} className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={filters.category === cat}
                onChange={e => {
                  onFiltersChange({ ...filters, category: e.target.checked ? cat : undefined })
                }}
                className="h-4 w-4 cursor-pointer rounded border-warm-grey"
              />
              <span className="text-sm text-slate">{formatCategory(cat)}</span>
            </label>
          ))}
        </div>
      </FilterSection>

      {/* Fire class */}
      <FilterSection title="Fire class" defaultExpanded>
        <div className="space-y-2">
          {FIRE_CLASSES.map(fc => (
            <label key={fc} className="flex items-center gap-2">
              <input
                type="radio"
                name="fire_class"
                checked={filters.fire_class_eu === fc}
                onChange={e => {
                  onFiltersChange({ ...filters, fire_class_eu: e.target.checked ? fc : undefined })
                }}
                className="h-4 w-4 cursor-pointer"
              />
              <span className="text-sm text-slate">{fc}</span>
            </label>
          ))}
        </div>
      </FilterSection>

      {/* Acoustic NRC */}
      <FilterSection title="Acoustic NRC" defaultExpanded>
        <div className="space-y-2">
          <div>
            <label className="block text-xs font-medium text-slate">Min NRC</label>
            <input
              type="number"
              min="0"
              max="1"
              step="0.05"
              value={minNrc}
              onChange={e => handleNrcChange('min', e.target.value)}
              className="mt-1 w-full rounded border border-warm-grey px-2 py-1 text-sm text-charcoal"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate">Max NRC</label>
            <input
              type="number"
              min="0"
              max="1"
              step="0.05"
              value={maxNrc}
              onChange={e => handleNrcChange('max', e.target.value)}
              className="mt-1 w-full rounded border border-warm-grey px-2 py-1 text-sm text-charcoal"
            />
          </div>
        </div>
      </FilterSection>

      {/* Commercial grade */}
      <FilterSection title="Commercial grade">
        <div className="space-y-2">
          {COMMERCIAL_GRADES.map(grade => (
            <label key={grade.value} className="flex items-center gap-2">
              <input
                type="radio"
                name="commercial_grade"
                checked={filters.commercial_grade === grade.value}
                onChange={e => {
                  onFiltersChange({ ...filters, commercial_grade: e.target.checked ? grade.value : undefined })
                }}
                className="h-4 w-4 cursor-pointer"
              />
              <span className="text-sm text-slate">{grade.label}</span>
            </label>
          ))}
        </div>
      </FilterSection>

      {/* Lead time */}
      <FilterSection title="Lead time">
        <div className="space-y-2">
          <div>
            <label className="block text-xs font-medium text-slate">Min weeks</label>
            <input
              type="number"
              min="0"
              value={minLeadTime}
              onChange={e => handleLeadTimeChange('min', e.target.value)}
              className="mt-1 w-full rounded border border-warm-grey px-2 py-1 text-sm text-charcoal"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate">Max weeks</label>
            <input
              type="number"
              min="0"
              value={maxLeadTime}
              onChange={e => handleLeadTimeChange('max', e.target.value)}
              className="mt-1 w-full rounded border border-warm-grey px-2 py-1 text-sm text-charcoal"
            />
          </div>
        </div>
      </FilterSection>

      {/* Availability */}
      <FilterSection title="Availability">
        <div className="space-y-2">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={filters.sample_available === true}
              onChange={e => {
                onFiltersChange({ ...filters, sample_available: e.target.checked || undefined })
              }}
              className="h-4 w-4 cursor-pointer"
            />
            <span className="text-sm text-slate">Sample available</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={filters.custom_colorway === true}
              onChange={e => {
                onFiltersChange({ ...filters, custom_colorway: e.target.checked || undefined })
              }}
              className="h-4 w-4 cursor-pointer"
            />
            <span className="text-sm text-slate">Custom colorway</span>
          </label>
        </div>
      </FilterSection>
    </div>
  )
}
