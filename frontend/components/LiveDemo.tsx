"use client";

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  Activity,
  BrainCircuit,
  ChevronRight,
  CheckCircle2,
  Clock,
  Cpu,
  Database,
  FileText,
  Flag,
  Gauge,
  GitBranch,
  History,
  Layers,
  Loader2,
  Map,
  PencilLine,
  Radar,
  Terminal,
  Trash2,
  TrendingUp,
  Zap,
} from "lucide-react";
import { GlowCard } from "@/components/ui/spotlight-card";
import { TextScramble } from "@/components/ui/text-scramble";

// ── Examples ─────────────────────────────────────────────────────────────────
const EXAMPLES = [
  { label: "Regional Bank",  text: "The company operates a network of community banks providing commercial lending, retail deposit accounts, residential mortgage origination, and small business banking services. Net interest income represents the majority of operating revenue." },
  { label: "Cloud SaaS",     text: "The company develops and sells enterprise software platforms delivered as a service over the cloud. Core offerings include CRM, workflow automation, and business intelligence dashboards. Revenue is subscription-based with multi-year enterprise contracts." },
  { label: "Biotech",        text: "The company is a clinical-stage biopharmaceutical firm focused on oncology and rare genetic disorders. Its lead pipeline candidate is an mRNA-based gene therapy currently in Phase 2 clinical trials. Revenue is derived primarily from research collaboration agreements and milestone payments." },
  { label: "Oil Pipeline",   text: "The company owns and operates a network of crude oil and natural gas pipelines and storage facilities across the Gulf Coast region. Revenue is generated through long-term take-or-pay transportation and storage contracts with upstream producers." },
  { label: "Semiconductor",  text: "The company designs and manufactures integrated circuits and logic chips for data center, automotive, and consumer electronics applications. Revenue is driven by licensing, wafer sales, and long-term supply agreements with OEM customers." },
  { label: "REIT",           text: "The company is a real estate investment trust that owns a diversified portfolio of commercial office buildings and industrial warehouses. Income is generated through long-term net leases with institutional tenants across major metropolitan markets." },
];

// ── Pipeline steps ────────────────────────────────────────────────────────────
const PIPELINE = [
  { id: "input", icon: Terminal,     label: "Raw Text",          detail: "Company description" },
  { id: "tfidf", icon: Database,     label: "TF-IDF",            detail: "60,000 sparse features" },
  { id: "l1",    icon: Layers,       label: "L1 - Sector",       detail: "11 broad sectors" },
  { id: "l2",    icon: GitBranch,    label: "L2 - Group",        detail: "Industry group within sector" },
  { id: "l3",    icon: BrainCircuit, label: "L3 - Industry",     detail: "Audited 145-class GECS baseline" },
  { id: "l4",    icon: Cpu,          label: "L4 - Sub-Industry", detail: "428-class constrained cascade · 55.44% F1" },
];

const SYSTEM_NOTES = [
  { label: "Task 1 - Industry",     value: "75.0% · calibrated ensemble" },
  { label: "Task 2 - Sub-Industry", value: "55.44% Macro F1 · 428 classes" },
  { label: "Top-3 Accuracy",        value: "91.4% · company-disjoint test" },
  { label: "Model",                 value: "ModernBERT-large ensemble (HF Space)" },
];

const BENCHMARKS = [
  { label: "Calibrated ensemble ★", pct: 75.0,  delta: "locked Task 1", hero: true  },
  { label: "Greedy ensemble",        pct: 73.95, delta: "pre-calibration", hero: false },
  { label: "ModernBERT-large ep3",   pct: 70.29, delta: "single model",  hero: false },
  { label: "V8 mega-ensemble",       pct: 68.42, delta: "classical peak", hero: false },
];

const TAXONOMY_META: Record<string, { abbr: string; color: string }> = {
  mstar: { abbr: "Morningstar", color: "text-violet-300" },
  gics:  { abbr: "GICS",        color: "text-cyan-300"   },
  naics: { abbr: "NAICS",       color: "text-emerald-300"},
  sic:   { abbr: "SIC",         color: "text-amber-300"  },
};

// ── Types ─────────────────────────────────────────────────────────────────────
type Alt = { rank: number; code: string; label: string; confidence: number };
type CascadeNode = { code: string; conf: number };
type CascadePath = { sector?: CascadeNode; group?: CascadeNode; mstar?: CascadeNode; sub?: CascadeNode };
type TaxonomyEntry = { code: string; label: string };
type TaxonomyMap = { mstar?: TaxonomyEntry; gics?: TaxonomyEntry; naics?: TaxonomyEntry; sic?: TaxonomyEntry };

