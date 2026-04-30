"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  Activity,
  BrainCircuit,
  ChevronRight,
  Cpu,
  Database,
  Gauge,
  Loader2,
  Radar,
  Sparkles,
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
  { id: "input", icon: Terminal, label: "Raw Text", detail: "Company description" },
  { id: "tfidf", icon: Database, label: "TF-IDF", detail: "50,000 sparse features" },
  { id: "sparse", icon: Cpu, label: "Sparse Matrix", detail: "CSR numerical representation" },
  { id: "svm", icon: BrainCircuit, label: "Linear SVM", detail: "Balanced classifier verdict" },
];

const SYSTEM_NOTES = [
  { label: "Serving model", value: "Linear SVM" },
  { label: "Vector space", value: "50K TF-IDF" },
  { label: "Best metric", value: "86.82% Macro F1" },
  { label: "Deployment stance", value: "Fast and dependable" },
];

type Alternative = {
  rank: number;
  code: string;
  label: string;
  confidence: number;
};

type Result = {
  mstar_code: string;
  mstar_label: string;
  sub_code: string;
  sub_label: string;
  confidence_t1?: number | null;
  confidence_t2?: number | null;
  alternatives_t1?: Alternative[];
  alternatives_t2?: Alternative[];
  features_t1?: string[];
  features_t2?: string[];
};

