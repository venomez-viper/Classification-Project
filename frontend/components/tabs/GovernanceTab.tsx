"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  BadgeCheck,
  BookCheck,
  Boxes,
  Clock3,
  FileClock,
  Fingerprint,
  GitCommitHorizontal,
  Shield,
  ShieldAlert,
  Stamp,
  UserCheck,
} from "lucide-react";

type GateStatus = "approved" | "review" | "blocked";
type ReleaseItem = {
  id: string;
  asset: string;
  owner: string;
  scope: string;
  status: GateStatus;
  note: string;
};

type AuditEvent = {
  time: string;
  actor: string;
  action: string;
  impact: string;
};

const RELEASE_GATES: ReleaseItem[] = [
  {
    id: "REL-201",
    asset: "Task 1 LinearSVC",
    owner: "Akash",
    scope: "Industry deployment",
    status: "approved",
    note: "Weighted F1 remains above rubric threshold and rollback package is ready.",
  },
  {
    id: "REL-202",
    asset: "Task 2 LinearSVC",
    owner: "Subasree",
    scope: "Subindustry deployment",
    status: "review",
    note: "Rare-class confidence drift needs sign-off before the next promotion window.",
  },
  {
    id: "REL-203",
    asset: "ModernBERT Ensemble · HF Space",
    owner: "Akash",
    scope: "Task 1 inference path",
    status: "approved",
    note: "Calibrated ensemble locked at 75.0% Macro F1. Deployed on HF Space, proxied by Vercel.",
  },
];

const AUDIT_LOG: AuditEvent[] = [
  {
    time: "18:06 UTC",
    actor: "admin",
    action: "Alert sensitivity changed",
    impact: "Switched operator profile to balanced thresholds.",
  },
  {
    time: "17:42 UTC",
    actor: "admin",
    action: "Railway fallback reviewed",
    impact: "Confirmed local SVM continuity path for npm-side resilience.",
  },
  {
    time: "17:10 UTC",
    actor: "admin",
    action: "Homepage journey refreshed",
    impact: "Public showcase navigation updated and approved for release.",
  },
  {
    time: "16:31 UTC",
    actor: "admin",
    action: "LLM endpoint status noted",
    impact: "HF Space instability documented in operational register.",
  },
];

const statusStyle: Record<GateStatus, string> = {
  approved: "border-emerald-500/20 bg-emerald-500/8 text-emerald-300",
  review: "border-amber-500/20 bg-amber-500/8 text-amber-300",
  blocked: "border-red-500/20 bg-red-500/8 text-red-300",
};

const FILTERS = ["all", "approved", "review", "blocked"] as const;

