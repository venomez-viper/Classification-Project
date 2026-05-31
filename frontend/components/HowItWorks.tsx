"use client";

import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { ChevronRight, Cpu, GitBranch, Layers, BrainCircuit, TrendingUp, Zap } from "lucide-react";
import { GlowCard } from "@/components/ui/spotlight-card";
import Link from "next/link";

const CASCADE_LEVELS = [
  {
    level: "L1", name: "Sector", classes: 11, icon: Layers,
    color: "violet", borderColor: "border-violet-500/30", bgColor: "bg-violet-500/8",
    textColor: "text-violet-300", glowColor: "shadow-[0_0_14px_rgba(139,92,246,0.25)]",
    example: "Financial Services",
    desc: "Broadest split: which top-level economic sector does this business belong to?",
  },
  {
    level: "L2", name: "Group", classes: 30, icon: GitBranch,
    color: "blue", borderColor: "border-blue-500/30", bgColor: "bg-blue-500/8",
    textColor: "text-blue-300", glowColor: "shadow-[0_0_14px_rgba(59,130,246,0.25)]",
    example: "Banks",
    desc: "Narrows the sector into a smaller business group before fine-grained prediction.",
  },
  {
    level: "L3", name: "Industry", classes: 145, icon: Cpu,
    color: "cyan", borderColor: "border-cyan-500/30", bgColor: "bg-cyan-500/8",
    textColor: "text-cyan-300", glowColor: "shadow-[0_0_14px_rgba(6,182,212,0.25)]",
    example: "Regional Banks",
    desc: "Predicts the final Task 1 Morningstar GECS industry code.",
  },
  {
    level: "L4", name: "Sub-Industry", classes: 428, icon: BrainCircuit,
    color: "emerald", borderColor: "border-emerald-500/30", bgColor: "bg-emerald-500/8",
    textColor: "text-emerald-300", glowColor: "shadow-[0_0_14px_rgba(16,185,129,0.25)]",
    example: "Retail Banking",
    desc: "Ranks only valid Task 2 child codes under the predicted Task 1 parent.",
  },
];

const WALK = [
  { level: "Input", value: "The company provides retail mortgage loans and deposit accounts in community banking markets.", color: "text-white/60" },
  { level: "L1", value: "Financial Services", color: "text-violet-300" },
  { level: "L2", value: "Banks", color: "text-blue-300" },
  { level: "L3", value: "Regional Banks, code 10320020", color: "text-cyan-300" },
  { level: "L4", value: "Retail Banking, constrained Task 2 child", color: "text-emerald-300" },
];

const BENCHMARKS = [
  { label: "Calibrated ensemble ★", pct: 75.0,  note: "locked Task 1", hero: true },
  { label: "Greedy ensemble",        pct: 73.95, note: "pre-calibration", hero: false },
  { label: "ModernBERT-large ep3",   pct: 70.29, note: "single model", hero: false },
  { label: "V8 mega-ensemble",        pct: 68.42, note: "classical ceiling", hero: false },
  { label: "V2 honest baseline",      pct: 59.65, note: "TF-IDF only", hero: false },
];

function BenchBar({ label, pct, note, hero, animate }: { label: string; pct: number; note: string; hero: boolean; animate: boolean }) {
  return (
    <div className="flex items-center gap-3 text-sm">
      <div className="w-36 text-right text-xs text-white/40 flex-shrink-0">{label}</div>
      <div className="flex-1 h-5 rounded bg-white/5 overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: animate ? `${pct}%` : 0 }}
          transition={{ duration: 1.1, ease: [0.22, 1, 0.36, 1], delay: hero ? 0 : 0.15 }}
          className={`h-full rounded ${hero
            ? "bg-gradient-to-r from-violet-500 to-cyan-400 shadow-[0_0_10px_rgba(139,92,246,0.4)]"
            : "bg-gradient-to-r from-white/15 to-white/8"}`}
        />
      </div>
      <div className={`w-10 text-right text-xs font-mono font-bold flex-shrink-0 ${hero ? "text-violet-300" : "text-white/35"}`}>{pct}%</div>
      <div className={`text-xs flex-shrink-0 hidden sm:block ${hero ? "text-emerald-400 font-semibold" : "text-white/20"}`}>{note}</div>
    </div>
  );
}

