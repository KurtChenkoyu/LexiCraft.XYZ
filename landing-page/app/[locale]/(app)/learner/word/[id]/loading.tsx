/**
 * Loading skeleton for word detail page
 * Shows instantly while the page content loads
 */
export default function WordLoading() {
  return (
    <div className="min-h-screen bg-slate-950 animate-pulse">
      {/* Header skeleton */}
      <div className="sticky top-0 z-10 bg-slate-950/95 backdrop-blur-sm border-b border-slate-800">
        <div className="max-w-4xl mx-auto px-4 py-3">
          <div className="h-6 w-32 bg-slate-800 rounded" />
        </div>
      </div>

      {/* Content skeleton */}
      <div className="max-w-4xl mx-auto p-4 pb-24">
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-2xl p-6">
          {/* Word title */}
          <div className="mb-6">
            <div className="h-10 w-48 bg-slate-800 rounded mb-2" />
            <div className="h-4 w-16 bg-slate-800 rounded" />
          </div>
          
          {/* Definition */}
          <div className="mb-6">
            <div className="h-4 w-full bg-slate-800 rounded mb-2" />
            <div className="h-4 w-3/4 bg-slate-800 rounded" />
          </div>
          
          {/* Example */}
          <div className="mb-6 p-4 bg-slate-800/50 rounded-lg">
            <div className="h-4 w-full bg-slate-700 rounded mb-2" />
            <div className="h-4 w-2/3 bg-slate-700 rounded" />
          </div>
          
          {/* Connection chips */}
          <div className="mb-6">
            <div className="h-4 w-24 bg-slate-800 rounded mb-3" />
            <div className="flex gap-2 flex-wrap">
              <div className="h-8 w-20 bg-slate-800 rounded-full" />
              <div className="h-8 w-24 bg-slate-800 rounded-full" />
              <div className="h-8 w-16 bg-slate-800 rounded-full" />
            </div>
          </div>
          
          {/* Word family */}
          <div className="mb-6">
            <div className="h-4 w-28 bg-slate-800 rounded mb-3" />
            <div className="flex gap-2 flex-wrap">
              <div className="h-6 w-20 bg-slate-800 rounded" />
              <div className="h-6 w-16 bg-slate-800 rounded" />
              <div className="h-6 w-18 bg-slate-800 rounded" />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}


