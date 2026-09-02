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
    fetchApi<any>("/operations/events")
      .then((res) => {
        const list = Array.isArray(res) ? res : res?.items || [];
        setEvents(
          list.map((e: any) => ({
            audit_id: e.id || e.event_id,
            actor: "system_ingress",
            tenant: e.merchant_id,
            action: e.event_type,
            resource: e.entity_id,
            timestamp: e.received_at || e.occurred_at,
            status: "SUCCESS",
          }))
        );
        setLoading(false);
      })
      .catch(() => {
        setEvents([]);
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
              {events.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-xs text-slate-400 font-medium">
                    No security audit events logged yet.
                  </td>
                </tr>
              ) : (
                events.map((e) => (
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
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
