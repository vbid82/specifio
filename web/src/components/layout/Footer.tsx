export function Footer() {
  return (
    <footer className="border-t border-warm-grey bg-white py-6">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between">
          <p className="text-[13px] text-slate">
            Specifio. Surface specification for professionals.
          </p>
          <p className="text-[13px] text-slate">
            &copy; {new Date().getFullYear()}
          </p>
        </div>
      </div>
    </footer>
  )
}
