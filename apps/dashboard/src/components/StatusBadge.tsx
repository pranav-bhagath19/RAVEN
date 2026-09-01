"use client";

import React from "react";

interface StatusBadgeProps {
  status: string;
  size?: "sm" | "md";
  className?: string;
}

export function StatusBadge({ status, size = "sm", className = "" }: StatusBadgeProps) {
  const normalized = (status || "").toUpperCase();

  let styles = "bg-slate-100 text-slate-700 border-slate-200";

  if (["CAPTURED", "RECOVERED", "APPROVED", "HEALTHY", "CHAMPION", "ACTIVE", "SUCCESS", "COMPLETED", "200_OK"].includes(normalized)) {
    styles = "bg-emerald-50 text-emerald-700 border-emerald-200";
  } else if (["FAILED", "VETOED", "CRITICAL", "ROLLED_BACK", "BLOCKED", "DECLINED", "ERROR", "REJECTED"].includes(normalized)) {
    styles = "bg-rose-50 text-rose-700 border-rose-200";
  } else if (["PENDING", "WARNING", "CHALLENGER", "IN_PROGRESS", "EXPIRED", "SMART_RETRY", "PAYMENT_LINK"].includes(normalized)) {
    styles = "bg-amber-50 text-amber-800 border-amber-200";
  } else if (["COUNTERFACTUAL", "SIMULATION", "TEST MODE"].includes(normalized)) {
    styles = "bg-blue-50 text-blue-700 border-blue-200 font-semibold";
  } else if (["PRODUCTION", "LIVE"].includes(normalized)) {
    styles = "bg-indigo-50 text-indigo-700 border-indigo-200 font-semibold";
  }

  const sizeClasses = size === "sm" ? "px-2 py-0.5 text-[11px]" : "px-2.5 py-1 text-xs";

  return (
    <span className={`inline-flex items-center font-sans font-bold rounded-md border ${sizeClasses} ${styles} ${className}`}>
      {status}
    </span>
  );
}
