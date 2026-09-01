"use client";

import React, { useState } from "react";
import { StatusBadge } from "@/components/StatusBadge";
import { CheckCircle2, Key, Lock, Mail, MessageSquare, Save, Settings, ShieldCheck, Sliders } from "lucide-react";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("general");

  const tabs = [
    { id: "general", label: "General & Tenant" },
    { id: "security", label: "Security & HMAC" },
    { id: "razorpay", label: "Razorpay Test Mode" },
    { id: "notifications", label: "Notification Channels" },
    { id: "ai", label: "AI & LLM Provider" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center">
          <Settings className="w-5 h-5 text-blue-600 mr-2" /> Platform Settings & Credentials Status
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          System configurations and provider connection statuses (Sensitive keys are masked per security invariants)
        </p>
      </div>

      {/* Tabs */}
      <div className="flex space-x-2 border-b border-slate-200 text-xs font-bold">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={`pb-2.5 px-3 border-b-2 transition-colors ${
              activeTab === t.id ? "border-blue-600 text-blue-600 font-bold" : "border-transparent text-slate-500 hover:text-slate-900"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
        {activeTab === "general" && (
          <div className="space-y-4 text-xs">
            <h3 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">Tenant Configuration</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1">Active Tenant ID</label>
                <input
                  type="text"
                  disabled
                  value="tenant_demo"
                  className="w-full bg-slate-100 border border-slate-200 rounded-lg px-3 py-2 text-slate-700 font-mono font-bold"
                />
              </div>
              <div>
                <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1">Default Policy Profile</label>
                <input
                  type="text"
                  disabled
                  value="POL_001_DEFAULT"
                  className="w-full bg-slate-100 border border-slate-200 rounded-lg px-3 py-2 text-slate-700 font-mono font-bold"
                />
              </div>
            </div>
          </div>
        )}

        {activeTab === "security" && (
          <div className="space-y-4 text-xs">
            <h3 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">Cryptographic Keys</h3>
            <div className="space-y-3">
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg flex items-center justify-between">
                <div>
                  <span className="font-bold text-slate-800">RAVEN Policy HMAC Key</span>
                  <p className="text-slate-500 text-[11px]">Used for PolicyApprovalToken HMAC-SHA256 signatures</p>
                </div>
                <StatusBadge status="CONFIGURED (MASKED)" />
              </div>
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg flex items-center justify-between">
                <div>
                  <span className="font-bold text-slate-800">API Key Authentication Provider</span>
                  <p className="text-slate-500 text-[11px]">SHA-256 hashed API key validation</p>
                </div>
                <StatusBadge status="ACTIVE" />
              </div>
            </div>
          </div>
        )}

        {activeTab === "razorpay" && (
          <div className="space-y-4 text-xs">
            <h3 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">Razorpay Integration Credentials</h3>
            <div className="space-y-3">
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg flex items-center justify-between">
                <div>
                  <span className="font-bold text-slate-800">Razorpay Key ID</span>
                  <p className="text-slate-500 font-mono text-[11px]">rzp_test_***</p>
                </div>
                <StatusBadge status="CONFIGURED" />
              </div>
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg flex items-center justify-between">
                <div>
                  <span className="font-bold text-slate-800">Razorpay Webhook Secret</span>
                  <p className="text-slate-500 font-mono text-[11px]">RAZORPAY_WEBHOOK_SECRET</p>
                </div>
                <StatusBadge status="CONFIGURED (MASKED)" />
              </div>
            </div>
          </div>
        )}

        {activeTab === "notifications" && (
          <div className="space-y-4 text-xs">
            <h3 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">Multichannel Notification Adapters</h3>
            <div className="space-y-3">
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg flex items-center justify-between">
                <div>
                  <span className="font-bold text-slate-800">SendGrid Email Provider</span>
                  <p className="text-slate-500 text-[11px]">Email dispatch for recovery links</p>
                </div>
                <StatusBadge status="CONFIGURED (MASKED)" />
              </div>
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg flex items-center justify-between">
                <div>
                  <span className="font-bold text-slate-800">Twilio SMS / WhatsApp Adapter</span>
                  <p className="text-slate-500 text-[11px]">Direct SMS and WhatsApp messaging</p>
                </div>
                <StatusBadge status="CONFIGURED (MASKED)" />
              </div>
            </div>
          </div>
        )}

        {activeTab === "ai" && (
          <div className="space-y-4 text-xs">
            <h3 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">AI Provider Credentials</h3>
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg flex items-center justify-between">
              <div>
                <span className="font-bold text-slate-800">OpenAI API Key (GPT-4o)</span>
                <p className="text-slate-500 font-mono text-[11px]">OPENAI_API_KEY</p>
              </div>
              <StatusBadge status="CONFIGURED (MASKED)" />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
