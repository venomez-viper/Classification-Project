"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { BrainCircuit, Loader2, Sparkles, ExternalLink } from "lucide-react";
import Navigation from "@/components/Navigation";

const EXAMPLES = [
  {
    label: "Tech - Chips",
    text: "The company designs graphics processing units for gaming, data center AI, and autonomous vehicles. Revenue is driven by data center GPU sales.",
  },
  {
    label: "Finance - Banking",
    text: "JPMorgan Chase operates as a global financial services firm providing investment banking, commercial banking, and asset management.",
  },
  {
    label: "Healthcare - Pharma",
    text: "Pfizer discovers, develops, and commercializes biopharmaceutical products including vaccines, oncology therapies, and rare disease treatments.",
  },
  {
    label: "Energy - Oil & Gas",
    text: "ExxonMobil explores, produces, and refines petroleum products. Operates in upstream, downstream, and chemical segments across global markets.",
  },
  {
    label: "Tech - Software",
    text: "The company sells cloud-based enterprise software that helps large businesses manage their employees, finances, and supply chains from a single dashboard.",
  },
  {
    label: "Defence",
    text: "The firm builds fighter jets, missiles, and radar systems under long-term government contracts for national defence programs worldwide.",
  },
];

type Alternative = {
  rank: number;
  code: string;
  label: string;
  confidence: number;
};

type PredictResult = {
  mstar_code: string;
  mstar_label: string;
  confidence_t1: number;
  alternatives_t1?: Alternative[];
  sub_code?: string | null;
  sub_label?: string | null;
  confidence_t2?: number | null;
  alternatives_t2?: Alternative[];
  route_reason?: string;
  engine?: string;
};

function ConfidenceBar({ value, color = "emerald" }: { value: number; color?: string }) {
  const pct = Math.max(0, Math.min(100, value));
  const gradient =
    color === "cyan"
      ? "from-cyan-500 to-blue-400"
      : pct >= 70
      ? "from-emerald-500 to-teal-400"
      : pct >= 45
      ? "from-cyan-500 to-blue-400"
      : "from-amber-500 to-yellow-400";

  return (
    <div>
      <div className="flex justify-between text-xs font-mono mb-1">
        <span className="text-white/40">CONFIDENCE</span>
        <span className="text-white font-semibold">{pct.toFixed(1)}%</span>
      </div>
      <div className="h-1.5 rounded-full bg-white/10 overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className={`h-full rounded-full bg-gradient-to-r ${gradient}`}
        />
      </div>
    </div>
  );
}

