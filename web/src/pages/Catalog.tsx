import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useCatalogFilters } from '../hooks/useCatalogFilters'
import { FilterSidebar } from '../components/catalog/FilterSidebar'
import { ActiveFilters } from '../components/catalog/ActiveFilters'
import { ProductGrid } from '../components/catalog/ProductGrid'
import { ProductModal } from '../components/catalog/ProductModal'
import type { Product } from '../types'

export function Catalog() {
  const {
    filters,
    products,
    loading,
    pagination,
    updateFilters,
    removeFilter,
    clearAll,
    loadMore,
  } = useCatalogFilters()

  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)
  const [searchParams, setSearchParams] = useSearchParams()

  // Sync selected product from URL
  if (!selectedProduct && searchParams.get('product')) {
    const productId = searchParams.get('product')
    const product = products.find(p => p.id === productId)
    if (product) {
      setSelectedProduct(product)
    }
  }

  const handleProductClick = (product: Product) => {
    setSelectedProduct(product)
    const newParams = new URLSearchParams(searchParams)
    newParams.set('product', product.id)
    setSearchParams(newParams)
  }

  const handleModalClose = () => {
    setSelectedProduct(null)
    const newParams = new URLSearchParams(searchParams)
    newParams.delete('product')
    setSearchParams(newParams)
  }

  return (
    <div className="min-h-screen bg-clean-white">
      {/* Active filters bar */}
      <div className="border-b border-warm-grey bg-white">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <ActiveFilters
            filters={filters}
            onRemoveFilter={removeFilter}
            onClearAll={clearAll}
          />
        </div>
      </div>

      {/* Main content */}
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="flex gap-8">
          {/* Sidebar */}
          <div className="hidden flex-shrink-0 lg:block">
            <FilterSidebar filters={filters} onFiltersChange={updateFilters} />
          </div>

          {/* Grid */}
          <div className="flex-1">
            <ProductGrid
              products={products}
              loading={loading}
              onProductClick={handleProductClick}
              pagination={pagination}
              onLoadMore={loadMore}
            />
          </div>
        </div>
      </div>

      {/* Product modal */}
      <ProductModal product={selectedProduct} onClose={handleModalClose} />
    </div>
  )
}
