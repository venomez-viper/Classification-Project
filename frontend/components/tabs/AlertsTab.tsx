"use client";

import type { ElementType } from "react";
import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  Bell,
  CheckCircle2,
  Clock3,
  Filter,
  Mail,
  MessageSquare,
  ShieldAlert,
  Siren,
} from "lucide-react";

type Severity = "critical" | "warning" | "info";
type AlertItem = {
  id: string;
  source: string;
  title: string;
  detail: string;
  time: string;
  severity: Severity;
  owner: string;
  status: "open" | "acked" | "resolved";
};

const ALERTS: AlertItem[] = [
  {
    id: "ALT-001",
    source: "HF Space",
    title: "HF Space cold start latency spike",
    detail: "Inference latency crossed 35s during cold start - Space was sleeping.",
    time: "2 min ago",
    severity: "critical",
    owner: "Akash",
    status: "open",
  },
  {
    id: "ALT-002",
    source: "Railway API",
    title: "Task 2 confidence dip",
    detail: "Subindustry confidence dropped below the expected threshold on recent runs.",
    time: "9 min ago",
    severity: "warning",
    owner: "Subasree",
    status: "acked",
  },
  {
    id: "ALT-003",
    source: "Vectorizer",
    title: "TF-IDF cache refreshed",
    detail: "Vectorizer cache rolled cleanly after the latest deployment cycle.",
    time: "22 min ago",
    severity: "info",
    owner: "Vishal",
    status: "resolved",
  },
  {
    id: "ALT-004",
    source: "Monitoring",
    title: "GPU memory sustained above 96%",
    detail: "The LLM host remained under elevated VRAM pressure for more than 15 minutes.",
    time: "31 min ago",
    severity: "warning",
    owner: "Akash",
    status: "open",
  },
];

const severityStyle: Record<Severity, string> = {
  critical: "border-red-500/20 bg-red-500/8 text-red-300",
  warning: "border-amber-500/20 bg-amber-500/8 text-amber-300",
  info: "border-cyan-500/20 bg-cyan-500/8 text-cyan-300",
};

const severityIcon: Record<Severity, ElementType> = {
  critical: Siren,
  warning: AlertTriangle,
  info: Bell,
};

export default function AlertsTab() {
  const [filter, setFilter] = useState<"all" | Severity>("all");

  const filtered = useMemo(() => {
    if (filter === "all") return ALERTS;
    return ALERTS.filter((item) => item.severity === filter);
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
          <h2 className="text-3xl font-black text-white tracking-widest uppercase">Alerts Center</h2>
          <p className="text-xs text-red-500/50 mt-1 font-mono tracking-widest uppercase">
            Incident routing, anomaly review, and operator attention queue
          </p>
        </div>
        <div className="flex items-center gap-2">
          {(["all", "critical", "warning", "info"] as const).map((value) => (
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
          { label: "Open Alerts", value: "7", sub: "2 critical" },
          { label: "Acknowledged", value: "5", sub: "Owner assigned" },
          { label: "Resolved Today", value: "12", sub: "Mean close 18m" },
          { label: "Escalation SLA", value: "97%", sub: "On target" },
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
            <ShieldAlert className="w-4 h-4 text-red-400" />
            <h3 className="text-xs font-bold text-white/60 tracking-widest uppercase">Live Alert Queue</h3>
          </div>
          <div className="space-y-3">
            {filtered.map((item) => {
              const Icon = severityIcon[item.severity];
              return (
                <div key={item.id} className="border border-white/8 bg-black rounded-xl p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start gap-3">
                      <div className={`mt-0.5 w-10 h-10 rounded-lg border flex items-center justify-center ${severityStyle[item.severity]}`}>
                        <Icon className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-sm font-mono text-white/35">{item.id}</span>
                          <span className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-widest border ${severityStyle[item.severity]}`}>
                            {item.severity}
                          </span>
                          <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-widest border border-white/10 text-white/35">
                            {item.status}
                          </span>
                        </div>
                        <div className="text-base font-semibold text-white mt-2">{item.title}</div>
                        <div className="text-sm text-white/45 mt-1 leading-relaxed">{item.detail}</div>
                        <div className="flex items-center gap-4 mt-3 text-[10px] font-mono text-white/35 uppercase tracking-widest">
                          <span>{item.source}</span>
                          <span>{item.time}</span>
                          <span>Owner: {item.owner}</span>
                        </div>
                      </div>
                    </div>
                    <button className="px-3 py-1.5 rounded-lg border border-white/10 text-[10px] font-mono uppercase tracking-widest text-white/40 hover:text-white hover:bg-white/5">
                      Review
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="col-span-12 xl:col-span-4 flex flex-col gap-6">
          <div className="border border-white/10 bg-[#0a0a0a] rounded-xl p-5">
            <div className="flex items-center gap-2 mb-5">
              <Filter className="w-4 h-4 text-amber-400" />
              <h3 className="text-xs font-bold text-white/60 tracking-widest uppercase">Escalation Policy</h3>
            </div>
            <div className="space-y-3 text-xs font-mono">
              {[
                "Critical -> page owner immediately",
                "Warning -> assign in 10 minutes",
                "Info -> batch into daily digest",
                "LLM outage -> fail over to SVM narrative",
              ].map((line) => (
                <div key={line} className="rounded-lg border border-white/8 bg-black px-3 py-3 text-white/45">
                  {line}
                </div>
              ))}
            </div>
          </div>

          <div className="border border-white/10 bg-[#0a0a0a] rounded-xl p-5">
            <div className="flex items-center gap-2 mb-5">
              <Clock3 className="w-4 h-4 text-cyan-400" />
              <h3 className="text-xs font-bold text-white/60 tracking-widest uppercase">Notification Channels</h3>
            </div>
            <div className="space-y-3">
              {[
                { icon: Mail, label: "Email digest", state: "Enabled" },
                { icon: MessageSquare, label: "Team chat alerts", state: "Enabled" },
                { icon: CheckCircle2, label: "Resolved-event summary", state: "Enabled" },
              ].map((channel) => (
                <div key={channel.label} className="flex items-center justify-between rounded-lg border border-white/8 bg-black px-3 py-3">
                  <div className="flex items-center gap-3">
                    <channel.icon className="w-4 h-4 text-white/35" />
                    <span className="text-sm text-white/55">{channel.label}</span>
                  </div>
                  <span className="text-[10px] font-mono uppercase tracking-widest text-emerald-400">
                    {channel.state}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
