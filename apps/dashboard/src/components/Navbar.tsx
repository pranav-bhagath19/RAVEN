"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ShieldCheck, LogOut, Key, Building } from "lucide-react";
import { getStoredAuth } from "../lib/api";

export default function Navbar() {
  const router = useRouter();
  const [auth, setAuth] = useState({ apiKey: "", tenantId: "", role: "" });

  useEffect(() => {
    setAuth(getStoredAuth());
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("raven_api_key");
    router.push("/login");
  };

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/80 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center space-x-3">
        <div className="bg-indigo-600/20 text-indigo-400 p-2 rounded-lg border border-indigo-500/30">
          <ShieldCheck className="w-5 h-5 text-indigo-400" />
        </div>
        <div>
          <span className="font-extrabold tracking-wider text-slate-100 text-lg">RAVEN</span>
          <span className="text-xs text-indigo-400 font-semibold ml-2 bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-800/40">
            CONTROL PLANE
          </span>
        </div>
      </div>

      <div className="flex items-center space-x-6">
        <div className="flex items-center space-x-2 text-xs text-slate-400 bg-slate-800/60 px-3 py-1.5 rounded-md border border-slate-700/50">
          <Building className="w-3.5 h-3.5 text-indigo-400" />
          <span>Tenant:</span>
          <span className="font-mono text-slate-200 font-medium">{auth.tenantId || "tenant_demo"}</span>
        </div>

        <div className="flex items-center space-x-2 text-xs text-slate-400 bg-slate-800/60 px-3 py-1.5 rounded-md border border-slate-700/50">
          <Key className="w-3.5 h-3.5 text-emerald-400" />
          <span>Role:</span>
          <span className="font-semibold text-emerald-400">{auth.role || "ADMIN"}</span>
        </div>

        <button
          onClick={handleLogout}
          className="text-xs flex items-center space-x-1.5 text-slate-400 hover:text-rose-400 transition-colors bg-slate-800/40 hover:bg-rose-950/30 px-3 py-1.5 rounded-md border border-slate-700/40 hover:border-rose-900/40"
        >
          <LogOut className="w-3.5 h-3.5" />
          <span>Sign Out</span>
        </button>
      </div>
    </header>
  );
}
