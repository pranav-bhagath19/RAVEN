"use client";

import React, { useState } from "react";
import { StatusBadge } from "../../components/StatusBadge";
import { Modal } from "../../components/Modal";
import { AlertTriangle, Lock, ShieldCheck, UserCheck, Users } from "lucide-react";

export default function AdminPage() {
  const [modalOpen, setModalOpen] = useState(false);
  const [modalLoading, setModalLoading] = useState(false);

  const users = [
    { username: "admin_dev_key", role: "ADMIN", tenant: "tenant_demo", status: "ACTIVE", last_login: "2026-08-31 23:50" },
    { username: "op_merchant_01", role: "OPERATOR", tenant: "tenant_demo", status: "ACTIVE", last_login: "2026-08-31 20:12" },
    { username: "auditor_sec_01", role: "AUDITOR", tenant: "tenant_demo", status: "ACTIVE", last_login: "2026-08-30 18:00" },
  ];

  const handleAction = () => {
    setModalLoading(true);
    setTimeout(() => {
      setModalLoading(false);
      setModalOpen(false);
    }, 800);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center">
            <Lock className="w-5 h-5 text-indigo-600 mr-2" /> Platform Administration & RBAC Controls
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            User roles, API key authorization, and global platform security boundaries
          </p>
        </div>

        <button
          onClick={() => setModalOpen(true)}
          className="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold rounded-lg shadow-xs transition-colors flex items-center space-x-1"
        >
          <AlertTriangle className="w-3.5 h-3.5" />
          <span>Purge Test Keys</span>
        </button>
      </div>

      {/* RBAC Schema Notice */}
      <div className="bg-slate-100 border border-slate-300 text-[#0f172a] rounded-xl p-4 flex items-center space-x-3">
        <ShieldCheck className="w-5 h-5 text-indigo-600 shrink-0" />
        <div className="text-xs">
          <span className="font-bold text-slate-800">RBAC Security Permission Matrix: </span>
          <span className="text-slate-600">
            Authorization is strictly enforced by server-side UserIdentity (`X-API-Key` & `X-Tenant-ID`). Roles below illustrate configured access permissions (ADMIN, OPERATOR, AUDITOR).
          </span>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase font-semibold text-[11px]">
              <th className="p-3.5">User Identity / API Key</th>
              <th className="p-3.5">Assigned Role</th>
              <th className="p-3.5">Tenant Scope</th>
              <th className="p-3.5">Last Active</th>
              <th className="p-3.5 text-right">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {users.map((u) => (
              <tr key={u.username} className="hover:bg-slate-50/80 transition-colors">
                <td className="p-3.5 font-mono font-bold text-slate-900">{u.username}</td>
                <td className="p-3.5 font-semibold text-blue-600">{u.role}</td>
                <td className="p-3.5 font-mono text-slate-700">{u.tenant}</td>
                <td className="p-3.5 text-slate-500 font-mono">{u.last_login}</td>
                <td className="p-3.5 text-right">
                  <StatusBadge status={u.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onConfirm={handleAction}
        title="Purge Revoked Operator Keys?"
        description="This administrative action will permanently purge all revoked API keys from the user repository. Active sessions will remain unaffected."
        confirmLabel="Confirm Key Purge"
        variant="danger"
        isLoading={modalLoading}
      />
    </div>
  );
}