export default function HFPage() {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PredictResult | null>(null);
  const [error, setError] = useState("");
  const [key, setKey] = useState(0);

  async function classify() {
    if (!text.trim() || loading) return;
    setLoading(true);
    setResult(null);
    setError("");

    try {
      const res = await fetch("/api/predict_hf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text.trim() }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "Prediction failed");
      setResult(data as PredictResult);
      setKey((k) => k + 1);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-black pt-20">
      <Navigation />

      <section className="py-16 px-6 max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-10">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-xs font-mono uppercase tracking-widest text-red-400">
              Hugging Face Space
            </span>
            <a
              href="https://akash-ag-gecs-classifier-space.hf.space"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-xs text-white/30 hover:text-white/60 transition-colors font-mono"
            >
              akash-ag-gecs-classifier-space <ExternalLink className="w-3 h-3" />
            </a>
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold text-white tracking-tight mb-3">
            GECS Industry{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-red-500 to-orange-400">
              Classifier
            </span>
          </h1>
          <p className="text-white/50 text-lg max-w-2xl">
            Paste any company description - the model maps it to one of{" "}
            <span className="text-white/80">145 Morningstar GECS</span> industry codes,
            then narrows it to a{" "}
            <span className="text-white/80">428-class sub-industry</span>.
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Input panel */}
          <div className="flex flex-col gap-4">
            <div className="rounded-xl border border-white/10 bg-white/3 p-6 flex flex-col gap-4">
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) classify();
                }}
                rows={9}
                placeholder="Paste a company description here…"
                className="w-full bg-transparent text-white text-base leading-relaxed resize-none outline-none placeholder:text-white/20 font-mono"
              />
              <div className="text-right text-xs font-mono text-white/20">
                Ctrl+Enter to classify
              </div>
            </div>

            {/* Examples */}
            <div className="grid grid-cols-2 gap-2">
              {EXAMPLES.map((ex) => (
                <button
                  key={ex.label}
                  onClick={() => setText(ex.text)}
                  className="px-3 py-2 rounded-lg text-xs border border-white/10 bg-white/4 hover:bg-white/10 text-white/50 hover:text-white transition-all font-mono text-left"
                >
                  {ex.label}
                </button>
              ))}
            </div>

            <button
              onClick={classify}
              disabled={loading || !text.trim()}
              className="w-full py-4 rounded-xl bg-red-600/20 border border-red-500/40 hover:bg-red-600/35 disabled:opacity-30 disabled:cursor-not-allowed text-red-100 font-bold text-base tracking-widest font-mono transition-all flex items-center justify-center gap-3"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" /> CLASSIFYING…
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" /> CLASSIFY
                </>
              )}
            </button>
          </div>

          {/* Results panel */}
          <div className="flex flex-col gap-4">
            <AnimatePresence mode="wait">
              {error && (
                <motion.div
                  key="error"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="rounded-xl border border-red-500/40 bg-red-950/30 p-6 font-mono text-sm text-red-400"
                >
                  <p className="font-bold mb-2">ERROR</p>
                  <p>{error}</p>
                </motion.div>
              )}

              {result && (
                <motion.div
                  key={`result-${key}`}
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4 }}
                  className="flex flex-col gap-4"
                >
                  {/* Task 1 */}
                  <div className="rounded-xl border border-red-500/30 bg-red-950/15 p-6">
                    <div className="flex justify-between items-center mb-4">
                      <p className="text-xs font-mono uppercase tracking-widest text-red-400">
                        Task 1 - GECS Industry
                      </p>
                      <span className="text-xs font-mono text-white/30 bg-white/5 px-2 py-0.5 rounded border border-white/10">
                        {result.engine ?? "cascade-svm"}
                      </span>
                    </div>

                    <p className="text-3xl font-bold text-white mb-1 tracking-tight">
                      {result.mstar_label}
                    </p>
                    <p className="font-mono text-sm text-white/40 mb-4">{result.mstar_code}</p>

                    <ConfidenceBar value={result.confidence_t1} />

                    {result.alternatives_t1 && result.alternatives_t1.length > 1 && (
                      <div className="mt-4 space-y-2">
                        <p className="text-xs font-mono text-white/30 uppercase tracking-widest mb-1">
                          Alternatives
                        </p>
                        {result.alternatives_t1.slice(1).map((alt) => (
                          <div
                            key={alt.code}
                            className="flex justify-between items-center rounded-lg border border-white/6 bg-black/30 px-3 py-2"
                          >
                            <div>
                              <p className="text-sm text-white/60">{alt.label}</p>
                              <code className="text-xs text-white/25 font-mono">{alt.code}</code>
                            </div>
                            <span className="font-mono text-xs text-white/50">
                              {alt.confidence.toFixed(1)}%
                            </span>
                          </div>
                        ))}
                      </div>
                    )}

                    {result.route_reason && (
                      <p className="mt-4 text-xs font-mono text-white/25 leading-relaxed">
                        {result.route_reason}
                      </p>
                    )}
                  </div>

                  {/* Task 2 */}
                  {result.sub_code ? (
                    <div className="rounded-xl border border-orange-500/25 bg-orange-950/10 p-6">
                      <p className="text-xs font-mono uppercase tracking-widest text-orange-400 mb-4">
                        Task 2 - Sub-Industry
                      </p>
                      <p className="text-2xl font-bold text-white mb-1 tracking-tight">
                        {result.sub_label ?? result.sub_code}
                      </p>
                      <p className="font-mono text-sm text-white/40 mb-4">{result.sub_code}</p>
                      <ConfidenceBar value={result.confidence_t2 ?? 0} color="cyan" />

                      {result.alternatives_t2 && result.alternatives_t2.length > 1 && (
                        <div className="mt-4 space-y-2">
                          <p className="text-xs font-mono text-white/30 uppercase tracking-widest mb-1">
                            Alternatives
                          </p>
                          {result.alternatives_t2.slice(1, 3).map((alt) => (
                            <div
                              key={alt.code}
                              className="flex justify-between items-center rounded-lg border border-white/6 bg-black/30 px-3 py-2"
                            >
                              <div>
                                <p className="text-sm text-white/60">{alt.label}</p>
                                <code className="text-xs text-white/25 font-mono">{alt.code}</code>
                              </div>
                              <span className="font-mono text-xs text-white/50">
                                {alt.confidence.toFixed(1)}%
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="rounded-xl border border-white/10 px-6 py-4 font-mono text-xs text-white/25 text-center">
                      Sub-industry not available for this industry code
                    </div>
                  )}
                </motion.div>
              )}

              {!error && !result && (
                <motion.div
                  key="placeholder"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="rounded-xl border border-white/8 bg-white/2 px-8 py-16 text-center"
                >
                  <BrainCircuit className="mx-auto mb-4 h-10 w-10 text-white/15" />
                  <p className="text-white/25 font-mono text-sm">
                    Results will appear here after classification
                  </p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </section>
    </main>
  );
}
