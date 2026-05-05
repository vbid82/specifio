import { useParams } from 'react-router-dom'

export function ProductDetail() {
  const { id } = useParams()
  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <h1 className="font-satoshi text-[24px] font-bold text-charcoal">
        Product Detail
      </h1>
      <p className="mt-2 text-body text-slate">Product ID: {id}</p>
    </div>
  )
}
