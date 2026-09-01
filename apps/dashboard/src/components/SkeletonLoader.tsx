"use client";

import React from "react";

export function CardSkeleton() {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs animate-pulse">
      <div className="h-3 w-24 bg-slate-200 rounded" />
      <div className="h-7 w-32 bg-slate-200 rounded mt-3" />
      <div className="h-3 w-40 bg-slate-100 rounded mt-2" />
    </div>
  );
}

export function TableSkeleton({ rows = 5, cols = 5 }: { rows?: number; cols?: number }) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
      <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex justify-between">
        <div className="h-8 w-48 bg-slate-200 animate-pulse rounded" />
        <div className="h-8 w-24 bg-slate-200 animate-pulse rounded" />
      </div>
      <div className="p-4 space-y-3">
        {Array.from({ length: rows }).map((_, r) => (
          <div key={r} className="flex items-center space-x-4 animate-pulse">
            {Array.from({ length: cols }).map((_, c) => (
              <div key={c} className="h-4 bg-slate-100 rounded flex-1" />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
