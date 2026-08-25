export function SkeletonCard() {
  return (
    <div className="animate-pulse rounded-xl border-2 border-slate-800 bg-slate-900 p-3">
      <div className="flex items-start justify-between">
        <div className="h-7 w-8 rounded bg-slate-800" />
        <div className="h-4 w-8 rounded bg-slate-800" />
      </div>
      <div className="my-2 flex justify-center">
        <div className="h-[72px] w-[72px] rounded-full bg-slate-800" />
      </div>
      <div className="mx-auto h-3 w-24 rounded bg-slate-800" />
      <div className="mx-auto mt-2 h-3 w-16 rounded bg-slate-800" />
      <div className="mt-3 h-7 w-full rounded-lg bg-slate-800" />
    </div>
  );
}

export function SkeletonCardGrid({ count = 6 }: { count?: number }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}

export function SkeletonBlock({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded-lg bg-slate-800 ${className}`} />;
}

export function SkeletonDashboard() {
  return (
    <div className="flex min-h-screen bg-slate-950">
      <div className="hidden w-64 shrink-0 flex-col gap-2 border-r border-slate-800/80 p-4 lg:flex">
        <SkeletonBlock className="mb-4 h-10 w-full" />
        {Array.from({ length: 6 }).map((_, i) => (
          <SkeletonBlock key={i} className="h-9 w-full" />
        ))}
      </div>
      <div className="mx-auto w-full max-w-5xl px-4 py-10 lg:px-8">
        <div className="mb-6">
          <SkeletonBlock className="h-8 w-56" />
          <SkeletonBlock className="mt-2 h-4 w-72" />
        </div>
        <SkeletonCardGrid count={6} />
      </div>
    </div>
  );
}
