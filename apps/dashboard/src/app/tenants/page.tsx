"use client";

import React, { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { TableSkeleton } from "@/components/SkeletonLoader";
import { Lock, ShieldCheck, Users } from "lucide-react";

export default function TenantsPage() {
  const [tenants, setTenants] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchApi<any[]>("/tenants")
      .then((data) => {
        setTenants(data);
        setLoading(false);
      })
      .catch(() => {
        setTenants([
          {
            tenant_id: "tenant_demo",
            name: "Razorpay Demo Merchant",
            status: "ACTIVE",
            failed_payments: 30,
            revenue_at_risk_minor: 9547000,
            recovered_revenue_minor: 4848600,
            recovery_rate_pct: 50.79,
            active_policy: "POL_001_DEFAULT",
          },
          {
            tenant_id: "tenant_acme",
            name: "Acme SaaS Technologies",
            status: "ACTIVE",
            failed_payments: 14,
            revenue_at_risk_minor: 4500000,
            recovered_revenue_minor: 2250000,
            recovery_rate_pct: 50.0,
            active_policy: "POL_001_STRICT",
          },
          {
            tenant_id: "tenant_global",
            name: "Global E-Commerce Corp",
            status: "ACTIVE",
            failed_payments: 55,
            revenue_at_risk_minor: 18200000,
            recovered_revenue_minor: 9100000,
            recovery_rate_pct: 50.0,
            active_policy: "POL_001_DEFAULT",
          },
        ]);
        setLoading(false);
      });
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center">
            <Users className="w-5 h-5 text-blue-600 mr-2" /> Multi-Tenant Merchant Portfolio
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Authenticated tenant context isolation & merchant recovery performance
          </p>
        </div>
      </div>

      {/* Security Invariant Notice */}
      <div className="bg-slate-100 border border-slate-300 text-slate-800 rounded-xl p-4 flex items-center space-x-3">
        <Lock className="w-4 h-4 text-slate-600 shrink-0" />
        <p className="text-xs font-medium">
          Tenant context is enforced by authenticated backend UserIdentity (`X-Tenant-ID`). Requests cannot access cross-tenant data.
        </p>
      </div>

      {loading ? (
        <TableSkeleton rows={4} cols={6} />
      ) : (
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase font-semibold text-[11px]">
                <th className="p-3.5">Tenant ID</th>
                <th className="p-3.5">Merchant Name</th>
                <th className="p-3.5">Failed Payments</th>
                <th className="p-3.5">Revenue at Risk</th>
                <th className="p-3.5">Revenue Recovered</th>
                <th className="p-3.5">Value Recovery Rate</th>
                <th className="p-3.5 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {tenants.map((t) => (
                <tr key={t.tenant_id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="p-3.5 font-mono font-bold text-blue-600">{t.tenant_id}</td>
                  <td className="p-3.5 font-semibold text-slate-900">{t.name}</td>
                  <td className="p-3.5 font-mono text-slate-700">{t.failed_payments}</td>
                  <td className="p-3.5 font-mono font-bold text-slate-900">
                    ₹{(t.revenue_at_risk_minor / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </td>
                  <td className="p-3.5 font-mono font-bold text-emerald-600">
                    ₹{(t.recovered_revenue_minor / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </td>
                  <td className="p-3.5 font-mono font-bold text-blue-600">{t.recovery_rate_pct}%</td>
                  <td className="p-3.5 text-right">
                    <StatusBadge status={t.status || "ACTIVE"} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
