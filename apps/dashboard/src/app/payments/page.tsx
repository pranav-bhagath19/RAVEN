"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { fetchApi } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { TableSkeleton } from "@/components/SkeletonLoader";
import { CreditCard, ExternalLink, Filter, RefreshCw, Search } from "lucide-react";

interface PaymentItem {
  payment_id: string;
  order_id: string;
  merchant_id: string;
  customer_id: string;
  amount_minor: number;
  currency: string;
  status: string;
  error_code: string | null;
  created_at: string;
  recovery_status?: string;
  recommended_action?: string;
}

export default function PaymentsPage() {
  const [payments, setPayments] = useState<PaymentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");

  useEffect(() => {
    fetchApi<any>("/operations/payments")
      .then((res) => {
        const list = Array.isArray(res) ? res : res?.items || [];
        setPayments(list);
        setLoading(false);
      })
      .catch(() => {
        setPayments([]);
        setLoading(false);
      });
  }, []);

  const filtered = payments.filter((p) => {
    const matchesSearch =
      p.payment_id.toLowerCase().includes(search.toLowerCase()) ||
      p.customer_id.toLowerCase().includes(search.toLowerCase()) ||
      (p.error_code || "").toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === "ALL" || p.status.toUpperCase() === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center">
            <CreditCard className="w-5 h-5 text-blue-600 mr-2" /> Failed Payments Directory
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Ingested Razorpay payment failures subject to autonomous revenue recovery
          </p>
        </div>
      </div>

      {/* Filter & Search Toolbar */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center space-x-2 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg w-full sm:w-80 focus-within:border-blue-500 transition-colors">
          <Search className="w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search Payment ID, Customer, Error..."
            className="bg-transparent text-xs text-slate-800 placeholder-slate-400 focus:outline-none w-full"
          />
        </div>

        <div className="flex items-center space-x-3 w-full sm:w-auto">
          <div className="flex items-center space-x-1.5 text-xs text-slate-600 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg">
            <Filter className="w-3.5 h-3.5 text-slate-500" />
            <span className="font-semibold">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-transparent text-xs font-bold text-slate-800 focus:outline-none"
            >
              <option value="ALL">All Statuses</option>
              <option value="FAILED">FAILED</option>
              <option value="RECOVERED">RECOVERED</option>
              <option value="CAPTURED">CAPTURED</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Payments Table */}
      {loading ? (
        <TableSkeleton rows={5} cols={6} />
      ) : (
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase font-semibold text-[11px]">
                <th className="p-3.5">Payment ID</th>
                <th className="p-3.5">Customer</th>
                <th className="p-3.5">Amount</th>
                <th className="p-3.5">Error Code</th>
                <th className="p-3.5">Payment Status</th>
                <th className="p-3.5">Action</th>
                <th className="p-3.5 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-xs text-slate-400 font-medium">
                    No failed payments matched the filter criteria.
                  </td>
                </tr>
              ) : (
                filtered.map((p) => (
                  <tr key={p.payment_id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="p-3.5 font-mono font-bold text-slate-900">{p.payment_id}</td>
                    <td className="p-3.5 font-mono text-slate-600">{p.customer_id}</td>
                    <td className="p-3.5 font-bold text-slate-900 font-mono">
                      ₹{(p.amount_minor / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                    </td>
                    <td className="p-3.5">
                      <span className="bg-slate-100 text-slate-700 font-mono text-[11px] px-2 py-0.5 rounded border border-slate-200">
                        {p.error_code || "BAD_REQUEST_PAYMENT_DECLINED"}
                      </span>
                    </td>
                    <td className="p-3.5">
                      <StatusBadge status={p.status} />
                    </td>
                    <td className="p-3.5">
                      <span className="bg-blue-50 text-blue-700 text-[11px] font-bold px-2 py-0.5 rounded border border-blue-200">
                        {p.recommended_action || "SMART_RETRY"}
                      </span>
                    </td>
                    <td className="p-3.5 text-right">
                      <Link
                        href={`/payments/${p.payment_id}`}
                        className="inline-flex items-center space-x-1 text-blue-600 hover:text-blue-800 font-semibold"
                      >
                        <span>View Trace</span>
                        <ExternalLink className="w-3 h-3" />
                      </Link>
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
