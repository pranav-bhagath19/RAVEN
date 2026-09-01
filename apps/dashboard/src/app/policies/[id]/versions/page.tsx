"use client";

import { History, RotateCcw } from "lucide-react";

export default function PolicyVersionsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-extrabold text-slate-100 tracking-tight flex items-center">
          <History className="w-5 h-5 text-indigo-400 mr-2" /> Policy Lineage & Rollback Graph
        </h1>
        <p className="text-xs text-slate-400 mt-1">Immutable version history with transactional rollback capabilities</p>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="bg-slate-950/60 border-b border-slate-800 text-slate-400 uppercase font-semibold">
              <th className="p-3.5">Version</th>
              <th className="p-3.5">Status</th>
              <th className="p-3.5">Hash</th>
              <th className="p-3.5">Activated At</th>
              <th className="p-3.5 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            <tr className="hover:bg-slate-800/40">
              <td className="p-3.5 font-bold text-indigo-400">v2 (Current)</td>
              <td className="p-3.5"><span className="bg-emerald-950 text-emerald-400 border border-emerald-800/50 px-2 py-0.5 rounded font-bold text-[11px]">ACTIVE</span></td>
              <td className="p-3.5 font-mono text-slate-400 text-[11px]">hash_99a8b12</td>
              <td className="p-3.5 text-slate-300">Just now</td>
              <td className="p-3.5 text-right text-slate-500">Active Version</td>
            </tr>
            <tr className="hover:bg-slate-800/40">
              <td className="p-3.5 font-bold text-slate-400">v1 (Archived)</td>
              <td className="p-3.5"><span className="bg-slate-950 text-slate-400 border border-slate-800 px-2 py-0.5 rounded font-bold text-[11px]">SUPERSEDED</span></td>
              <td className="p-3.5 font-mono text-slate-400 text-[11px]">hash_1182371</td>
              <td className="p-3.5 text-slate-300">Yesterday</td>
              <td className="p-3.5 text-right">
                <button className="text-amber-400 hover:text-amber-300 font-semibold inline-flex items-center space-x-1">
                  <RotateCcw className="w-3 h-3" /> <span>Rollback to v1</span>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
