"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { fetchApi } from "@/lib/api";
import { DecisionLineage } from "@/components/DecisionLineage";
import { StatusBadge } from "@/components/StatusBadge";
import {
  AlertCircle,
  ArrowLeft,
  Brain,
  CheckCircle2,
  Clock,
  CreditCard,
  Database,
  GitCommit,
  Key,
  Lock,
  ShieldCheck,
  Zap,
} from "lucide-react";

export default function PaymentDetailPage() {
  const params = useParams();
  const paymentId = (params?.id as string) || "";
  const [loading, setLoading] = useState(true);
  const [detail, setDetail] = useState<any>(null);

  useEffect(() => {
    if (!paymentId) {
      setLoading(false);
      return;
    }
    fetchApi<any>(`/operations/traces/${paymentId}`)
      .then((res) => {
        setDetail(res);
        setLoading(false);
      })
      .catch(() => {
        setDetail(null);
        setLoading(false);
      });
  }, [paymentId]);

  if (!loading && !detail) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-3">
          <Link
            href="/payments"
            className="p-1.5 bg-white border border-slate-200 rounded-lg text-slate-600 hover:text-slate-900 shadow-2xs"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <h1 className="text-xl font-bold text-slate-900 font-mono">{paymentId || "Unknown Payment"}</h1>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center text-slate-500">
          <AlertCircle className="w-8 h-8 text-amber-500 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-slate-800">Payment Trace Not Found</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
            No reconstructed state or DecisionTrace record was found for ID <code className="font-mono">{paymentId}</code>.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Header Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Link
            href="/payments"
            className="p-1.5 bg-white border border-slate-200 rounded-lg text-slate-600 hover:text-slate-900 shadow-2xs"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold text-slate-900 tracking-tight font-mono">{paymentId}</h1>
              <StatusBadge status={detail?.verification_result || detail?.status || "UNKNOWN"} />
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Reconstructed payment state & chronological DecisionTrace
            </p>
          </div>
        </div>
      </div>

      {/* Decision Lineage Flow Component */}
      <DecisionLineage
        paymentId={paymentId}
        rootCause={detail?.root_cause || "UNKNOWN"}
        actionType={detail?.recommended_action || detail?.selected_action || "NONE"}
        propensityScore={detail?.propensity_score || 0}
        expectedValueINR={(detail?.expected_value_minor || 0) / 100}
        policyDecision={detail?.policy_decision || "PENDING"}
        tokenVerified={!!detail?.policy_token_id}
        executionStatus={detail?.execution_result || "NONE"}
        verificationStatus={detail?.verification_result || "PENDING"}
      />

      {/* Grid: Payment Summary Card & Security Invariant Panel */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Payment Metadata Panel */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider border-b border-slate-100 pb-3 mb-4 flex items-center">
            <CreditCard className="w-4 h-4 text-blue-600 mr-2" /> Reconstructed Payment Metadata
          </h3>
          <div className="space-y-3 text-xs">
            <div className="flex justify-between py-1.5 border-b border-slate-50">
              <span className="text-slate-500 font-medium">Merchant ID</span>
              <span className="font-mono font-bold text-slate-800">{detail?.merchant_id || "N/A"}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-50">
              <span className="text-slate-500 font-medium">Customer ID</span>
              <span className="font-mono font-bold text-slate-800">{detail?.customer_id || "N/A"}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-50">
              <span className="text-slate-500 font-medium">Original Amount</span>
              <span className="font-mono font-bold text-slate-900">
                ₹{((detail?.amount_minor || 0) / 100).toFixed(2)}
              </span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-50">
              <span className="text-slate-500 font-medium">Propensity Score</span>
              <span className="font-mono font-bold text-blue-600">
                {((detail?.propensity_score || 0) * 100).toFixed(0)}%
              </span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-slate-500 font-medium">Expected Value (EV)</span>
              <span className="font-mono font-bold text-emerald-600">
                ₹{((detail?.expected_value_minor || 0) / 100).toFixed(2)}
              </span>
            </div>
          </div>
        </div>

        {/* Policy & Security Verification Panel */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider border-b border-slate-100 pb-3 mb-4 flex items-center">
            <ShieldCheck className="w-4 h-4 text-emerald-600 mr-2" /> Policy & Cryptographic Verification
          </h3>
          <div className="space-y-3 text-xs">
            <div className="flex justify-between py-1.5 border-b border-slate-50">
              <span className="text-slate-500 font-medium">Policy Engine Evaluation</span>
              <StatusBadge status={detail?.policy_decision || "PENDING"} />
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-50">
              <span className="text-slate-500 font-medium">HMAC Approval Token</span>
              <span className="font-mono font-bold text-purple-700 bg-purple-50 px-2 py-0.5 rounded border border-purple-200">
                {detail?.policy_token_id || "NONE"}
              </span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-50">
              <span className="text-slate-500 font-medium">Side-Effect Lock</span>
              <span className="font-mono font-semibold text-emerald-700">Idempotent Protected</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-slate-500 font-medium">Ground-Truth Verification</span>
              <span className="font-mono font-semibold text-emerald-700">{detail?.verification_result || "PENDING"}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
