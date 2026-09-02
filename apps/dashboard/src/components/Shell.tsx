"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Activity,
  ArrowLeftRight,
  BarChart3,
  Bell,
  CheckSquare,
  ChevronRight,
  CreditCard,
  FileText,
  FlaskConical,
  GitCommit,
  Home,
  Layers,
  Lock,
  LogOut,
  Menu,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
  Users,
  X,
  Zap,
} from "lucide-react";
import { getStoredAuth } from "@/lib/api";

interface ShellProps {
  children: React.ReactNode;
}

export function Shell({ children }: ShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [testMode, setTestMode] = useState(true);
  const [auth, setAuth] = useState({ apiKey: "", tenantId: "", role: "" });

  useEffect(() => {
    if (typeof window !== "undefined") {
      setAuth(getStoredAuth());
    }
  }, []);

  const handleLogout = () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("raven_api_key");
      router.push("/login");
    }
  };

  const getBreadcrumb = () => {
    if (pathname.includes("/payments/")) return "Transactions / Trace Detail";
    if (pathname.includes("/policies/")) return "Policy Engine / Rule Inspector";
    if (pathname.includes("/intelligence/")) return "AI Intelligence / ML Registry";
    if (pathname === "/dashboard" || pathname === "/") return "Home";
    if (pathname === "/payments") return "Transactions";
    if (pathname === "/recoveries") return "Recoveries";
    if (pathname === "/decisions") return "Decision Traces";
    if (pathname === "/policies") return "Policy Engine";
    if (pathname === "/intelligence") return "AI Intelligence";
    if (pathname === "/tenants") return "Tenants";
    if (pathname === "/operations") return "System Operations";
    if (pathname === "/audit") return "Audit Logs";
    if (pathname === "/settings") return "Account & Settings";
    if (pathname === "/admin") return "Admin Control";
    return "Dashboard";
  };

  const mainNavItems = [
    { name: "Home", href: "/dashboard", icon: Home },
    { name: "Transactions", href: "/payments", icon: ArrowLeftRight },
    { name: "Recoveries", href: "/recoveries", icon: CheckSquare },
    { name: "Decision Traces", href: "/decisions", icon: FileText },
  ];

  const productNavItems = [
    { name: "Policy Engine", href: "/policies", icon: ShieldCheck, badge: "POL_001-007" },
    { name: "AI Intelligence", href: "/intelligence", icon: Sparkles, badge: "LinUCB" },
    { name: "Tenant Portfolio", href: "/tenants", icon: Users },
    { name: "System Operations", href: "/operations", icon: Activity },
    { name: "Audit Trail", href: "/audit", icon: GitCommit },
  ];

  return (
    <div className="min-h-screen bg-[#f4f5f8] text-[#0f172a] flex font-sans antialiased">
      {/* Sidebar Desktop Container */}
      <aside className="hidden md:flex flex-col w-64 bg-black text-slate-900 shrink-0 select-none border-r border-slate-200">
        {/* Black Top Header with Text-Only RAVEN Branding */}
        <div className="bg-black text-white px-5 py-4 flex items-center justify-between">
          <Link href="/dashboard" className="flex items-center space-x-2">
            <div className="flex items-center space-x-2">
              <span className="font-black text-2xl tracking-tight text-white font-sans">RAVEN</span>
              <span className="text-[10px] font-extrabold uppercase bg-[#0570DE] text-white px-2 py-0.5 rounded font-mono tracking-wider">
                RECOVERY
              </span>
            </div>
          </Link>
        </div>

        {/* Razorpay Sidebar Container */}
        <div className="flex-1 bg-[#f4f5f7] rounded-t-2xl border-t border-slate-200 px-3 py-4 flex flex-col justify-between overflow-y-auto">
          <div className="space-y-6">
            {/* Primary Main Menu */}
            <div className="space-y-1">
              {mainNavItems.map((item) => {
                const Icon = item.icon;
                const active = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`flex items-center px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                      active
                        ? "bg-[#e2e8f0] text-slate-900 font-bold shadow-2xs"
                        : "text-slate-700 hover:bg-slate-200/60 hover:text-slate-900"
                    }`}
                  >
                    <Icon className={`w-4 h-4 mr-3.5 ${active ? "text-slate-900" : "text-slate-600"}`} />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
            </div>

            {/* Category Header: RECOVERY PRODUCTS */}
            <div>
              <div className="px-3.5 text-[11px] font-extrabold text-slate-400 uppercase tracking-wider mb-2">
                RECOVERY PRODUCTS
              </div>
              <div className="space-y-1">
                {productNavItems.map((item) => {
                  const Icon = item.icon;
                  const active = pathname === item.href || pathname.startsWith(item.href);
                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      className={`flex items-center justify-between px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                        active
                          ? "bg-[#e2e8f0] text-slate-900 font-bold shadow-2xs"
                          : "text-slate-700 hover:bg-slate-200/60 hover:text-slate-900"
                      }`}
                    >
                      <div className="flex items-center">
                        <Icon className={`w-4 h-4 mr-3.5 ${active ? "text-[#0570DE]" : "text-slate-600"}`} />
                        <span>{item.name}</span>
                      </div>
                      {item.badge && (
                        <span className="text-[10px] font-bold bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full border border-emerald-200">
                          {item.badge}
                        </span>
                      )}
                    </Link>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Bottom Fixed Footer Section */}
          <div className="pt-4 border-t border-slate-200/80 space-y-1 mt-6">
            {/* Test Mode Toggle Switch */}
            <div className="flex items-center justify-between px-3.5 py-2.5 text-sm font-medium text-slate-800 hover:bg-slate-200/40 rounded-lg cursor-pointer">
              <div className="flex items-center">
                <FlaskConical className="w-4 h-4 mr-3.5 text-slate-700" />
                <span className="font-semibold">Test Mode</span>
              </div>
              <button
                type="button"
                onClick={() => setTestMode(!testMode)}
                className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                  testMode ? "bg-[#0570DE]" : "bg-slate-300"
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out ${
                    testMode ? "translate-x-4" : "translate-x-0"
                  }`}
                />
              </button>
            </div>

            {/* Account & Settings Link */}
            <Link
              href="/settings"
              className={`flex items-center px-3.5 py-2.5 rounded-lg text-sm font-medium ${
                pathname === "/settings"
                  ? "bg-[#e2e8f0] text-slate-900 font-bold"
                  : "text-slate-700 hover:bg-slate-200/60 hover:text-slate-900"
              }`}
            >
              <Settings className="w-4 h-4 mr-3.5 text-slate-600" />
              <span>Account & Settings</span>
            </Link>

            {/* Operator Identity & Logout */}
            <div className="px-3.5 py-2 mt-2 flex items-center justify-between text-xs text-slate-500 bg-white/60 border border-slate-200 rounded-lg">
              <div className="truncate">
                <span className="font-bold text-slate-800 block truncate">{auth.tenantId}</span>
                <span className="text-[10px] font-mono text-slate-500 uppercase">{auth.role}</span>
              </div>
              <button
                onClick={handleLogout}
                title="Sign Out"
                className="text-slate-400 hover:text-rose-600 p-1 hover:bg-slate-100 rounded"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </aside>

      {/* Mobile Drawer Navigation */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden">
          <div className="fixed inset-0 bg-slate-900/60" onClick={() => setMobileMenuOpen(false)} />
          <div className="relative w-64 bg-[#f4f5f7] text-slate-900 flex flex-col h-full z-10 border-r border-slate-200">
            <div className="p-4 bg-black text-white flex items-center justify-between">
              <span className="font-bold text-lg">RAVEN Engine</span>
              <button onClick={() => setMobileMenuOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>
            <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
              {mainNavItems.concat(productNavItems).map((item) => {
                const Icon = item.icon;
                const active = pathname === item.href;
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center px-3 py-2.5 rounded-lg text-sm font-semibold ${
                      active ? "bg-slate-200 text-slate-900" : "text-slate-700 hover:bg-slate-100"
                    }`}
                  >
                    <Icon className="w-4 h-4 mr-3" />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
            </nav>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header */}
        <header className="bg-white border-b border-slate-200 px-6 py-3.5 flex items-center justify-between shrink-0 shadow-2xs">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="md:hidden p-1.5 text-slate-600 hover:text-slate-900 rounded-md border border-slate-200"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div className="flex items-center space-x-2 text-xs font-medium text-slate-500">
              <span className="font-bold text-slate-800 font-sans">RAVEN Engine</span>
              <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
              <span className="font-bold text-slate-900">{getBreadcrumb()}</span>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {/* Quick Search */}
            <div className="hidden sm:flex items-center space-x-2 bg-slate-100 px-3 py-1.5 rounded-md border border-slate-200 w-56 lg:w-72 focus-within:border-[#0570DE] focus-within:ring-1 focus-within:ring-[#0570DE] transition-all">
              <Search className="w-3.5 h-3.5 text-slate-400" />
              <input
                type="text"
                placeholder="Search Payment or Trace ID..."
                className="bg-transparent text-xs text-slate-800 placeholder-slate-400 focus:outline-none w-full font-sans"
              />
            </div>

            {/* Test Mode Live Indicator */}
            {testMode && (
              <div className="hidden sm:flex items-center space-x-2 bg-amber-50 text-amber-800 px-2.5 py-1 rounded-md border border-amber-200 text-xs font-bold font-sans">
                <FlaskConical className="w-3.5 h-3.5 text-amber-600" />
                <span>TEST MODE</span>
              </div>
            )}

            {/* Notification Bell */}
            <button
              title="Notifications"
              className="p-1.5 text-slate-500 hover:text-slate-800 rounded-lg hover:bg-slate-100 transition-colors relative"
            >
              <Bell className="w-4 h-4" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-[#0570DE] rounded-full" />
            </button>
          </div>
        </header>

        {/* Page Main Body */}
        <main className="flex-1 p-6 overflow-y-auto max-w-7xl w-full mx-auto">{children}</main>
      </div>
    </div>
  );
}