function ConfidenceBar({ label, value, tone }: { label: string; value?: number | null; tone: "red" | "blue" }) {
  const safeValue = Math.max(0, Math.min(100, value ?? 0));
  const fillClass = tone === "red" ? "from-red-500 to-rose-400" : "from-cyan-500 to-blue-400";

  return (
    <div>
      <div className="mb-2 flex items-center justify-between text-sm">
        <span className="text-white/55">{label}</span>
        <span className="font-mono text-white">{value == null ? "N/A" : `${safeValue.toFixed(1)}%`}</span>
      </div>
      <div className="h-3 rounded-full bg-white/8 overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${safeValue}%` }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className={`h-full rounded-full bg-gradient-to-r ${fillClass}`}
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
    setActiveStep(0);

    for (let i = 0; i < PIPELINE.length; i++) {
      setActiveStep(i);
      await new Promise((resolve) => setTimeout(resolve, 320));
    }

    try {
      const res = await fetch("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || "Server error");
      }

      setResult(data);
      setResultKey((key) => key + 1);
      setActiveStep(PIPELINE.length);
    } catch (err: any) {
      setError(err.message || "Could not reach the classification server.");
      setActiveStep(-1);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="min-h-screen px-6 py-20 overflow-hidden">
      <div className="mx-auto max-w-7xl">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.65 }}
          className="mb-14 grid gap-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-end"
        >
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-red-500/20 bg-red-500/10 px-4 py-2 text-xs uppercase tracking-[0.3em] text-red-300">
              <Radar className="h-3.5 w-3.5" />
              Prediction Lab
            </div>
            <h1 className="mt-6 text-5xl sm:text-6xl lg:text-7xl font-black tracking-tight text-white">
              Turn raw company language
              <span className="block text-white/55">into a model verdict you can inspect.</span>
            </h1>
            <p className="mt-6 max-w-3xl text-lg sm:text-xl leading-relaxed text-white/55">
              This is not just a text box. It is a full inference surface showing the sparse pipeline,
              the predicted GECS labels, confidence estimates, competing classes, and the features that drove the decision.
            </p>
          </div>

          <GlowCard glowColor="cyan" className="border-white/8 bg-white/[0.03] p-0 overflow-hidden">
            <div className="border-b border-white/8 px-6 py-5">
              <div className="text-xs uppercase tracking-[0.28em] text-cyan-300/80 mb-2">System frame</div>
              <h2 className="text-2xl font-bold text-white">Why this demo matters</h2>
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

        <div className="grid gap-8 lg:grid-cols-[1.02fr_0.98fr]">
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
                onChange={(event) => setText(event.target.value)}
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
                    <div className="text-sm text-white/58 leading-relaxed">
                      {example.text.slice(0, 86)}...
                    </div>
                  </button>
                ))}
              </div>
            </GlowCard>

            <div className="grid gap-4 md:grid-cols-3">
              <div className="rounded-[28px] border border-white/10 bg-white/[0.03] p-5">
                <Activity className="h-5 w-5 text-red-300 mb-3" />
                <div className="text-sm font-semibold text-white mb-1">Fast verdicts</div>
                <div className="text-sm text-white/52">Sparse inference keeps the experience responsive.</div>
              </div>
              <div className="rounded-[28px] border border-white/10 bg-white/[0.03] p-5">
                <Gauge className="h-5 w-5 text-cyan-300 mb-3" />
                <div className="text-sm font-semibold text-white mb-1">Interpretable output</div>
                <div className="text-sm text-white/52">Confidence bands and feature signals explain the result.</div>
              </div>
              <div className="rounded-[28px] border border-white/10 bg-white/[0.03] p-5">
                <Sparkles className="h-5 w-5 text-emerald-300 mb-3" />
                <div className="text-sm font-semibold text-white mb-1">Production stance</div>
                <div className="text-sm text-white/52">The winning model is the one we could actually trust to ship.</div>
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
                  Running classification
                </>
              ) : (
                <>
                  <Zap className="h-5 w-5" />
                  Run prediction lab
                </>
              )}
            </button>
          </div>

          <div className="flex flex-col gap-6">
            <GlowCard glowColor="blue" className="border-white/8 bg-black/55 p-8">
              <div className="mb-6 flex items-center justify-between">
                <div>
                  <div className="text-xs uppercase tracking-[0.28em] text-white/35 mb-2">Inference pipeline</div>
                  <h2 className="text-2xl font-bold text-white">The classifier is not a black box.</h2>
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
                  <GlowCard glowColor="red" className="border-white/8 bg-red-500/[0.05] p-8">
                    <div className="mb-4 text-xs uppercase tracking-[0.28em] text-red-300/80">Task 1 verdict</div>
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
                      <span className="text-white/45">MSTAR-GLOBAL</span>
                    </div>
                    <ConfidenceBar label="Industry confidence" value={result.confidence_t1} tone="red" />
                  </GlowCard>

                  <GlowCard glowColor="blue" className="border-white/8 bg-cyan-500/[0.04] p-8">
                    <div className="mb-4 text-xs uppercase tracking-[0.28em] text-cyan-300/80">Task 2 verdict</div>
                    <TextScramble
                      key={`sub-${resultKey}`}
                      as="h3"
                      speed={0.02}
                      duration={0.85}
                      className="text-3xl sm:text-4xl font-bold text-white mb-4"
                    >
                      {result.sub_label}
                    </TextScramble>
                    <div className="mb-6 inline-flex items-center gap-3 rounded-2xl border border-cyan-500/15 bg-black/30 px-4 py-3 font-mono text-cyan-200">
                      <span>{result.sub_code}</span>
                      <span className="text-white/20">|</span>
                      <span className="text-white/45">SUBINDUSTRY</span>
                    </div>
                    <ConfidenceBar label="Subindustry confidence" value={result.confidence_t2} tone="blue" />
                  </GlowCard>

                  <div className="grid gap-6 xl:grid-cols-2">
                    <GlowCard glowColor="amber" className="border-white/8 bg-white/[0.03] p-6">
                      <div className="mb-4 text-xs uppercase tracking-[0.28em] text-white/35">Top task 1 alternatives</div>
                      <div className="space-y-3">
                        {(result.alternatives_t1 ?? []).slice(0, 3).map((alt) => (
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

                    <GlowCard glowColor="emerald" className="border-white/8 bg-white/[0.03] p-6">
                      <div className="mb-4 text-xs uppercase tracking-[0.28em] text-white/35">What pushed the model</div>
                      <div className="flex flex-wrap gap-2">
                        {(result.features_t1 ?? []).concat(result.features_t2 ?? []).slice(0, 10).map((feature) => (
                          <span
                            key={feature}
                            className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-white/65"
                          >
                            {feature}
                          </span>
                        ))}
                      </div>
                    </GlowCard>
                  </div>
                </motion.div>
              ) : (
                <motion.div
                  key="placeholder"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="rounded-[28px] border border-white/8 bg-white/[0.03] px-8 py-12 text-center"
                >
                  <Cpu className="mx-auto mb-4 h-12 w-12 text-white/12" />
                  <div className="text-xl font-mono text-white/25">Prediction lab is armed and ready.</div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </section>
  );
}
