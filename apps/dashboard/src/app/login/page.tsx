"use client";

import React, { useState } from "react";
import { setStoredAuth } from "@/lib/api";
import { ArrowRight, Eye, EyeOff, Key, Lock, ShieldCheck, Zap } from "lucide-react";

export default function LoginPage() {
  const [apiKey, setApiKey] = useState("admin_dev_key");
  const [tenantId, setTenantId] = useState("tenant_demo");
  const [showKey, setShowKey] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      if (!apiKey.trim()) {
        throw new Error("API Key is required");
      }
      setStoredAuth(apiKey, tenantId, "ADMIN");
      window.location.href = "/dashboard";
    } catch (err: any) {
      setError(err.message || "Failed to authenticate session");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex items-center justify-center p-4">
      <div className="max-w-4xl w-full grid grid-cols-1 md:grid-cols-2 bg-white rounded-2xl shadow-2xl overflow-hidden text-slate-900 border border-slate-200">
        {/* Left Branding Panel */}
        <div className="bg-[#0b1329] p-8 text-slate-100 flex flex-col justify-between relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-blue-600/10 rounded-full blur-3xl" />
          <div>
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white font-extrabold text-xl shadow-md">
                R
              </div>
              <span className="text-xl font-extrabold tracking-tight">RAVEN</span>
            </div>

            <div className="mt-12 space-y-4">
              <span className="text-xs font-mono font-bold text-blue-400 uppercase tracking-widest bg-blue-950/60 border border-blue-800/60 px-2.5 py-1 rounded-md">
                Razorpay AI Buildathon Track 03
              </span>
              <h2 className="text-2xl font-black text-white tracking-tight leading-tight">
                Autonomous Revenue Recovery Engine
              </h2>
              <p className="text-xs text-slate-400 leading-relaxed">
                Recover failed payments intelligently, safely, and automatically. Built with deterministic State Reconstruction, LinUCB Adaptive Intelligence, and non-bypassable PolicyEngine safety boundaries.
              </p>
            </div>
          </div>

          <div className="mt-8 space-y-3 pt-6 border-t border-slate-800">
            <div className="flex items-center text-xs text-slate-300">
              <ShieldCheck className="w-4 h-4 text-emerald-400 mr-2 shrink-0" />
              <span>AI recommends. PolicyEngine decides. RAVEN executes.</span>
            </div>
            <div className="flex items-center text-xs text-slate-300">
              <Lock className="w-4 h-4 text-blue-400 mr-2 shrink-0" />
              <span>HMAC-SHA256 Ephemeral PolicyApprovalTokens</span>
            </div>
          </div>
        </div>

        {/* Right Authentication Form */}
        <div className="p-8 flex flex-col justify-between">
          <div>
            <h3 className="text-lg font-bold text-slate-900">Operator Sign In</h3>
            <p className="text-xs text-slate-500 mt-1">Authenticate into RAVEN Control Plane</p>

            {error && (
              <div className="mt-4 p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg font-medium">
                {error}
              </div>
            )}

            <form onSubmit={handleLogin} className="mt-6 space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Tenant Context
                </label>
                <select
                  value={tenantId}
                  onChange={(e) => setTenantId(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs font-semibold text-slate-800 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                >
                  <option value="tenant_demo">tenant_demo (Razorpay Merchant)</option>
                  <option value="tenant_acme">tenant_acme (Enterprise Merchant)</option>
                  <option value="tenant_global">tenant_global (Global Merchant)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  API Credentials / Secret Key
                </label>
                <div className="relative">
                  <input
                    type={showKey ? "text" : "password"}
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="Enter API key..."
                    className="w-full bg-slate-50 border border-slate-300 rounded-lg pl-3 pr-10 py-2 text-xs font-mono text-slate-900 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  />
                  <button
                    type="button"
                    onClick={() => setShowKey(!showKey)}
                    className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600"
                  >
                    {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                <p className="text-[11px] text-slate-400 mt-1">Default operator key: <code className="font-mono text-slate-600">admin_dev_key</code></p>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2.5 px-4 rounded-lg text-xs transition-colors shadow-xs flex items-center justify-center space-x-2 mt-6"
              >
                <span>{loading ? "Authenticating..." : "Access Control Plane"}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </form>
          </div>

          <div className="mt-8 pt-4 border-t border-slate-100 text-center">
            <p className="text-[11px] text-slate-400">
              Razorpay AI Buildathon Track 03 — Autonomous Revenue Recovery
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
