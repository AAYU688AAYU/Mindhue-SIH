import React from 'react';
import { Activity } from 'lucide-react';

export default function ClinicalLoadingSkeleton() {
  return (
    <div className="w-full space-y-6 animate-pulse p-2">
      {/* Top Banner Skeleton */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="space-y-2.5 max-w-lg w-full">
          <div className="flex items-center gap-2">
            <div className="h-5 w-28 bg-blue-100/70 rounded-full" />
            <div className="h-4 w-40 bg-slate-200 rounded" />
          </div>
          <div className="h-7 w-3/4 bg-slate-200 rounded-lg" />
          <div className="h-4 w-5/6 bg-slate-100 rounded" />
        </div>
        <div className="flex gap-2">
          <div className="h-10 w-36 bg-blue-200/60 rounded-xl" />
          <div className="h-10 w-28 bg-slate-200 rounded-xl" />
        </div>
      </div>

      {/* KPI Cards Skeleton */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <div className="h-3 w-24 bg-slate-200 rounded" />
              <div className="h-4 w-4 bg-slate-200 rounded-full" />
            </div>
            <div className="h-8 w-16 bg-slate-300 rounded-lg" />
            <div className="h-3 w-32 bg-slate-100 rounded" />
          </div>
        ))}
      </div>

      {/* Main Content Area Skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div className="h-5 w-48 bg-slate-200 rounded" />
          <div className="h-64 bg-slate-100/80 rounded-xl flex items-center justify-center">
            <div className="flex flex-col items-center gap-2 text-slate-400">
              <Activity className="w-8 h-8 animate-spin text-[#005eb8]" />
              <span className="text-xs font-semibold tracking-wide text-slate-500">
                Loading Clinical Surveillance Engine...
              </span>
            </div>
          </div>
        </div>
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div className="h-5 w-36 bg-slate-200 rounded" />
          <div className="space-y-3 pt-2">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-12 bg-slate-100 rounded-xl" />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
