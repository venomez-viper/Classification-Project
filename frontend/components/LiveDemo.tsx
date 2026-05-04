"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  Activity,
  BrainCircuit,
  ChevronRight,
  Cpu,
  Database,
  FileText,
  Gauge,
  GitBranch,
  Layers,
  Loader2,
  Map,
  Radar,
  Terminal,
  Zap,
} from "lucide-react";
import { GlowCard } from "@/components/ui/spotlight-card";
import { TextScramble } from "@/components/ui/text-scramble";

const EXAMPLES = [
  {
    label: "Retail Banking",
    text: "The company provides retail banking, mortgage lending, treasury products, and investment portfolio management for individual and corporate clients across the United States.",
  },
  {
    label: "Cloud Software",
    text: "The company develops enterprise software, cloud infrastructure tools, analytics platforms, and database services for large businesses and public sector customers.",
  },
  {
    label: "Medical Devices",
    text: "The company manufactures surgical devices, patient monitoring systems, and diagnostic equipment used by hospitals and clinical settings worldwide.",
  },
  {
    label: "Energy Production",
    text: "The company explores, develops, and produces oil and natural gas from offshore and onshore assets in North America and international basins.",
  },
];

const PIPELINE = [
  { id: "input", icon: Terminal,    label: "Raw Text",    detail: "Company description" },
  { id: "tfidf", icon: Database,    label: "TF-IDF",      detail: "50,000 sparse features" },
  { id: "l1",    icon: Layers,      label: "L1 — Sector", detail: "11 broad sectors" },
  { id: "l2",    icon: GitBranch,   label: "L2 — Group",  detail: "Industry group within sector" },
  { id: "l3",    icon: BrainCircuit,label: "L3 — Code",   detail: "Final Morningstar GECS code" },
];

const SYSTEM_NOTES = [
  { label: "Architecture",      value: "BreezeML Level 2" },
  { label: "Vector space",      value: "50K TF-IDF" },
  { label: "Best metric",       value: "88.90% Macro F1" },
  { label: "Deployment stance", value: "CPU · No cloud · No GPU" },
];

const ENGINE_STYLES: Record<string, { badge: string; glow: "red" | "blue" | "cyan" | "amber" | "emerald" | "purple"; dot: string }> = {
  "SVM Cascade":    { badge: "border-emerald-500/30 bg-emerald-500/10 text-emerald-300", glow: "emerald", dot: "bg-emerald-400" },
  "DeBERTa":        { badge: "border-cyan-500/30 bg-cyan-500/10 text-cyan-300",          glow: "cyan",    dot: "bg-cyan-400" },
  "Consensus":      { badge: "border-purple-500/30 bg-purple-500/10 text-purple-300",    glow: "purple",  dot: "bg-purple-400" },
  "Low Confidence": { badge: "border-amber-500/30 bg-amber-500/10 text-amber-300",       glow: "amber",   dot: "bg-amber-400" },
};

const TAXONOMY_META: Record<string, { abbr: string; color: string }> = {
  mstar: { abbr: "MSTAR", color: "text-red-300"     },
  gics:  { abbr: "GICS",  color: "text-cyan-300"    },
  naics: { abbr: "NAICS", color: "text-emerald-300" },
  sic:   { abbr: "SIC",   color: "text-amber-300"   },
};

type TaxonomyEntry = { code: string; label: string };

type Result = {
  success: boolean;
  engine: string;
  route_reason: string;
  mstar_code: string;
  mstar_label: string;
  confidence: number;
  alternatives?: { rank: number; code: string; label: string; confidence: number }[];
  explanation?: string;
  explanation_engine?: string;
  taxonomy_map?: {
    mstar?: TaxonomyEntry;
    gics?: TaxonomyEntry;
    naics?: TaxonomyEntry;
    sic?: TaxonomyEntry;
    status?: string;
  };
};

