"use client";

import React from "react";
import { LucideIcon } from "lucide-react";

interface KpiCardProps {
  title: string;
  value: string | number;
  subtext?: string;
  icon?: LucideIcon;
  trend?: string;
  trendDirection?: "up" | "down" | "neutral";
  loading?: boolean;
  accentColor?: "blue" | "emerald" | "amber" | "rose" | "indigo";
}

export function KpiCard({
  title,
  value,
  subtext,
  icon: Icon,
  trend,
  trendDirection = "up",
  loading = false,
  accentColor = "blue",
}: KpiCardProps) {
  const colorMap = {
    blue: "bg-blue-50 text-blue-600 border-blue-100",
    emerald: "bg-emerald-50 text-emerald-600 border-emerald-100",
    amber: "bg-amber-50 text-amber-600 border-amber-100",
    rose: "bg-rose-50 text-rose-600 border-rose-100",
    indigo: "bg-indigo-50 text-indigo-600 border-indigo-100",
  };

  return (
    <div className="bg-white border border-slate-200/80 rounded-xl p-5 shadow-xs hover:border-slate-300 transition-all duration-200">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{title}</span>
        {Icon && (
          <div className={`p-2 rounded-lg border ${colorMap[accentColor]}`}>
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>

      <div className="mt-3 flex items-baseline justify-between">
        {loading ? (
          <div className="h-8 w-28 bg-slate-100 animate-pulse rounded-md" />
        ) : (
          <div className="text-2xl font-bold text-slate-900 tracking-tight font-mono">{value}</div>
        )}

        {trend && !loading && (
          <span
            className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
              trendDirection === "up"
                ? "bg-emerald-50 text-emerald-700"
                : trendDirection === "down"
                ? "bg-rose-50 text-rose-700"
                : "bg-slate-100 text-slate-600"
            }`}
          >
            {trend}
          </span>
        )}
      </div>

      {subtext && <p className="text-xs text-slate-400 mt-1.5 font-medium">{subtext}</p>}
    </div>
  );
}
