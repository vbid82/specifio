import type { Product } from '../../types'
import { ProductCard } from './ProductCard'
import { SkeletonCard } from './SkeletonCard'

interface ProductGridProps {
  products: Product[]
  loading: boolean
  onProductClick: (product: Product) => void
  pagination: { offset: number; limit: number; total: number }
  onLoadMore: () => void
}

export function ProductGrid({
  products,
  loading,
  onProductClick,
  pagination,
  onLoadMore,
}: ProductGridProps) {
  const skeletonCount = 6
  const hasMore = pagination.offset + pagination.limit < pagination.total

  // Loading state
  if (loading && products.length === 0) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: skeletonCount }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    )
  }

  // Empty state
  if (products.length === 0 && !loading) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <p className="text-lg text-slate">No products match your filters.</p>
        <p className="mt-2 text-sm text-slate">Try adjusting your criteria or clear all filters.</p>
      </div>
    )
  }

  // Product grid
  return (
    <div className="space-y-8">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {products.map(product => (
          <ProductCard
            key={product.id}
            product={product}
            onClick={() => onProductClick(product)}
          />
        ))}
      </div>

      {/* Pagination info and load more */}
      <div className="flex items-center justify-between border-t border-warm-grey pt-6">
        <p className="text-sm text-slate">
          Showing {products.length + pagination.offset} of {pagination.total} products
        </p>

        {hasMore && (
          <button
            onClick={onLoadMore}
            disabled={loading}
            className="rounded bg-specifio-blue px-4 py-2 font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {loading ? 'Loading...' : 'Load more'}
          </button>
        )}
      </div>
    </div>
  )
}
