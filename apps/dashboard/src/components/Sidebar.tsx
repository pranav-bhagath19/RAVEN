"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  CreditCard,
  RotateCcw,
  GitCommit,
  BrainCircuit,
  Sliders,
  Building2,
  Activity,
  FileCheck,
  Settings,
  ShieldAlert,
} from "lucide-react";

const navItems = [
  { name: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { name: "Failed Payments", href: "/payments", icon: CreditCard },
  { name: "Recoveries", href: "/recoveries", icon: RotateCcw },
  { name: "Decision Traces", href: "/decisions", icon: GitCommit },
  { name: "Intelligence & ML", href: "/intelligence", icon: BrainCircuit },
  { name: "Policy Engine", href: "/policies", icon: Sliders },
  { name: "Tenants", href: "/tenants", icon: Building2 },
  { name: "Operations Queue", href: "/operations", icon: Activity },
  { name: "Audit Trail", href: "/audit", icon: FileCheck },
  { name: "Settings & Keys", href: "/settings", icon: Settings },
  { name: "Platform Admin", href: "/admin", icon: ShieldAlert },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-900/60 p-4 flex flex-col justify-between hidden md:flex min-h-[calc(100vh-4rem)]">
      <nav className="space-y-1">
        <div className="px-3 py-2 text-xs font-semibold uppercase text-slate-500 tracking-wider">
          Navigation
        </div>
        {navItems.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center space-x-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                isActive
                  ? "bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 shadow-sm shadow-indigo-900/30"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? "text-indigo-400" : "text-slate-400"}`} />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      <div className="p-3 bg-slate-800/40 rounded-lg border border-slate-800 text-[11px] text-slate-500 space-y-1">
        <div className="font-semibold text-slate-400">RAVEN Autonomous Engine</div>
        <div>Version 1.0.0 (Production)</div>
        <div className="text-emerald-500 flex items-center space-x-1 pt-1">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>Engine Active</span>
        </div>
      </div>
    </aside>
  );
}
