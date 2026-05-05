import { Link } from 'react-router-dom'

export function Home() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="max-w-2xl">
        <h1 className="font-satoshi text-[32px] font-bold leading-tight text-charcoal">
          Filter by fire class, acoustic rating, and lead time in one search.
        </h1>
        <p className="mt-4 text-body text-slate">
          Specifio is a specification workspace for architectural surfaces.
          Browse products with structured technical data. Build project shortlists.
          Request samples and quotes in one flow.
        </p>
        <div className="mt-8">
          <Link
            to="/catalog"
            className="inline-block rounded bg-specifio-blue px-6 py-2.5 text-[14px] font-medium text-white hover:bg-specifio-blue/90"
          >
            Browse the catalog
          </Link>
        </div>
      </div>
    </div>
  )
}
