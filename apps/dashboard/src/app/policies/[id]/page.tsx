"use client";

import React, { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { StatusBadge } from "../../../components/StatusBadge";
import { Modal } from "../../../components/Modal";
import { ArrowLeft, Clock, History, Play, RotateCcw, ShieldCheck, Sliders } from "lucide-react";

export default function PolicyDetailPage() {
  const params = useParams();
  const policyId = (params?.id as string) || "POL_001";
  const [modalOpen, setModalOpen] = useState(false);
  const [modalLoading, setModalLoading] = useState(false);

  const handleRollback = () => {
    setModalLoading(true);
    setTimeout(() => {
      setModalLoading(false);
      setModalOpen(false);
    }, 800);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Link
            href="/policies"
            className="p-1.5 bg-white border border-slate-200 rounded-lg text-slate-600 hover:text-slate-900 shadow-2xs"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold text-slate-900 tracking-tight font-mono">{policyId}</h1>
              <StatusBadge status="ACTIVE" />
            </div>
            <p className="text-xs text-slate-500 mt-0.5">PolicyEngine Safety Rule Specification & Version Controls</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <Link
            href={`/policies/${policyId}/simulate`}
            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-lg shadow-xs flex items-center space-x-1"
          >
            <Play className="w-3.5 h-3.5" />
            <span>Simulate Policy</span>
          </Link>
          <button
            onClick={() => setModalOpen(true)}
            className="px-3 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded-lg shadow-xs flex items-center space-x-1"
          >
            <RotateCcw className="w-3.5 h-3.5 text-amber-600" />
            <span>Rollback Version</span>
          </button>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="flex space-x-4 border-b border-slate-200 text-xs font-bold">
        <span className="border-b-2 border-blue-600 text-blue-600 pb-2.5">Rule Specification</span>
        <Link href={`/policies/${policyId}/simulate`} className="text-slate-500 hover:text-slate-900 pb-2.5">
          Counterfactual Simulator
        </Link>
        <Link href={`/policies/${policyId}/audit`} className="text-slate-500 hover:text-slate-900 pb-2.5">
          Audit Trail
        </Link>
      </div>

      {/* Rule Specification Card */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
        <h3 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-3">Active Policy Parameters</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="p-3.5 bg-slate-50 border border-slate-200/80 rounded-lg">
            <span className="text-slate-500 font-semibold uppercase text-[10px]">Rule ID</span>
            <p className="font-mono font-bold text-slate-900 mt-1">{policyId}</p>
          </div>
          <div className="p-3.5 bg-slate-50 border border-slate-200/80 rounded-lg">
            <span className="text-slate-500 font-semibold uppercase text-[10px]">Active Version</span>
            <p className="font-mono font-bold text-blue-600 mt-1">v1.2.0 (Hash: 9a81f3b)</p>
          </div>
          <div className="p-3.5 bg-slate-50 border border-slate-200/80 rounded-lg">
            <span className="text-slate-500 font-semibold uppercase text-[10px]">Max Execution Ceiling</span>
            <p className="font-mono font-bold text-slate-900 mt-1">3 Retries / 24 Hours</p>
          </div>
          <div className="p-3.5 bg-slate-50 border border-slate-200/80 rounded-lg">
            <span className="text-slate-500 font-semibold uppercase text-[10px]">Veto Authority</span>
            <p className="font-semibold text-emerald-700 mt-1">Non-bypassable (POL_001 Safety invariant)</p>
          </div>
        </div>
      </div>

      {/* Rollback Confirmation Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onConfirm={handleRollback}
        title={`Rollback ${policyId} to Previous Version?`}
        description="This operation will deactivate version v1.2.0 and promote v1.1.0 as active in the PolicyEngine. All subsequent recovery decisions will evaluate against v1.1.0."
        confirmLabel="Confirm Rollback"
        variant="warning"
        isLoading={modalLoading}
      />
    </div>
  );
}
