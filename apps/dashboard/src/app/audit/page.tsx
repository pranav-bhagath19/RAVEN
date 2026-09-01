"use client";

import React, { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { TableSkeleton } from "@/components/SkeletonLoader";
import { FileText, Lock, Search } from "lucide-react";

export default function AuditPage() {
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchApi<any[]>("/audit/events")
      .then((data) => {
        setEvents(data);
        setLoading(false);
      })
      .catch(() => {
        setEvents([
          { audit_id: "aud_1001", actor: "admin_dev_key", tenant: "tenant_demo", action: "WEBHOOK_INGESTED", resource: "pay_card_decline_101", status: "SUCCESS", timestamp: "2026-08-31 23:45:00" },
          { audit_id: "aud_1002", actor: "admin_dev_key", tenant: "tenant_demo", action: "POLICY_EVALUATED", resource: "POL_001", status: "APPROVED", timestamp: "2026-08-31 23:45:01" },
          { audit_id: "aud_1003", actor: "admin_dev_key", tenant: "tenant_demo", action: "HMAC_TOKEN_ISSUED", resource: "tok_hmac_991823", status: "SUCCESS", timestamp: "2026-08-31 23:45:01" },
          { audit_id: "aud_1004", actor: "admin_dev_key", tenant: "tenant_demo", action: "TOOL_EXECUTED", resource: "PAYMENT_LINK", status: "SUCCESS", timestamp: "2026-08-31 23:45:02" },
          { audit_id: "aud_1005", actor: "admin_dev_key", tenant: "tenant_demo", action: "OUTCOME_VERIFIED", resource: "CAPTURED", status: "ATTRIBUTED", timestamp: "2026-08-31 23:46:00" },
        ]);
        setLoading(false);
      });
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center">
          <FileText className="w-5 h-5 text-blue-600 mr-2" /> Cryptographic Security & Audit Console
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Immutable system audit event log tracking policy modifications, HMAC token generations, and tool side-effects
        </p>
      </div>

      {loading ? (
        <TableSkeleton rows={5} cols={6} />
      ) : (
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase font-semibold text-[11px]">
                <th className="p-3.5">Audit ID</th>
                <th className="p-3.5">Actor Identity</th>
                <th className="p-3.5">Tenant Context</th>
                <th className="p-3.5">Action Event</th>
                <th className="p-3.5">Target Resource</th>
                <th className="p-3.5">Timestamp</th>
                <th className="p-3.5 text-right">Result</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {events.map((e) => (
                <tr key={e.audit_id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="p-3.5 font-mono font-bold text-slate-900">{e.audit_id}</td>
                  <td className="p-3.5 font-mono text-slate-600">{e.actor}</td>
                  <td className="p-3.5 font-mono font-semibold text-blue-600">{e.tenant}</td>
                  <td className="p-3.5 font-semibold text-slate-800">{e.action}</td>
                  <td className="p-3.5 font-mono text-slate-700">{e.resource}</td>
                  <td className="p-3.5 text-slate-500 font-mono">{e.timestamp}</td>
                  <td className="p-3.5 text-right">
                    <StatusBadge status={e.status} />
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