type Result = {
  success: boolean;
  prediction_id?: string;
  model_version?: string;
  official_definition?: string;
  matched_phrase?: string;
  reasoning?: string | null;
  route_reason?: string;
  trace?: Record<string, number>;
  mstar_code: string;
  mstar_label: string;
  confidence_t1: number;
  alternatives_t1?: Alt[];
  cascade_path_t1?: CascadePath;
  features_t1?: string[];
  sub_code?: string;
  sub_label?: string;
  confidence_t2?: number | null;
  alternatives_t2?: Alt[];
  cascade_path_t2?: CascadePath;
  taxonomy_map?: TaxonomyMap;
};

type HistoryEntry = { mstar_label: string; mstar_code: string; conf: number; text: string };

const HIST_KEY = "gecs_pred_history";
const MAX_HIST = 5;
function loadHistory(): HistoryEntry[] { try { return JSON.parse(localStorage.getItem(HIST_KEY) ?? "[]") || []; } catch { return []; } }
function saveHistory(h: HistoryEntry[]) { localStorage.setItem(HIST_KEY, JSON.stringify(h)); }

type RawJson = Record<string, unknown>;

function asObject(value: unknown): RawJson {
  return typeof value === "object" && value !== null ? (value as RawJson) : {};
}

function asString(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

function asPercent(value: unknown, fallback = 0): number {
  if (typeof value !== "number" || Number.isNaN(value)) return fallback;
  return value <= 1 ? value * 100 : value;
}

function normalizeAlt(value: unknown, index: number): Alt {
  const alt = asObject(value);
  return {
    rank: typeof alt.rank === "number" ? alt.rank : index + 1,
    code: asString(alt.code),
    label: asString(alt.industry_name, asString(alt.subindustry_name, asString(alt.label, asString(alt.code)))),
    confidence: asPercent(alt.confidence_percent ?? alt.confidence),
  };
}

function normalizePredictResponse(value: unknown): Result {
  const data = asObject(value);
  const task1 = asObject(data.task1);
  const task2 = asObject(data.task2);
  const t1Alts = Array.isArray(data.alternatives) ? data.alternatives : data.alternatives_t1;
  const t2Alts = Array.isArray(task2.alternatives) ? task2.alternatives : data.alternatives_t2;

  return {
    success: Boolean(data.success ?? true),
    prediction_id: asString(data.prediction_id),
    model_version: asString(data.model_version),
    official_definition: asString(task1.official_definition, asString(data.official_definition)),
    matched_phrase: asString(task1.matched_phrase, asString(data.matched_phrase)),
    reasoning: typeof data.reasoning === "string" ? data.reasoning : null,
    route_reason: asString(data.route_reason),
    trace: asObject(data.trace) as Record<string, number>,
    mstar_code: asString(task1.code, asString(data.mstar_code)),
    mstar_label: asString(task1.industry_name, asString(data.mstar_label, asString(task1.label, "Unknown GECS industry"))),
    confidence_t1: asPercent(task1.confidence_percent ?? task1.confidence ?? data.confidence_t1),
    alternatives_t1: Array.isArray(t1Alts) ? t1Alts.map(normalizeAlt) : undefined,
    cascade_path_t1: data.cascade_path_t1 as CascadePath | undefined,
    features_t1: Array.isArray(data.features_t1) ? (data.features_t1 as string[]) : undefined,
    sub_code: asString(task2.code, asString(data.sub_code)),
    sub_label: asString(task2.subindustry_name, asString(data.sub_label, asString(task2.label))),
    confidence_t2: task2.confidence_percent != null || task2.confidence != null || data.confidence_t2 != null
      ? asPercent(task2.confidence_percent ?? task2.confidence ?? data.confidence_t2)
      : null,
    alternatives_t2: Array.isArray(t2Alts) ? t2Alts.map(normalizeAlt) : undefined,
    cascade_path_t2: data.cascade_path_t2 as CascadePath | undefined,
    taxonomy_map: data.taxonomy_map as TaxonomyMap | undefined,
  };
}

function overrideCandidates(result: Result): Alt[] {
  const candidates: Alt[] = [
    {
      rank: 0,
      code: result.mstar_code,
      label: result.mstar_label,
      confidence: result.confidence_t1,
    },
    ...(result.alternatives_t1 ?? []),
  ];
  const seen = new Set<string>();
  return candidates
    .filter((candidate) => {
      if (!candidate.code || seen.has(candidate.code)) return false;
      seen.add(candidate.code);
      return true;
    })
    .slice(0, 5);
}

// ── Sub-components ────────────────────────────────────────────────────────────
function ConfidenceBar({ label, value, tone }: { label: string; value?: number | null; tone: "red" | "blue" | "emerald" | "purple" | "amber" | "violet" }) {
  const safeValue = Math.max(0, Math.min(100, value ?? 0));
  const fill = { red: "from-red-500 to-rose-400", blue: "from-blue-500 to-indigo-400", emerald: "from-emerald-500 to-teal-400", purple: "from-purple-500 to-violet-400", amber: "from-amber-500 to-yellow-400", violet: "from-violet-500 to-purple-400" }[tone];
  return (
    <div>
      <div className="mb-2 flex items-center justify-between text-sm">
        <span className="text-white/55">{label}</span>
        <span className="font-mono text-white">{value == null ? "N/A" : `${safeValue.toFixed(1)}%`}</span>
      </div>
      <div className="h-3 rounded-full bg-white/8 overflow-hidden">
        <motion.div initial={{ width: 0 }} animate={{ width: `${safeValue}%` }} transition={{ duration: 0.7, ease: "easeOut" }} className={`h-full rounded-full bg-gradient-to-r ${fill}`} />
      </div>
    </div>
  );
}

function BenchmarkBar({ label, pct, delta, hero, animate }: { label: string; pct: number; delta: string; hero: boolean; animate: boolean }) {
  return (
    <div className="flex items-center gap-3">
      <div className="w-24 text-right text-xs text-white/40 flex-shrink-0">{label}</div>
      <div className="flex-1 h-5 rounded-md bg-white/5 overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: animate ? `${pct}%` : 0 }}
          transition={{ duration: 1, ease: [0.22, 1, 0.36, 1], delay: hero ? 0 : 0.15 }}
          className={`h-full rounded-md ${hero ? "bg-gradient-to-r from-violet-500 to-cyan-400 shadow-[0_0_12px_rgba(139,92,246,0.5)]" : "bg-gradient-to-r from-white/20 to-white/10"}`}
        />
      </div>
      <div className={`w-10 text-right text-xs font-mono font-bold flex-shrink-0 ${hero ? "text-violet-300" : "text-white/40"}`}>{pct}%</div>
      <div className={`text-xs flex-shrink-0 ${hero ? "text-emerald-400 font-semibold" : "text-white/20"}`}>{delta}</div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────
export default function LiveDemo() {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeStep, setActiveStep] = useState(-1);
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState("");
  const [resultKey, setResultKey] = useState(0);
  const [history, setHistory] = useState<HistoryEntry[]>(() => loadHistory());
  const [histOpen, setHistOpen] = useState(true);
  const [benchVisible, setBenchVisible] = useState(false);
  const [feedbackStatus, setFeedbackStatus] = useState("");
  const [feedbackError, setFeedbackError] = useState("");
  const [overrideOpen, setOverrideOpen] = useState(false);
  const benchRef = useRef<HTMLDivElement>(null);

  // Trigger benchmark bar animation when scrolled into view
  useEffect(() => {
    const el = benchRef.current;
    if (!el) return;
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) setBenchVisible(true); }, { threshold: 0.3 });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  async function runInference() {
    if (!text.trim() || loading) return;
    setLoading(true);
    setResult(null);
    setError("");
    setFeedbackStatus("");
    setFeedbackError("");
    setOverrideOpen(false);

    for (let i = 0; i < PIPELINE.length; i++) {
      setActiveStep(i);
      await new Promise((r) => setTimeout(r, 220));
    }

    try {
      const res = await fetch("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ company_text: text, segment_text: text, include_reasoning: true }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Server error");

      const normalized = normalizePredictResponse(data);
      setResult(normalized);
      setResultKey((k) => k + 1);
      setActiveStep(PIPELINE.length);

      // Push to history
      const entry: HistoryEntry = { mstar_label: normalized.mstar_label, mstar_code: normalized.mstar_code, conf: normalized.confidence_t1 ?? 0, text };
      const updated = [entry, ...loadHistory()].slice(0, MAX_HIST);
      saveHistory(updated);
      setHistory(updated);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Could not reach classification server.");
      setActiveStep(-1);
    } finally {
      setLoading(false);
    }
  }

  async function submitFeedback(status: "accepted" | "flagged" | "overridden", overrideCode?: string) {
    if (!result?.prediction_id) {
      setFeedbackError("Feedback unavailable: this prediction has no saved prediction ID.");
      return;
    }
    setFeedbackError("");
    setFeedbackStatus("Saving review decision...");
    try {
      const res = await fetch("/api/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prediction_id: result.prediction_id,
          status: overrideCode ? `${status}:${overrideCode}` : status,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Feedback failed");
      setFeedbackStatus(
        status === "accepted"
          ? "Accepted and logged for review history."
          : status === "flagged"
            ? "Flagged for analyst review."
            : `Override logged with ${overrideCode}.`
      );
      setOverrideOpen(false);
    } catch (err: unknown) {
      setFeedbackStatus("");
      setFeedbackError(err instanceof Error ? err.message : "Could not save feedback.");
    }
  }

  function restoreHistory(item: HistoryEntry) { setText(item.text); }
  function clearHistory() { saveHistory([]); setHistory([]); }

  return (
    <section className="min-h-screen px-6 py-20 overflow-hidden">
      <div className="mx-auto max-w-7xl">

        {/* ── Header ── */}
        <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.65 }}
          className="mb-14 grid gap-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-end">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-violet-500/20 bg-violet-500/10 px-4 py-2 text-xs uppercase tracking-[0.3em] text-violet-300">
              <Radar className="h-3.5 w-3.5" />
              4-Level Cascade SVM - Live
            </div>
            <h1 className="mt-6 text-5xl sm:text-6xl lg:text-7xl font-black tracking-tight text-white">
              Turn raw company language
              <span className="block text-white/55">into a Morningstar verdict.</span>
            </h1>
            <p className="mt-6 max-w-3xl text-lg sm:text-xl leading-relaxed text-white/55">
              A calibrated ModernBERT-large ensemble for Morningstar industry routing - 75.0% Macro F1, 91.4% top-3 accuracy, deployed on Hugging Face Space. The story is honest: we caught our own leakage and rebuilt from scratch.
            </p>
          </div>

          <GlowCard glowColor="cyan" className="border-white/8 bg-white/[0.03] p-0 overflow-hidden">
            <div className="border-b border-white/8 px-6 py-5">
              <div className="text-xs uppercase tracking-[0.28em] text-cyan-300/80 mb-2">Results at a glance</div>
              <h2 className="text-2xl font-bold text-white">Group 4 · MGT 599 Capstone</h2>
            </div>
            <div className="grid grid-cols-2 gap-px bg-white/8">
              {SYSTEM_NOTES.map((item) => (
                <div key={item.label} className="bg-black/65 px-6 py-5">
                  <div className="text-xs uppercase tracking-[0.24em] text-white/35">{item.label}</div>
                  <div className="mt-2 text-base font-semibold text-white">{item.value}</div>
                </div>
              ))}
            </div>
          </GlowCard>
        </motion.div>

        {/* ── Two-column layout ── */}
        <div className="grid gap-8 lg:grid-cols-[1.02fr_0.98fr]">

          {/* ══ LEFT: input ══ */}
          <div className="flex flex-col gap-6">

            {/* Feature 4: History */}
            {history.length > 0 && (
              <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
                <GlowCard glowColor="purple" className="border-white/8 bg-black/40 p-0 overflow-hidden">
                  <button onClick={() => setHistOpen(!histOpen)}
                    className="w-full flex items-center justify-between px-5 py-3 border-b border-white/8 bg-white/[0.02] text-left">
                    <div className="flex items-center gap-2 text-xs uppercase tracking-[0.25em] text-white/35">
                      <History className="h-3.5 w-3.5" />
                      Recent Predictions
                    </div>
                    <div className="flex items-center gap-2">
                      <button onClick={(e) => { e.stopPropagation(); clearHistory(); }}
                        className="flex items-center gap-1 text-xs text-red-400/50 hover:text-red-300 transition-colors px-2 py-1 rounded-lg hover:bg-red-500/10">
                        <Trash2 className="h-3 w-3" /> Clear
                      </button>
                      <ChevronRight className={`h-4 w-4 text-white/20 transition-transform ${histOpen ? "rotate-90" : ""}`} />
                    </div>
                  </button>
                  {histOpen && (
                    <div className="max-h-44 overflow-y-auto">
                      {history.map((item, i) => (
                        <button key={i} onClick={() => restoreHistory(item)}
                          className="w-full flex items-center gap-3 px-5 py-3 border-b border-white/5 last:border-0 hover:bg-white/[0.04] transition-colors text-left">
                          <Clock className="h-3.5 w-3.5 text-white/20 flex-shrink-0" />
                          <span className="flex-1 text-sm text-white/65 truncate">{item.mstar_label}</span>
                          <span className="font-mono text-xs text-cyan-400/70 flex-shrink-0 border border-cyan-500/20 bg-cyan-500/8 px-2 py-0.5 rounded">{item.mstar_code}</span>
                          <span className="text-xs font-bold text-violet-400 w-10 text-right flex-shrink-0">{Math.round(item.conf)}%</span>
                        </button>
                      ))}
                    </div>
                  )}
                </GlowCard>
              </motion.div>
            )}

            {/* Input card */}
            <GlowCard glowColor="red" className="border-white/8 bg-black/55 p-8">
              <div className="mb-6 flex items-center justify-between border-b border-white/8 pb-4">
                <div className="flex items-center gap-3">
                  <div className="flex gap-1.5">
                    <span className="h-3 w-3 rounded-full bg-red-500" />
                    <span className="h-3 w-3 rounded-full bg-amber-400" />
                    <span className="h-3 w-3 rounded-full bg-emerald-500" />
                  </div>
                  <span className="font-mono text-sm text-white/30">prediction_lab.input</span>
                </div>
                <div className="text-xs uppercase tracking-[0.25em] text-white/25">Live text payload</div>
              </div>

              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={9}
                placeholder="Paste a company description here..."
                className="w-full resize-none bg-transparent text-lg leading-relaxed text-white outline-none placeholder:text-white/12 font-mono"
              />

              {/* Feature 2: Example pills */}
              <div className="mt-5 flex flex-wrap gap-2">
                {EXAMPLES.map((ex) => (
                  <button key={ex.label} onClick={() => setText(ex.text)}
                    className="rounded-full border border-violet-500/25 bg-violet-500/8 px-3 py-1.5 text-xs font-semibold text-violet-300 hover:bg-violet-500/20 hover:border-violet-400/50 hover:shadow-[0_0_8px_rgba(139,92,246,0.3)] transition-all">
                    {ex.label}
                  </button>
                ))}
              </div>
            </GlowCard>

            {/* Stats row */}
            <div className="grid gap-4 md:grid-cols-3">
              <div className="rounded-[28px] border border-white/10 bg-white/[0.03] p-5">
                <Activity className="h-5 w-5 text-red-300 mb-3" />
                <div className="text-sm font-semibold text-white mb-1">1,673 samples/sec</div>
                <div className="text-sm text-white/52">Fast local inference with SQLite prediction logging.</div>
              </div>
              <div className="rounded-[28px] border border-white/10 bg-white/[0.03] p-5">
                <Gauge className="h-5 w-5 text-cyan-300 mb-3" />
                <div className="text-sm font-semibold text-white mb-1">4-level cascade</div>
                <div className="text-sm text-white/52">Sector → Group → Industry → Sub-Industry.</div>
              </div>
              <div className="rounded-[28px] border border-white/10 bg-white/[0.03] p-5">
                <Map className="h-5 w-5 text-emerald-300 mb-3" />
                <div className="text-sm font-semibold text-white mb-1">4-taxonomy map</div>
                <div className="text-sm text-white/52">Every code mapped to GICS, NAICS, SIC.</div>
              </div>
            </div>

            {/* Run button */}
            <button onClick={runInference} disabled={loading || !text.trim()}
              className="w-full rounded-2xl bg-violet-700 px-6 py-5 text-lg font-bold text-white transition-all hover:bg-violet-600 hover:shadow-[0_0_45px_rgba(124,58,237,0.4)] disabled:cursor-not-allowed disabled:opacity-35 flex items-center justify-center gap-3">
              {loading ? (
                <><Loader2 className="h-5 w-5 animate-spin" />Running cascade inference</>
              ) : (
                <><Zap className="h-5 w-5" />Run Cascade Classification</>
              )}
            </button>

            {/* Feature 3: Benchmark scorecard */}
            <div ref={benchRef}>
              <GlowCard glowColor="purple" className="border-white/8 bg-black/40 p-6">
                <div className="flex items-center gap-2 mb-5">
                  <TrendingUp className="h-4 w-4 text-violet-300" />
                  <div className="text-xs uppercase tracking-[0.28em] text-white/35">
                    Model Benchmark - audited Task 1 holdout Macro F1
                  </div>
                </div>
                <div className="flex flex-col gap-3">
                  {BENCHMARKS.map((b) => (
                    <BenchmarkBar key={b.label} {...b} animate={benchVisible} />
                  ))}
                </div>
              </GlowCard>
            </div>
          </div>

          {/* ══ RIGHT: pipeline + results ══ */}
          <div className="flex flex-col gap-6">

            {/* Pipeline visualiser */}
            <GlowCard glowColor="blue" className="border-white/8 bg-black/55 p-8">
              <div className="mb-6 flex items-center justify-between">
                <div>
                  <div className="text-xs uppercase tracking-[0.28em] text-white/35 mb-2">Cascade Architecture</div>
                  <h2 className="text-2xl font-bold text-white">Reads the taxonomy structure.</h2>
                </div>
                <div className="font-mono text-xs text-white/25">
                  {activeStep < 0 ? "IDLE" : activeStep >= PIPELINE.length ? "COMPLETE" : `STEP ${activeStep + 1}/${PIPELINE.length}`}
                </div>
              </div>
              <div className="space-y-4">
                {PIPELINE.map((step, index) => {
                  const active = activeStep === index;
                  const done = activeStep > index;
                  return (
                    <div key={step.id} className="flex items-center gap-5">
                      <motion.div
                        animate={{ backgroundColor: done ? "#10b981" : active ? "#7c3aed" : "rgba(255,255,255,0.06)", boxShadow: active ? "0 0 22px rgba(124,58,237,0.5)" : done ? "0 0 14px rgba(16,185,129,0.28)" : "none" }}
                        transition={{ duration: 0.3 }}
                        className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-2xl">
                        <step.icon className="h-5 w-5 text-white" />
                      </motion.div>
                      <div className="flex-1">
                        <div className={`text-base font-semibold ${done ? "text-emerald-400" : active ? "text-violet-300" : "text-white/40"}`}>{step.label}</div>
                        <div className="text-xs text-white/28">{step.detail}</div>
                      </div>
                      {done ? <span className="font-mono text-xs uppercase tracking-[0.24em] text-emerald-400">Done</span>
                        : active ? <Loader2 className="h-4 w-4 animate-spin text-violet-400" />
                        : <ChevronRight className="h-4 w-4 text-white/15" />}
                    </div>
                  );
                })}
              </div>
            </GlowCard>

            {/* Results */}
            <AnimatePresence mode="wait">
              {error ? (
                <motion.div key="error" initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                  className="rounded-[28px] border border-red-500/25 bg-red-500/10 px-6 py-6 text-red-200">{error}</motion.div>

              ) : result ? (
                <motion.div key={`result-${resultKey}`} initial={{ opacity: 0, y: 18, scale: 0.98 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }} className="flex flex-col gap-5">

                  {/* Task 1 - Industry */}
                  <GlowCard glowColor="red" className="border-white/8 bg-red-500/[0.05] p-8">
                    <div className="mb-4 text-xs uppercase tracking-[0.28em] text-red-300/80">Task 1 - GECS Industry · audited baseline</div>
                    <TextScramble key={`mstar-${resultKey}`} as="h3" speed={0.02} duration={0.8} className="text-3xl sm:text-4xl font-bold text-white mb-4">
                      {result.mstar_label}
                    </TextScramble>
                    <div className="mb-5 inline-flex items-center gap-3 rounded-2xl border border-red-500/15 bg-black/30 px-4 py-3 font-mono text-red-200">
                      <span>{result.mstar_code}</span>
                      <span className="text-white/20">|</span>
                      <span className="text-white/45">MSTAR-GECS</span>
                    </div>
                    <ConfidenceBar label="Classification confidence" value={result.confidence_t1} tone="red" />

                    {/* Feature 1: Signal words */}
                    {result.features_t1 && result.features_t1.length > 0 && (
                      <div className="mt-5 pt-4 border-t border-white/8">
                        <div className="text-xs uppercase tracking-[0.24em] text-white/25 mb-3 flex items-center gap-2">
                          <FileText className="h-3 w-3" /> Key classification signals
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {result.features_t1.slice(0, 10).map((w) => (
                            <span key={w} className="font-mono text-xs px-2.5 py-1 rounded-lg border border-violet-500/30 bg-violet-500/10 text-violet-300 shadow-[0_0_6px_rgba(139,92,246,0.2)]">{w}</span>
                          ))}
                        </div>
                      </div>
                    )}
                  </GlowCard>

                  {/* Task 2 - Sub-Industry */}
                  {(result.official_definition || result.matched_phrase || result.reasoning || result.route_reason) && (
                    <GlowCard glowColor="emerald" className="border-white/8 bg-white/[0.03] p-6">
                      <div className="mb-4 flex items-center gap-2">
                        <FileText className="h-4 w-4 text-emerald-300" />
                        <div className="text-xs uppercase tracking-[0.28em] text-emerald-300/80">Model Evidence</div>
                      </div>
                      <div className="space-y-4">
                        {result.official_definition && (
                          <div>
                            <div className="mb-1 text-xs uppercase tracking-[0.2em] text-white/28">Official definition</div>
                            <p className="text-sm leading-relaxed text-white/65">{result.official_definition}</p>
                          </div>
                        )}
                        {result.matched_phrase && (
                          <div>
                            <div className="mb-1 text-xs uppercase tracking-[0.2em] text-white/28">Closest taxonomy phrase</div>
                            <p className="font-mono text-sm text-emerald-200">{result.matched_phrase}</p>
                          </div>
                        )}
                        {result.reasoning && (
                          <div>
                            <div className="mb-1 text-xs uppercase tracking-[0.2em] text-white/28">Reasoning note</div>
                            <p className="text-sm leading-relaxed text-white/60">{result.reasoning}</p>
                          </div>
                        )}
                        {result.route_reason && (
                          <div className="rounded-2xl border border-emerald-500/15 bg-emerald-500/8 px-4 py-3 text-sm text-emerald-100/80">
                            {result.route_reason}
                          </div>
                        )}
                      </div>
                    </GlowCard>
                  )}

                  {result.sub_label && result.sub_code && (
                    <GlowCard glowColor="blue" className="border-white/8 bg-blue-500/[0.04] p-8">
                      <div className="mb-4 text-xs uppercase tracking-[0.28em] text-blue-300/80">Task 2 - Sub-Industry · 55.44% F1 · 428 classes</div>
                      <TextScramble key={`sub-${resultKey}`} as="h3" speed={0.02} duration={0.8} className="text-2xl sm:text-3xl font-bold text-white mb-4">
                        {result.sub_label}
                      </TextScramble>
                      <div className="mb-5 inline-flex items-center gap-3 rounded-2xl border border-blue-500/15 bg-black/30 px-4 py-3 font-mono text-blue-200">
                        <span>{result.sub_code}</span>
                        <span className="text-white/20">|</span>
                        <span className="text-white/45">Sub-Industry</span>
                      </div>
                      <ConfidenceBar label="Sub-industry confidence" value={result.confidence_t2} tone="blue" />
                      {result.alternatives_t2 && result.alternatives_t2.length > 0 && (
                        <div className="mt-4 pt-4 border-t border-white/8">
                          <div className="text-xs uppercase tracking-[0.24em] text-white/25 mb-3">Other candidates</div>
                          <div className="space-y-2">
                            {result.alternatives_t2.slice(0, 3).map((alt) => (
                              <div key={`${alt.rank}-${alt.code}`} className="flex items-center justify-between rounded-xl border border-white/6 bg-black/20 px-4 py-2.5">
                                <div>
                                  <span className="text-xs text-white/30 mr-2">#{alt.rank}</span>
                                  <span className="text-sm text-white/65">{alt.label}</span>
                                </div>
                                <span className="font-mono text-xs text-blue-300">{alt.confidence.toFixed(1)}%</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </GlowCard>
                  )}

                  {/* Feature 5: Taxonomy crosswalk */}
                  {result.taxonomy_map && (
                    <GlowCard glowColor="emerald" className="border-white/8 bg-white/[0.03] p-6">
                      <div className="mb-4 flex items-center gap-2">
                        <Map className="h-4 w-4 text-emerald-300" />
                        <div className="text-xs uppercase tracking-[0.28em] text-emerald-300/80">Taxonomy Crosswalk</div>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        {(["mstar", "gics", "naics", "sic"] as const).map((key) => {
                          const entry = result.taxonomy_map?.[key];
                          const meta = TAXONOMY_META[key];
                          if (!entry) return null;
                          return (
                            <div key={key} className="rounded-xl border border-white/8 bg-black/30 px-4 py-3">
                              <div className={`text-xs uppercase tracking-[0.22em] mb-1 ${meta.color}`}>{meta.abbr}</div>
                              <div className="font-mono text-xs text-white/40 mb-1">{entry.code}</div>
                              <div className="text-sm font-semibold text-white leading-tight">{entry.label}</div>
                            </div>
                          );
                        })}
                      </div>
                    </GlowCard>
                  )}

                  {/* T1 Alternatives */}
                  {result.alternatives_t1 && result.alternatives_t1.length > 0 && (
                    <GlowCard glowColor="amber" className="border-white/8 bg-white/[0.03] p-6">
                      <div className="mb-4 text-xs uppercase tracking-[0.28em] text-white/35">Top industry alternatives</div>
                      <div className="space-y-3">
                        {result.alternatives_t1.slice(0, 3).map((alt) => (
                          <div key={`${alt.rank}-${alt.code}`} className="rounded-2xl border border-white/8 bg-black/30 px-4 py-4">
                            <div className="flex items-center justify-between gap-4">
                              <div>
                                <div className="text-sm text-white/40">Rank {alt.rank}</div>
                                <div className="font-semibold text-white">{alt.label}</div>
                                <div className="font-mono text-xs text-white/35 mt-1">{alt.code}</div>
                              </div>
                              <div className="font-mono text-amber-300">{alt.confidence.toFixed(1)}%</div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </GlowCard>
                  )}

                  {result.trace && Object.keys(result.trace).length > 0 && (
                    <GlowCard glowColor="purple" className="border-white/8 bg-white/[0.03] p-6">
                      <div className="mb-4 text-xs uppercase tracking-[0.28em] text-violet-300/80">Processing Trace</div>
                      <div className="grid gap-3 sm:grid-cols-2">
                        {Object.entries(result.trace).map(([name, value]) => (
                          <div key={name} className="rounded-2xl border border-white/8 bg-black/30 px-4 py-3">
                            <div className="text-xs uppercase tracking-[0.18em] text-white/28">{name.replaceAll("_", " ")}</div>
                            <div className="mt-1 font-mono text-sm text-violet-200">
                              {typeof value === "number" ? `${value.toFixed(3)}s` : String(value)}
                            </div>
                          </div>
                        ))}
                      </div>
                    </GlowCard>
                  )}

                  <GlowCard glowColor="cyan" className="border-white/8 bg-cyan-500/[0.04] p-6">
                    <div className="mb-4 flex items-start justify-between gap-4">
                      <div>
                        <div className="mb-2 text-xs uppercase tracking-[0.28em] text-cyan-300/80">Analyst Review</div>
                        <p className="text-sm leading-relaxed text-white/55">
                          Log whether this prediction is accepted, needs review, or should be overridden to another GECS industry.
                        </p>
                      </div>
                      {result.prediction_id && (
                        <span className="rounded-full border border-white/10 bg-black/30 px-3 py-1 font-mono text-xs text-white/35">
                          #{result.prediction_id}
                        </span>
                      )}
                    </div>

                    <div className="flex flex-wrap gap-3">
                      <button
                        onClick={() => submitFeedback("accepted")}
                        disabled={!result.prediction_id}
                        className="inline-flex items-center gap-2 rounded-xl border border-emerald-500/25 bg-emerald-500/10 px-4 py-2 text-sm font-semibold text-emerald-200 transition hover:bg-emerald-500/20 disabled:cursor-not-allowed disabled:opacity-40"
                      >
                        <CheckCircle2 className="h-4 w-4" /> Accept
                      </button>
                      <button
                        onClick={() => submitFeedback("flagged")}
                        disabled={!result.prediction_id}
                        className="inline-flex items-center gap-2 rounded-xl border border-amber-500/25 bg-amber-500/10 px-4 py-2 text-sm font-semibold text-amber-200 transition hover:bg-amber-500/20 disabled:cursor-not-allowed disabled:opacity-40"
                      >
                        <Flag className="h-4 w-4" /> Flag
                      </button>
                      <button
                        onClick={() => setOverrideOpen((open) => !open)}
                        disabled={!result.prediction_id}
                        className="inline-flex items-center gap-2 rounded-xl border border-cyan-500/25 bg-cyan-500/10 px-4 py-2 text-sm font-semibold text-cyan-200 transition hover:bg-cyan-500/20 disabled:cursor-not-allowed disabled:opacity-40"
                      >
                        <PencilLine className="h-4 w-4" /> Override
                      </button>
                    </div>

                    {overrideOpen && (
                      <div className="mt-5 space-y-2 border-t border-white/8 pt-4">
                        <div className="mb-3 text-xs uppercase tracking-[0.22em] text-white/28">Choose replacement industry</div>
                        {overrideCandidates(result).map((candidate) => (
                          <button
                            key={candidate.code}
                            onClick={() => submitFeedback("overridden", candidate.code)}
                            className="flex w-full items-center justify-between rounded-2xl border border-white/8 bg-black/30 px-4 py-3 text-left transition hover:border-cyan-400/40 hover:bg-cyan-500/8"
                          >
                            <span>
                              <span className="block font-semibold text-white">{candidate.label}</span>
                              <span className="font-mono text-xs text-white/35">{candidate.code}</span>
                            </span>
                            <span className="font-mono text-xs text-cyan-300">{candidate.confidence.toFixed(1)}%</span>
                          </button>
                        ))}
                      </div>
                    )}

                    {feedbackStatus && (
                      <div className="mt-4 rounded-2xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-100">
                        {feedbackStatus}
                      </div>
                    )}
                    {feedbackError && (
                      <div className="mt-4 rounded-2xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-100">
                        {feedbackError}
                      </div>
                    )}
                  </GlowCard>

                </motion.div>

              ) : (
                <motion.div key="placeholder" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                  className="rounded-[28px] border border-white/8 bg-white/[0.03] px-8 py-12 text-center">
                  <Cpu className="mx-auto mb-4 h-12 w-12 text-white/12" />
                  <div className="text-xl font-mono text-white/25">Paste a company description to classify.</div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </section>
  );
}