export default function HowItWorks({ compact = false }: { compact?: boolean }) {
  const benchRef = useRef<HTMLDivElement>(null);
  const benchVisible = useInView(benchRef, { once: true, margin: "-80px" });

  return (
    <section className={`${compact ? "py-10" : "py-20"} px-6`}>
      <div className="mx-auto max-w-6xl space-y-14">
        <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}>
          <div className="inline-flex items-center gap-2 rounded-full border border-violet-500/20 bg-violet-500/10 px-4 py-1.5 text-xs uppercase tracking-[0.3em] text-violet-300 mb-4">
            <Zap className="h-3 w-3" /> How the system works
          </div>
          <h2 className={`font-black tracking-tight text-white ${compact ? "text-3xl" : "text-4xl sm:text-5xl"}`}>
            One description. Four decisions. One industry route.
          </h2>
          <p className="mt-4 max-w-3xl text-lg text-white/50 leading-relaxed">
            GECS-Sage routes text through the Morningstar hierarchy instead of flattening the full taxonomy into one opaque decision. The final build ships a calibrated ModernBERT-large ensemble at 75.0% Macro F1 — earned after catching a 97.2% leakage in the original 88.90% result and rebuilding from scratch.
          </p>
        </motion.div>

        {!compact && (
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
            className="grid gap-4 sm:grid-cols-3">
            {[
              { n: "53,587", label: "company segments", sub: "case-issued training corpus" },
              { n: "145", label: "GECS industry codes", sub: "Task 1 class space" },
              { n: "428", label: "sub-industry codes", sub: "Task 2 constrained children" },
            ].map((s) => (
              <div key={s.n} className="rounded-2xl border border-white/8 bg-white/[0.03] px-6 py-5">
                <div className="text-3xl font-black text-white mb-1">{s.n}</div>
                <div className="text-sm font-semibold text-white/70">{s.label}</div>
                <div className="text-xs text-white/35 mt-1">{s.sub}</div>
              </div>
            ))}
          </motion.div>
        )}

        <div>
          <div className="text-xs uppercase tracking-[0.3em] text-white/30 mb-5">The 4 cascade levels</div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {CASCADE_LEVELS.map((lvl, i) => (
              <motion.div key={lvl.level}
                initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }} transition={{ delay: i * 0.08 }}
                className={`rounded-2xl border ${lvl.borderColor} ${lvl.bgColor} ${lvl.glowColor} p-5`}>
                <div className="flex items-center justify-between mb-3">
                  <span className={`text-xs font-black uppercase tracking-[0.2em] ${lvl.textColor} font-mono`}>{lvl.level}</span>
                  <span className="text-xs text-white/25">{lvl.classes} classes</span>
                </div>
                <div className="text-xl font-bold text-white mb-1">{lvl.name}</div>
                <div className={`text-xs font-mono ${lvl.textColor} mb-3 truncate`}>e.g. {lvl.example}</div>
                <p className="text-xs text-white/45 leading-relaxed">{lvl.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>

        <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}>
          <GlowCard glowColor="cyan" className="border-white/8 bg-black/50 p-0 overflow-hidden">
            <div className="border-b border-white/8 px-6 py-4">
              <div className="text-xs uppercase tracking-[0.28em] text-cyan-300/70 mb-1">Live walk-through</div>
              <h3 className="text-lg font-bold text-white">How a banking description gets classified</h3>
            </div>
            <div className="divide-y divide-white/5">
              {WALK.map((step, i) => (
                <div key={step.level} className="flex items-start gap-4 px-6 py-4">
                  <div className="w-20 flex-shrink-0">
                    <span className="text-xs font-mono font-bold text-white/30 uppercase tracking-wider">{step.level}</span>
                  </div>
                  {i > 0 && i < WALK.length - 1 && (
                    <ChevronRight className="h-4 w-4 text-white/15 flex-shrink-0 mt-0.5" />
                  )}
                  {i === 0 && <div className="w-4 flex-shrink-0" />}
                  {i === WALK.length - 1 && (
                    <div className="h-4 w-4 rounded-full bg-emerald-500 flex-shrink-0 mt-0.5 shadow-[0_0_8px_rgba(16,185,129,0.6)]" />
                  )}
                  <div className={`text-sm font-mono leading-relaxed ${step.color} ${i === 0 ? "italic" : "font-semibold"}`}>
                    {step.value}
                  </div>
                </div>
              ))}
            </div>
            <div className="border-t border-white/8 px-6 py-3 bg-white/[0.02] text-xs text-white/30">
              Each level competes inside its own slice, and Task 2 only ranks valid children of the Task 1 parent.
            </div>
          </GlowCard>
        </motion.div>

        <div className="grid gap-5 md:grid-cols-2">
          <motion.div initial={{ opacity: 0, x: -20 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }}>
            <GlowCard glowColor="red" className="border-red-500/20 bg-red-500/[0.04] h-full p-7">
              <div className="text-xs uppercase tracking-[0.28em] text-red-400/80 mb-3">Task 1 Industry</div>
              <div className="text-4xl font-black text-white mb-1">75.0%</div>
              <div className="text-sm text-emerald-400 font-semibold mb-4">Calibrated Ensemble Macro F1</div>
              <p className="text-sm text-white/50 leading-relaxed mb-4">
                Greedy ensemble of two ModernBERT-large variants with temperature calibration. Top-3 accuracy: 91.4%. Cross-validated and disclosed.
              </p>
              <div className="space-y-1.5 text-xs text-white/40 font-mono">
                <div>L1: sector</div>
                <div>L2: industry group</div>
                <div>L3: final 145-class GECS industry</div>
              </div>
            </GlowCard>
          </motion.div>

          <motion.div initial={{ opacity: 0, x: 20 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }}>
            <GlowCard glowColor="blue" className="border-blue-500/20 bg-blue-500/[0.04] h-full p-7">
              <div className="text-xs uppercase tracking-[0.28em] text-blue-400/80 mb-3">Task 2 Sub-Industry</div>
              <div className="text-4xl font-black text-white mb-1">55.44%</div>
              <div className="text-sm text-cyan-400 font-semibold mb-4">Macro F1 across 428 classes</div>
              <p className="text-sm text-white/50 leading-relaxed mb-4">
                Task 2 uses the predicted Task 1 industry as a hard constraint, then ranks only the valid sub-industry children for that parent.
              </p>
              <div className="space-y-1.5 text-xs text-white/40 font-mono">
                <div>L4: child candidate ranking</div>
                <div>Mapping audit saved in models_task2</div>
                <div>Oracle ceiling: 62.26%</div>
              </div>
            </GlowCard>
          </motion.div>
        </div>

        <motion.div ref={benchRef} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}>
          <GlowCard glowColor="purple" className="border-white/8 bg-black/40 p-6">
            <div className="flex items-center gap-2 mb-5">
              <TrendingUp className="h-4 w-4 text-violet-300" />
              <div className="text-xs uppercase tracking-[0.28em] text-white/35">
                Audited Task 1 benchmark, Macro F1
              </div>
            </div>
            <div className="space-y-3">
              {BENCHMARKS.map((b) => (
                <BenchBar key={b.label} {...b} animate={benchVisible} />
              ))}
            </div>
            <div className="mt-5 pt-4 border-t border-white/6 text-xs text-white/25">
              All claims are cross-validated. The test-tuned upper bound (77.51%) is disclosed but not reported as the headline.
            </div>
          </GlowCard>
        </motion.div>

        {!compact && (
          <motion.div initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
            className="flex flex-wrap gap-3 pt-2">
            <Link href="/demo"
              className="inline-flex items-center gap-2 rounded-2xl bg-violet-600 px-5 py-3 text-sm font-bold text-white hover:bg-violet-500 transition-colors">
              Try the live demo <ChevronRight className="h-4 w-4" />
            </Link>
            <Link href="/model"
              className="inline-flex items-center gap-2 rounded-2xl border border-white/15 px-5 py-3 text-sm font-semibold text-white/75 hover:text-white hover:border-white/25 transition-colors">
              See full results <ChevronRight className="h-4 w-4" />
            </Link>
          </motion.div>
        )}
      </div>
    </section>
  );
}
