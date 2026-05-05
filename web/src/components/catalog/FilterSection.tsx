import { useState } from 'react'
import type { ReactNode } from 'react'
import { ChevronDown } from 'lucide-react'

interface FilterSectionProps {
  title: string
  defaultExpanded?: boolean
  children: ReactNode
}

export function FilterSection({ title, defaultExpanded = false, children }: FilterSectionProps) {
  const [expanded, setExpanded] = useState(defaultExpanded)

  return (
    <div className="border-b border-warm-grey py-3">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between gap-2 transition-colors hover:text-specifio-blue"
      >
        <span className="text-label font-medium text-slate">{title}</span>
        <ChevronDown
          size={16}
          className={`flex-shrink-0 text-slate transition-transform ${expanded ? 'rotate-180' : ''}`}
        />
      </button>

      {expanded && (
        <div className="mt-2 space-y-2">
          {children}
        </div>
      )}
    </div>
  )
}