function ConfidenceBar({
  label,
  value,
  tone,
}: {
  label: string;
  value?: number | null;
  tone: "red" | "blue" | "emerald" | "purple" | "amber";
}) {
  const safeValue = Math.max(0, Math.min(100, value ?? 0));
  const fill = {
    red:    "from-red-500 to-rose-400",
    blue:   "from-blue-500 to-indigo-400",
    emerald:"from-emerald-500 to-teal-400",
    purple: "from-purple-500 to-violet-400",
    amber:  "from-amber-500 to-yellow-400",
  }[tone];

  return (
    <div>
      <div className="mb-2 flex items-center justify-between text-sm">
        <span className="text-white/55">{label}</span>
        <span className="font-mono text-white">
          {value == null ? "N/A" : `${safeValue.toFixed(1)}%`}
        </span>
      </div>
      <div className="h-3 rounded-full bg-white/8 overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${safeValue}%` }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className={`h-full rounded-full bg-gradient-to-r ${fill}`}
        />
      </div>
    </div>
  );
}

export default function LiveDemo() {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeStep, setActiveStep] = useState(-1);
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState("");
  const [resultKey, setResultKey] = useState(0);

  async function runInference() {
    if (!text.trim() || loading) return;

    setLoading(true);
    setResult(null);
    setError("");

    for (let i = 0; i < PIPELINE.length; i++) {
      setActiveStep(i);
      await new Promise((resolve) => setTimeout(resolve, 280));
    }

    try {
      const res = await fetch("/api/predict_legendary", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || "Server error");
      }

      setResult(data);
      setResultKey((k) => k + 1);
      setActiveStep(PIPELINE.length);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Could not reach the BreezeML Level 2 server (port 5003).";
      setError(message);
      setActiveStep(-1);
    } finally {
      setLoading(false);
    }
  }

  const engineStyle = result
    ? (ENGINE_STYLES[result.engine] ?? ENGINE_STYLES["Low Confidence"])
    : null;

  return (
    <section className="min-h-screen px-6 py-20 overflow-hidden">
      <div className="mx-auto max-w-7xl">

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.65 }}
          className="mb-14 grid gap-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-end"
        >
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-red-500/20 bg-red-500/10 px-4 py-2 text-xs uppercase tracking-[0.3em] text-red-300">
              <Radar className="h-3.5 w-3.5" />
              BreezeML Level 2 — Live
            </div>
            <h1 className="mt-6 text-5xl sm:text-6xl lg:text-7xl font-black tracking-tight text-white">
              Turn raw company language
              <span className="block text-white/55">into a Morningstar verdict.</span>
            </h1>
            <p className="mt-6 max-w-3xl text-lg sm:text-xl leading-relaxed text-white/55">
              88.90% Macro F1. 145 classes. 10,717 holdout samples. No GPU. No cloud. BreezeML Level 2 reads the Morningstar taxonomy hierarchy instead of flattening it — and outperforms a
              fine-tuned DeBERTa neural network by{" "}
              <span className="font-semibold text-white">+24.90 percentage points</span>.
            </p>
          </div>

          <GlowCard glowColor="cyan" className="border-white/8 bg-white/[0.03] p-0 overflow-hidden">
            <div className="border-b border-white/8 px-6 py-5">
              <div className="text-xs uppercase tracking-[0.28em] text-cyan-300/80 mb-2">Stack frame</div>
              <h2 className="text-2xl font-bold text-white">BreezeML Level 2 — results</h2>
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

        {/* Two-column layout */}
        <div className="grid gap-8 lg:grid-cols-[1.02fr_0.98fr]">

          {/* Left: input */}
          <div className="flex flex-col gap-6">
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
                rows={11}
                placeholder="Paste a company description here..."
                className="w-full resize-none bg-transparent text-lg leading-relaxed text-white outline-none placeholder:text-white/12 font-mono"
              />

              <div className="mt-6 grid gap-3 sm:grid-cols-2">
                {EXAMPLES.map((example) => (
                  <button
                    key={example.label}
                    onClick={() => setText(example.text)}
                    className="rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3 text-left transition-colors hover:bg-white/[0.08]"
                  >
                    <div className="text-xs uppercase tracking-[0.24em] text-white/35 mb-1">{example.label}</div>
                    <div className="text-sm text-white/58 leading-relaxed">{example.text.slice(0, 86)}...</div>
                  </button>
                ))}
              </div>
            </GlowCard>

            <div className="grid gap-4 md:grid-cols-3">
              <div className="rounded-[28px] border border-white/10 bg-white/[0.03] p-5">
                <Activity className="h-5 w-5 text-red-300 mb-3" />
                <div className="text-sm font-semibold text-white mb-1">1,673 samples/sec</div>
                <div className="text-sm text-white/52">40× faster than DeBERTa, on CPU only.</div>
              </div>
              <div className="rounded-[28px] border border-white/10 bg-white/[0.03] p-5">
                <Gauge className="h-5 w-5 text-cyan-300 mb-3" />
                <div className="text-sm font-semibold text-white mb-1">Confidence routing</div>
                <div className="text-sm text-white/52">SVM → DeBERTa → Consensus, each explained.</div>
              </div>
              <div className="rounded-[28px] border border-white/10 bg-white/[0.03] p-5">
                <Map className="h-5 w-5 text-emerald-300 mb-3" />
                <div className="text-sm font-semibold text-white mb-1">4-taxonomy map</div>
                <div className="text-sm text-white/52">Every code mapped to GICS, NAICS, SIC.</div>
              </div>
            </div>

            <button
              onClick={runInference}
              disabled={loading || !text.trim()}
              className="w-full rounded-2xl bg-red-700 px-6 py-5 text-lg font-bold text-white transition-all hover:bg-red-600 hover:shadow-[0_0_45px_rgba(220,38,38,0.35)] disabled:cursor-not-allowed disabled:opacity-35 flex items-center justify-center gap-3"
            >
              {loading ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  Running BreezeML inference
                </>
              ) : (
                <>
                  <Zap className="h-5 w-5" />
                  Run BreezeML classification
                </>
              )}
            </button>
          </div>

          {/* Right: pipeline + results */}
          <div className="flex flex-col gap-6">

            {/* Pipeline visualiser */}
            <GlowCard glowColor="blue" className="border-white/8 bg-black/55 p-8">
              <div className="mb-6 flex items-center justify-between">
                <div>
                  <div className="text-xs uppercase tracking-[0.28em] text-white/35 mb-2">BreezeML Level 2</div>
                  <h2 className="text-2xl font-bold text-white">BreezeML reads the taxonomy structure.</h2>
                </div>
                <div className="font-mono text-xs text-white/25">
                  {activeStep < 0
                    ? "IDLE"
                    : activeStep >= PIPELINE.length
                      ? "COMPLETE"
                      : `STEP ${activeStep + 1}/${PIPELINE.length}`}
                </div>
              </div>

              <div className="space-y-5">
                {PIPELINE.map((step, index) => {
                  const active = activeStep === index;
                  const done = activeStep > index;
                  return (
                    <div key={step.id} className="flex items-center gap-5">
                      <motion.div
                        animate={{
                          backgroundColor: done ? "#10b981" : active ? "#dc2626" : "rgba(255,255,255,0.06)",
                          boxShadow: active
                            ? "0 0 22px rgba(220,38,38,0.45)"
                            : done
                              ? "0 0 14px rgba(16,185,129,0.28)"
                              : "none",
                        }}
                        transition={{ duration: 0.3 }}
                        className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-2xl"
                      >
                        <step.icon className="h-5 w-5 text-white" />
                      </motion.div>
                      <div className="flex-1">
                        <div className={`text-lg font-semibold ${done ? "text-emerald-400" : active ? "text-red-400" : "text-white/40"}`}>
                          {step.label}
                        </div>
                        <div className="text-sm text-white/28">{step.detail}</div>
                      </div>
                      {done ? (
                        <span className="font-mono text-xs uppercase tracking-[0.24em] text-emerald-400">Done</span>
                      ) : active ? (
                        <Loader2 className="h-4 w-4 animate-spin text-red-400" />
                      ) : (
                        <ChevronRight className="h-4 w-4 text-white/15" />
                      )}
                    </div>
                  );
                })}
              </div>
            </GlowCard>

            {/* Results */}
            <AnimatePresence mode="wait">
              {error ? (
                <motion.div
                  key="error"
                  initial={{ opacity: 0, y: 18 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="rounded-[28px] border border-red-500/25 bg-red-500/10 px-6 py-6 text-red-200"
                >
                  {error}
                </motion.div>

              ) : result ? (
                <motion.div
                  key={`result-${resultKey}`}
                  initial={{ opacity: 0, y: 18, scale: 0.98 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.45 }}
                  className="flex flex-col gap-6"
                >
                  {/* Engine badge + route reason */}
                  <div className={`flex items-center gap-3 rounded-2xl border px-4 py-3 ${engineStyle?.badge}`}>
                    <span className={`h-2 w-2 flex-shrink-0 rounded-full ${engineStyle?.dot}`} />
                    <span className="font-semibold text-sm flex-shrink-0">{result.engine}</span>
                    {result.route_reason && (
                      <span className="text-xs text-white/40 ml-auto leading-tight line-clamp-2 text-right">
                        {result.route_reason}
                      </span>
                    )}
                  </div>

                  {/* Main verdict */}
                  <GlowCard glowColor={engineStyle?.glow ?? "red"} className="border-white/8 bg-red-500/[0.05] p-8">
                    <div className="mb-4 text-xs uppercase tracking-[0.28em] text-red-300/80">
                      Morningstar GECS verdict
                    </div>
                    <TextScramble
                      key={`mstar-${resultKey}`}
                      as="h3"
                      speed={0.02}
                      duration={0.8}
                      className="text-3xl sm:text-4xl font-bold text-white mb-4"
                    >
                      {result.mstar_label}
                    </TextScramble>
                    <div className="mb-6 inline-flex items-center gap-3 rounded-2xl border border-red-500/15 bg-black/30 px-4 py-3 font-mono text-red-200">
                      <span>{result.mstar_code}</span>
                      <span className="text-white/20">|</span>
                      <span className="text-white/45">MSTAR-GECS</span>
                    </div>
                    <ConfidenceBar label="Classification confidence" value={result.confidence} tone="red" />
                  </GlowCard>

                  {/* Analyst memo */}
                  {result.explanation && (
                    <GlowCard glowColor="blue" className="border-white/8 bg-blue-500/[0.04] p-6">
                      <div className="mb-3 flex items-center gap-2">
                        <FileText className="h-4 w-4 text-cyan-300" />
                        <div className="text-xs uppercase tracking-[0.28em] text-cyan-300/80">Analyst Memo</div>
                      </div>
                      <p className="text-sm leading-relaxed text-white/70 italic">
                        &ldquo;{result.explanation}&rdquo;
                      </p>
                    </GlowCard>
                  )}

                  {/* Cross-taxonomy grid */}
                  {result.taxonomy_map?.status === "mapped" && (
                    <GlowCard glowColor="emerald" className="border-white/8 bg-white/[0.03] p-6">
                      <div className="mb-4 flex items-center gap-2">
                        <Map className="h-4 w-4 text-emerald-300" />
                        <div className="text-xs uppercase tracking-[0.28em] text-emerald-300/80">
                          Cross-Taxonomy Map
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        {(["mstar", "gics", "naics", "sic"] as const).map((key) => {
                          const entry = result.taxonomy_map?.[key];
                          const meta = TAXONOMY_META[key];
                          if (!entry) return null;
                          return (
                            <div key={key} className="rounded-xl border border-white/8 bg-black/30 px-4 py-3">
                              <div className={`text-xs uppercase tracking-[0.22em] mb-1 ${meta.color}`}>
                                {meta.abbr}
                              </div>
                              <div className="font-mono text-xs text-white/40 mb-1">{entry.code}</div>
                              <div className="text-sm font-semibold text-white leading-tight">{entry.label}</div>
                            </div>
                          );
                        })}
                      </div>
                    </GlowCard>
                  )}

                  {/* Alternatives */}
                  {result.alternatives && result.alternatives.length > 0 && (
                    <GlowCard glowColor="amber" className="border-white/8 bg-white/[0.03] p-6">
                      <div className="mb-4 text-xs uppercase tracking-[0.28em] text-white/35">
                        Top alternatives
                      </div>
                      <div className="space-y-3">
                        {result.alternatives.slice(0, 3).map((alt) => (
                          <div
                            key={`${alt.rank}-${alt.code}`}
                            className="rounded-2xl border border-white/8 bg-black/30 px-4 py-4"
                          >
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
                </motion.div>

              ) : (
                <motion.div
                  key="placeholder"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="rounded-[28px] border border-white/8 bg-white/[0.03] px-8 py-12 text-center"
                >
                  <Cpu className="mx-auto mb-4 h-12 w-12 text-white/12" />
                  <div className="text-xl font-mono text-white/25">
                    Paste a company description to classify.
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </section>
  );
}
