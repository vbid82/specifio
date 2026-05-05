import type { Product } from '../../types'

interface ProductCardProps {
  product: Product
  onClick: () => void
}

export function ProductCard({ product, onClick }: ProductCardProps) {
  // Format fire class badge
  const getFireClassBadge = () => {
    if (!product.fire_class_eu) return null
    let badge = product.fire_class_eu
    if (product.fire_smoke_class_eu) badge += `-${product.fire_smoke_class_eu}`
    if (product.fire_droplet_class_eu) badge += `,${product.fire_droplet_class_eu}`
    return badge
  }

  // Format lead time
  const getLeadTime = () => {
    if (!product.lead_time_weeks_min && product.lead_time_weeks_min !== 0) return null
    if (product.lead_time_weeks_max) {
      return `${product.lead_time_weeks_min}-${product.lead_time_weeks_max} weeks`
    }
    return `${product.lead_time_weeks_min} weeks`
  }

  // Format price
  const getPrice = () => {
    if (product.price_visibility === 'on_request') {
      return 'Price on request'
    }
    if (product.price_visibility === 'public' && product.indicative_price_eur) {
      return `€${parseFloat(product.indicative_price_eur).toFixed(2)}`
    }
    if (product.price_visibility === 'registered' || product.price_visibility === 'trade_only') {
      return 'Sign in for pricing'
    }
    return null
  }

  // Get primary image
  const getImageUrl = () => {
    return product.primary_image_url || null
  }

  const fireClassBadge = getFireClassBadge()
  const leadTime = getLeadTime()
  const price = getPrice()
  const imageUrl = getImageUrl()

  return (
    <button
      onClick={onClick}
      className="overflow-hidden rounded border border-warm-grey bg-white text-left transition-shadow hover:shadow-card"
    >
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
      <div className="p-4">
        {/* Manufacturer */}
        <div className="text-xs font-semibold uppercase tracking-wide text-slate">
          {product.manufacturer_name}
        </div>

        {/* Product name */}
        <h3 className="mt-2 font-medium text-charcoal">{product.name}</h3>

        {/* Spec badges */}
        {(fireClassBadge || product.nrc_value || leadTime) && (
          <div className="mt-2 flex flex-wrap gap-1">
            {fireClassBadge && (
              <span className="inline-block rounded bg-blue-50 px-1.5 py-0.5 font-mono text-xs text-specifio-blue">
                {fireClassBadge}
              </span>
            )}
            {product.nrc_value && (
              <span className="inline-block rounded bg-blue-50 px-1.5 py-0.5 font-mono text-xs text-specifio-blue">
                NRC {product.nrc_value}
              </span>
            )}
            {leadTime && (
              <span className="inline-block rounded bg-blue-50 px-1.5 py-0.5 font-mono text-xs text-specifio-blue">
                {leadTime}
              </span>
            )}
          </div>
        )}

        {/* Sample availability */}
        <div className="mt-3 text-xs">
          <span className={product.sample_available ? 'text-forest' : 'text-slate'}>
            {product.sample_available ? 'Sample available' : 'No sample'}
          </span>
        </div>

        {/* Price */}
        {price && (
          <div className="mt-2 font-mono text-sm text-slate">
            {price}
          </div>
        )}
      </div>
    </button>
  )
}
