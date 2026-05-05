export function SkeletonCard() {
  return (
    <div className="overflow-hidden rounded border border-warm-grey">
      <div className="aspect-video w-full animate-pulse bg-warm-grey" />
      <div className="space-y-3 p-4">
        <div className="h-3 w-24 animate-pulse rounded bg-warm-grey" />
        <div className="h-4 w-3/4 animate-pulse rounded bg-warm-grey" />
        <div className="flex gap-2">
          <div className="h-5 w-16 animate-pulse rounded bg-warm-grey" />
          <div className="h-5 w-16 animate-pulse rounded bg-warm-grey" />
        </div>
        <div className="h-3 w-1/2 animate-pulse rounded bg-warm-grey" />
      </div>
    </div>
  )
}