export default function GovernanceTab() {
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>("all");

  const filteredGates = useMemo(() => {
    if (filter === "all") return RELEASE_GATES;
    return RELEASE_GATES.filter((item) => item.status === filter);
  }, [filter]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.35 }}
      className="max-w-[1500px] mx-auto pb-12 space-y-6"
    >
      <div className="flex items-end justify-between border-b border-red-500/20 pb-4 relative">
        <div className="absolute bottom-0 left-0 w-1/3 h-[1px] bg-gradient-to-r from-red-500 to-transparent" />
        <div>
          <h2 className="text-3xl font-black text-white tracking-widest uppercase">Governance Command</h2>
          <p className="text-xs text-red-500/50 mt-1 font-mono tracking-widest uppercase">
            approvals, traceability, risk posture, and release guardrails
          </p>
        </div>
        <div className="flex items-center gap-2">
          {FILTERS.map((value) => (
            <button
              key={value}
              onClick={() => setFilter(value)}
              className={`px-3 py-1.5 rounded-lg text-[10px] font-mono uppercase tracking-widest border transition-colors ${
                filter === value
                  ? "border-red-500/30 bg-red-500/10 text-red-300"
                  : "border-white/10 text-white/35 hover:text-white hover:bg-white/5"
              }`}
            >
              {value}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        {[
          { label: "Governance Score", value: "91 / 100", sub: "Control posture healthy" },
          { label: "Open Reviews", value: "3", sub: "1 blocked release" },
          { label: "Audit Coverage", value: "97%", sub: "Recent changes tracked" },
          { label: "Fallback Readiness", value: "SVM Ready", sub: "Local path verified" },
        ].map((item) => (
          <div key={item.label} className="rounded-xl border border-white/10 bg-black/50 p-4">
            <div className="text-[10px] font-mono text-white/30 uppercase tracking-widest">{item.label}</div>
            <div className="mt-2 text-2xl font-black font-mono text-white">{item.value}</div>
            <div className="text-[10px] text-white/35 mt-1">{item.sub}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-12 xl:col-span-8 border border-white/10 bg-[#0a0a0a] rounded-xl p-5">
          <div className="flex items-center gap-2 mb-5">
            <Stamp className="w-4 h-4 text-red-400" />
            <h3 className="text-xs font-bold text-white/60 tracking-widest uppercase">Release Approval Board</h3>
          </div>
          <div className="space-y-3">
            {filteredGates.map((item) => (
              <div key={item.id} className="border border-white/8 bg-black rounded-xl p-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-mono text-white/35">{item.id}</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-widest border ${statusStyle[item.status]}`}>
                        {item.status}
                      </span>
                    </div>
                    <div className="text-base font-semibold text-white mt-2">{item.asset}</div>
                    <div className="text-sm text-white/45 mt-1 leading-relaxed">{item.note}</div>
                    <div className="flex items-center gap-4 mt-3 text-[10px] font-mono text-white/35 uppercase tracking-widest flex-wrap">
                      <span>{item.scope}</span>
                      <span>Owner: {item.owner}</span>
                    </div>
                  </div>
                  <div className="text-right text-[10px] font-mono uppercase tracking-widest text-white/30">
                    ready for
                    <div className="text-white/60 mt-1">{item.status === "approved" ? "promotion" : item.status === "review" ? "committee review" : "remediation"}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="col-span-12 xl:col-span-4 flex flex-col gap-6">
          <div className="border border-white/10 bg-[#0a0a0a] rounded-xl p-5">
            <div className="flex items-center gap-2 mb-5">
              <Shield className="w-4 h-4 text-emerald-400" />
              <h3 className="text-xs font-bold text-white/60 tracking-widest uppercase">Control Stack</h3>
            </div>
            <div className="space-y-3">
              {[
                { icon: BookCheck, label: "Runbook coverage", value: "Complete" },
                { icon: UserCheck, label: "Owner assignment", value: "Mapped" },
                { icon: Fingerprint, label: "Change trace", value: "Logged" },
                { icon: BadgeCheck, label: "Rollback path", value: "Prepared" },
              ].map((item) => (
                <div key={item.label} className="flex items-center justify-between rounded-lg border border-white/8 bg-black px-3 py-3">
                  <div className="flex items-center gap-3">
                    <item.icon className="w-4 h-4 text-white/35" />
                    <span className="text-sm text-white/55">{item.label}</span>
                  </div>
                  <span className="text-[10px] font-mono uppercase tracking-widest text-emerald-400">
                    {item.value}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="border border-white/10 bg-[#0a0a0a] rounded-xl p-5">
            <div className="flex items-center gap-2 mb-5">
              <ShieldAlert className="w-4 h-4 text-amber-400" />
              <h3 className="text-xs font-bold text-white/60 tracking-widest uppercase">Risk Register</h3>
            </div>
            <div className="space-y-3 text-xs font-mono">
              {[
                "HF Space cold starts can widen response times during peak traffic.",
                "Task 2 long-tail classes remain the largest model quality exposure.",
                "GPU saturation may affect LLM continuity until workload shaping is added.",
                "Fallback messaging should stay aligned with real service status.",
              ].map((line) => (
                <div key={line} className="rounded-lg border border-white/8 bg-black px-3 py-3 text-white/45">
                  {line}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-12 xl:col-span-7 border border-white/10 bg-[#0a0a0a] rounded-xl p-5">
          <div className="flex items-center gap-2 mb-5">
            <FileClock className="w-4 h-4 text-cyan-400" />
            <h3 className="text-xs font-bold text-white/60 tracking-widest uppercase">Audit Trail</h3>
          </div>
          <div className="space-y-3">
            {AUDIT_LOG.map((event) => (
              <div key={`${event.time}-${event.action}`} className="rounded-lg border border-white/8 bg-black px-4 py-3">
                <div className="flex items-center justify-between gap-4 flex-wrap">
                  <div className="text-sm text-white">{event.action}</div>
                  <div className="text-[10px] font-mono uppercase tracking-widest text-white/30">
                    {event.time}
                  </div>
                </div>
                <div className="text-[10px] font-mono uppercase tracking-widest text-red-300 mt-2">
                  actor: {event.actor}
                </div>
                <div className="text-sm text-white/45 mt-2 leading-relaxed">{event.impact}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="col-span-12 xl:col-span-5 grid grid-cols-1 gap-6">
          <div className="border border-white/10 bg-[#0a0a0a] rounded-xl p-5">
            <div className="flex items-center gap-2 mb-5">
              <Boxes className="w-4 h-4 text-purple-300" />
              <h3 className="text-xs font-bold text-white/60 tracking-widest uppercase">Asset Traceability</h3>
            </div>
            <div className="space-y-3 text-xs font-mono">
              {[
                "Dataset lineage: Morningstar -> cleaned corpus -> train/test split",
                "Feature lineage: TF-IDF 50k task1, TF-IDF 10k task2",
                "Service lineage: Vercel -> Railway SVM -> HF Space / local LLM fallback",
                "Deployment lineage: main branch -> Vercel build -> health route verification",
              ].map((line) => (
                <div key={line} className="rounded-lg border border-white/8 bg-black px-4 py-3 text-white/45">
                  {line}
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-1 2xl:grid-cols-3 gap-4">
            {[
              { icon: GitCommitHorizontal, label: "Change reviews", value: "Committed" },
              { icon: Clock3, label: "Review cadence", value: "Daily" },
              { icon: Fingerprint, label: "Ownership map", value: "Tracked" },
            ].map((card) => (
              <div key={card.label} className="rounded-xl border border-white/10 bg-black/50 p-4 flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center">
                  <card.icon className="w-4 h-4 text-white/50" />
                </div>
                <div>
                  <div className="text-[10px] font-mono uppercase tracking-widest text-white/30">{card.label}</div>
                  <div className="text-sm text-white mt-1">{card.value}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
