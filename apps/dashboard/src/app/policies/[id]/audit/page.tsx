"use client";

import React from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { StatusBadge } from "../../../../components/StatusBadge";
import { ArrowLeft, Clock, History, ShieldCheck } from "lucide-react";

export default function PolicyAuditPage() {
  const params = useParams();
  const policyId = (params?.id as string) || "POL_001";

  const history = [
    { version: "v1.2.0", hash: "9a81f3b", author: "admin_dev_key", timestamp: "2026-08-31 23:10:00", action: "PARAMETER_UPDATE", status: "ACTIVE" },
    { version: "v1.1.0", hash: "4c72d1a", author: "admin_dev_key", timestamp: "2026-08-30 14:20:00", action: "RULE_MODIFICATION", status: "SUPERSEDED" },
    { version: "v1.0.0", hash: "1e00a99", author: "system_init", timestamp: "2026-08-15 09:00:00", action: "INITIAL_PROVISION", status: "SUPERSEDED" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-3">
        <Link
          href={`/policies/${policyId}`}
          className="p-1.5 bg-white border border-slate-200 rounded-lg text-slate-600 hover:text-slate-900 shadow-2xs"
        >
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight font-mono">{policyId} Immutable Audit History</h1>
            <StatusBadge status="ACTIVE" />
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Complete cryptographic version lineage & parameter modification audit trail
          </p>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase font-semibold text-[11px]">
              <th className="p-3.5">Version</th>
              <th className="p-3.5">SHA-256 Hash</th>
              <th className="p-3.5">Author</th>
              <th className="p-3.5">Action Type</th>
              <th className="p-3.5">Timestamp</th>
              <th className="p-3.5 text-right">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {history.map((h) => (
              <tr key={h.version} className="hover:bg-slate-50/80 transition-colors">
                <td className="p-3.5 font-mono font-bold text-blue-600">{h.version}</td>
                <td className="p-3.5 font-mono text-slate-700">{h.hash}</td>
                <td className="p-3.5 font-mono text-slate-600">{h.author}</td>
                <td className="p-3.5 font-semibold text-slate-800">{h.action}</td>
                <td className="p-3.5 text-slate-500 font-mono">{h.timestamp}</td>
                <td className="p-3.5 text-right">
                  <StatusBadge status={h.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
