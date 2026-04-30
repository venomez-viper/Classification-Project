"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  BellRing,
  KeyRound,
  Lock,
  Settings2,
  Shield,
  SlidersHorizontal,
  UserCog,
  Workflow,
} from "lucide-react";

type ToggleProps = {
  label: string;
  detail: string;
  defaultOn?: boolean;
};

function ToggleRow({ label, detail, defaultOn = false }: ToggleProps) {
  const [on, setOn] = useState(defaultOn);

  return (
    <div className="flex items-center justify-between rounded-xl border border-white/8 bg-black px-4 py-4">
      <div>
        <div className="text-sm font-semibold text-white">{label}</div>
        <div className="text-xs text-white/35 mt-1">{detail}</div>
      </div>
      <button
        type="button"
        onClick={() => setOn((v) => !v)}
        className={`relative w-12 h-7 rounded-full transition-colors ${on ? "bg-red-600" : "bg-white/10"}`}
        aria-pressed={on}
      >
        <span
          className={`absolute top-1 w-5 h-5 rounded-full bg-white transition-all ${on ? "left-6" : "left-1"}`}
        />
      </button>
    </div>
  );
}

export default function SettingsTab() {
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
          <h2 className="text-3xl font-black text-white tracking-widest uppercase">Settings Console</h2>
          <p className="text-xs text-red-500/50 mt-1 font-mono tracking-widest uppercase">
            Operator preferences, security posture, and workflow defaults
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        {[
          { label: "Workspace Mode", value: "Operator" },
          { label: "Alert Sensitivity", value: "Balanced" },
          { label: "Security Tier", value: "Protected" },
          { label: "Runbook Profile", value: "Default" },
        ].map((item) => (
          <div key={item.label} className="rounded-xl border border-white/10 bg-black/50 p-4">
            <div className="text-[10px] font-mono text-white/30 uppercase tracking-widest">{item.label}</div>
            <div className="mt-2 text-xl font-black font-mono text-white">{item.value}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-12 xl:col-span-4 border border-white/10 bg-[#0a0a0a] rounded-xl p-5">
          <div className="flex items-center gap-2 mb-5">
            <UserCog className="w-4 h-4 text-red-400" />
            <h3 className="text-xs font-bold text-white/60 tracking-widest uppercase">Operator Profile</h3>
          </div>
          <div className="space-y-4">
            {[
              { label: "Active user", value: "admin" },
              { label: "Role", value: "ML Ops Controller" },
              { label: "Default landing tab", value: "Overview" },
              { label: "Timezone", value: "America/Chicago" },
            ].map((item) => (
              <div key={item.label} className="rounded-lg border border-white/8 bg-black px-4 py-3">
                <div className="text-[10px] font-mono uppercase tracking-widest text-white/30">{item.label}</div>
                <div className="text-sm text-white mt-1">{item.value}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="col-span-12 xl:col-span-8 grid grid-cols-1 2xl:grid-cols-2 gap-6">
          <div className="border border-white/10 bg-[#0a0a0a] rounded-xl p-5">
            <div className="flex items-center gap-2 mb-5">
              <BellRing className="w-4 h-4 text-amber-400" />
              <h3 className="text-xs font-bold text-white/60 tracking-widest uppercase">Notification Preferences</h3>
            </div>
            <div className="space-y-3">
              <ToggleRow label="Desktop alert banners" detail="Show immediate operator banners for high-priority events." defaultOn />
              <ToggleRow label="Critical-only mode" detail="Suppress low-priority messages during investigation windows." />
              <ToggleRow label="Daily status digest" detail="Send a roll-up summary of system health and model performance." defaultOn />
            </div>
          </div>

          <div className="border border-white/10 bg-[#0a0a0a] rounded-xl p-5">
            <div className="flex items-center gap-2 mb-5">
              <Shield className="w-4 h-4 text-cyan-400" />
              <h3 className="text-xs font-bold text-white/60 tracking-widest uppercase">Security Controls</h3>
            </div>
            <div className="space-y-3">
              <ToggleRow label="Session lock reminders" detail="Prompt for re-authentication after extended idle periods." defaultOn />
              <ToggleRow label="Audit trail annotations" detail="Log settings changes and alert acknowledgements." defaultOn />
              <ToggleRow label="Strict action confirmations" detail="Require confirmation before changing deployment-sensitive options." />
            </div>
          </div>

          <div className="border border-white/10 bg-[#0a0a0a] rounded-xl p-5">
            <div className="flex items-center gap-2 mb-5">
              <Workflow className="w-4 h-4 text-emerald-400" />
              <h3 className="text-xs font-bold text-white/60 tracking-widest uppercase">Workflow Defaults</h3>
            </div>
            <div className="space-y-3">
              <ToggleRow label="Auto-open monitoring" detail="Jump to monitoring after a critical alert is raised." defaultOn />
              <ToggleRow label="Pin prediction diagnostics" detail="Keep recent model explanation cards visible across app sessions." />
              <ToggleRow label="Prefer SVM fallback narrative" detail="Show SVM continuity messaging when the LLM service is degraded." defaultOn />
            </div>
          </div>

          <div className="border border-white/10 bg-[#0a0a0a] rounded-xl p-5">
            <div className="flex items-center gap-2 mb-5">
              <Settings2 className="w-4 h-4 text-red-300" />
              <h3 className="text-xs font-bold text-white/60 tracking-widest uppercase">Configuration Summary</h3>
            </div>
            <div className="space-y-3 text-xs font-mono">
              {[
                "Alert threshold profile: balanced",
                "Prediction explainability cards: enabled",
                "Monitoring auto-refresh: 30s",
                "UI layout mode: command center",
                "Access controls: standard protected",
              ].map((line) => (
                <div key={line} className="rounded-lg border border-white/8 bg-black px-4 py-3 text-white/45">
                  {line}
                </div>
              ))}
            </div>
            <div className="mt-5 flex gap-3">
              <button className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-white text-xs font-mono uppercase tracking-widest">
                Save profile
              </button>
              <button className="px-4 py-2 rounded-lg border border-white/10 text-white/45 hover:text-white hover:bg-white/5 text-xs font-mono uppercase tracking-widest">
                Reset
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { icon: SlidersHorizontal, label: "Preference layers", value: "12 active rules" },
          { icon: Lock, label: "Protected actions", value: "6 confirmation gates" },
          { icon: KeyRound, label: "Session state", value: "Authenticated" },
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
    </motion.div>
  );
}
