import { useEffect } from 'react'
import { X } from 'lucide-react'
import type { Product } from '../../types'

interface ProductModalProps {
  product: Product | null
  onClose: () => void
}

export function ProductModal({ product, onClose }: ProductModalProps) {
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
  }, [onClose])

  if (!product) return null

  const formatFireClass = () => {
    if (!product.fire_class_eu) return null
    let result = product.fire_class_eu
    if (product.fire_smoke_class_eu) result += `-${product.fire_smoke_class_eu}`
    if (product.fire_droplet_class_eu) result += `,${product.fire_droplet_class_eu}`
    return result
  }

  const formatCommercialGrade = () => {
    if (!product.commercial_grade || product.commercial_grade.length === 0) return null
    const gradeMap: Record<string, string> = {
      type_i: 'Type I',
      type_ii: 'Type II',
      type_iii: 'Type III',
      contract_grade: 'Contract',
      residential_grade: 'Residential',
      marine_grade: 'Marine',
      exterior_grade: 'Exterior',
    }
    return product.commercial_grade.map(g => gradeMap[g] || g).join(', ')
  }

  const formatLeadTime = () => {
    if (!product.lead_time_weeks_min && product.lead_time_weeks_min !== 0) return null
    if (product.lead_time_weeks_max) {
      return `${product.lead_time_weeks_min}-${product.lead_time_weeks_max} weeks`
    }
    return `${product.lead_time_weeks_min} weeks`
  }

  const getImageUrl = () => {
    return product.primary_image_url || null
  }

  const imageUrl = getImageUrl()

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 md:items-center"
      onClick={onClose}
    >
      <div
        className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-t-lg bg-white md:rounded-lg"
        onClick={e => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute right-4 top-4 p-1 text-slate transition-colors hover:text-charcoal"
        >
          <X size={24} />
        </button>

        {/* Image */}
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={product.name}
            className="aspect-video w-full object-cover"
          />
        ) : (
          <div className="aspect-video w-full bg-warm-grey flex items-center justify-center">
            <span className="text-sm text-slate">No image</span>
          </div>
        )}

        {/* Content */}
        <div className="space-y-6 p-6 md:p-8">
          {/* Header */}
          <div>
            <h2 className="text-2xl font-bold text-charcoal">{product.name}</h2>
            <p className="mt-1 text-sm font-semibold uppercase tracking-wide text-slate">
              {product.manufacturer_name}
            </p>
          </div>

          {/* Description */}
          {product.description && (
            <p className="text-base text-slate">{product.description}</p>
          )}

          {/* Specifications table */}
          <div className="space-y-3">
            <h3 className="font-semibold text-charcoal">Specifications</h3>
            <div className="space-y-2 text-sm">
              {[
                ['Category', product.category?.replace(/_/g, ' ').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')],
                ['Fire class', formatFireClass()],
                ['Acoustic NRC', product.nrc_value],
                ['Commercial grade', formatCommercialGrade()],
                ['Lead time', formatLeadTime()],
              ].map(([label, value]) => {
                if (!value) return null
                return (
                  <div key={label} className="flex justify-between">
                    <span className="font-medium text-slate">{label}</span>
                    <span className="font-mono text-charcoal">{value}</span>
                  </div>
                )
              })}
            </div>
          </div>

          {/* CTAs */}
          <div className="space-y-2 border-t border-warm-grey pt-6">
            {product.sample_available && (
              <button className="w-full rounded bg-specifio-blue px-4 py-2 font-medium text-white transition-opacity hover:opacity-90">
                Request sample
              </button>
            )}
            <button className="w-full rounded border border-specifio-blue px-4 py-2 font-medium text-specifio-blue transition-colors hover:bg-blue-50">
              Request quote
            </button>
            <button className="w-full rounded border border-specifio-blue px-4 py-2 font-medium text-specifio-blue transition-colors hover:bg-blue-50">
              Add to project
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
