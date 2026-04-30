"use client";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2, ChevronRight, Terminal, Cpu, Database, Zap } from "lucide-react";
import { GlowCard } from "@/components/ui/spotlight-card";
import { TextScramble } from "@/components/ui/text-scramble";

const EXAMPLES = [
  {
    label: "Financial Services",
    text: "The company provides retail banking, mortgage loans, and investment portfolio management for individual and corporate clients across the United States.",
  },
  {
    label: "Cloud Computing",
    text: "The company develops and sells cloud computing services and enterprise software for businesses. Its main products include productivity tools and database services.",
  },
  {
    label: "Medical Devices",
    text: "The company manufactures surgical devices and diagnostic equipment used in hospitals and clinical settings globally.",
  },
  {
    label: "Oil and Gas",
    text: "The company explores and produces oil and natural gas from offshore and onshore fields in North America and the Gulf of Mexico.",
  },
];

const PIPELINE = [
  { id: "input",  icon: Terminal, label: "Raw Text",     detail: "Company description" },
  { id: "tfidf",  icon: Database, label: "TF-IDF",       detail: "50,000 bigram features" },
  { id: "sparse", icon: Cpu,      label: "Sparse CSR",   detail: "scipy.sparse matrix" },
  { id: "svm",    icon: Zap,      label: "Linear SVM",   detail: "dual=False, balanced" },
];

type Result = { mstar_code: string; mstar_label: string; sub_code: string; sub_label: string };

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
      await new Promise((r) => setTimeout(r, 380));
    }

    try {
      const res = await fetch("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Server error");
      setResult(data);
      setResultKey((k) => k + 1);
      setActiveStep(PIPELINE.length);
    } catch (e: any) {
      setError(e.message || "Could not reach the Flask server. Make sure it is running on port 5000.");
      setActiveStep(-1);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="min-h-screen py-24 px-6 scale-[1.02] transition-transform">
      <div className="max-w-7xl mx-auto">

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-16"
        >
          <TextScramble
            as="p"
            speed={0.02}
            duration={0.8}
            className="text-red-500 text-base font-semibold uppercase tracking-widest mb-4"
          >
            Live Inference
          </TextScramble>
          <h1 className="text-5xl sm:text-6xl font-bold text-white mb-5">
            GECS Classifier
          </h1>
          <p className="text-white/50 text-xl max-w-2xl">
            Paste any company description. The model runs TF-IDF vectorization and a
            Linear SVM in real time and tells you the Morningstar industry and subindustry.
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-10">

          {/* LEFT: Input panel */}
          <div className="flex flex-col gap-8">

            {/* Terminal input */}
            <GlowCard glowColor="red" className="flex-1 p-8">
              <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/8">
                <div className="flex gap-1.5">
                  <span className="w-3.5 h-3.5 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.4)]" />
                  <span className="w-3.5 h-3.5 rounded-full bg-amber-400" />
                  <span className="w-3.5 h-3.5 rounded-full bg-emerald-500" />
                </div>
                <span className="text-sm text-white/30 ml-3 font-mono">gecs_classifier.py</span>
              </div>

              <div className="font-mono text-sm text-white/30 mb-3">
                <span className="text-red-400">input</span> = <span className="text-amber-300">"""</span>
              </div>
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={10}
                placeholder="Paste company description here..."
                className="w-full bg-transparent text-white text-lg leading-relaxed resize-none outline-none placeholder:text-white/10 font-mono"
              />
              <div className="font-mono text-sm text-white/30 mt-3">
                <span className="text-amber-300">"""</span>
              </div>
            </GlowCard>

            {/* Example pills */}
            <div className="flex flex-wrap gap-3">
              {EXAMPLES.map((ex) => (
                <button
                  key={ex.label}
                  onClick={() => setText(ex.text)}
                  className="px-4 py-2 rounded-xl text-sm border border-white/10 bg-white/5 hover:bg-white/10 text-white/50 hover:text-white transition-all font-medium"
                >
                  {ex.label}
                </button>
              ))}
            </div>

            {/* Run button */}
            <button
              onClick={runInference}
              disabled={loading || !text.trim()}
              className="w-full py-5 rounded-2xl bg-red-700 hover:bg-red-600 disabled:opacity-35 disabled:cursor-not-allowed text-white font-bold text-lg tracking-wide transition-all hover:shadow-[0_0_50px_rgba(220,38,38,0.4)] flex items-center justify-center gap-4"
            >
              {loading
                ? <><Loader2 className="w-5 h-5 animate-spin" /> Running inference...</>
                : <><Zap className="w-5 h-5" /> Run Classification</>}
            </button>
          </div>

          {/* RIGHT: Pipeline + Result */}
          <div className="flex flex-col gap-8">

            {/* Animated pipeline */}
            <GlowCard glowColor="blue" className="p-8">
              <p className="text-sm text-white/30 uppercase tracking-widest font-mono mb-8">
                Inference Pipeline
              </p>
              <div className="flex flex-col gap-6">
                {PIPELINE.map((step, i) => {
                  const isActive = activeStep === i;
                  const isDone = activeStep > i;
                  return (
                    <div key={step.id} className="flex items-center gap-6">
                      <motion.div
                        animate={{
                          backgroundColor: isDone ? "#16a34a" : isActive ? "#dc2626" : "rgba(255,255,255,0.06)",
                          boxShadow: isActive ? "0 0 25px rgba(220,38,38,0.6)" : isDone ? "0 0 15px rgba(22,163,74,0.4)" : "none",
                        }}
                        transition={{ duration: 0.3 }}
                        className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
                      >
                        <step.icon className="w-5 h-5 text-white" />
                      </motion.div>
                      <div className="flex-1">
                        <p className={`text-lg font-semibold transition-colors ${isDone ? "text-emerald-400" : isActive ? "text-red-400" : "text-white/40"}`}>
                          {step.label}
                        </p>
                        <p className="text-sm text-white/25">{step.detail}</p>
                      </div>
                      {isDone && (
                        <motion.span initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} className="text-emerald-400 text-sm font-mono font-bold">
                          DONE
                        </motion.span>
                      )}
                      {isActive && (
                        <Loader2 className="w-5 h-5 text-red-400 animate-spin" />
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Pipeline connector lines */}
              <div className="mt-8 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
              <p className="text-sm text-white/20 font-mono mt-5 text-center">
                {activeStep < 0 ? "Waiting for system input..." : activeStep >= PIPELINE.length ? "Inference successfully completed" : `Currently Processing: ${PIPELINE[activeStep]?.label}`}
              </p>
            </GlowCard>

            {/* Result display */}
            <AnimatePresence mode="wait">
              {error && (
                <motion.div
                  key="error"
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="rounded-2xl border border-red-500/30 bg-red-500/10 text-red-300 text-base p-6 text-center"
                >
                  {error}
                </motion.div>
              )}

              {result && (
                <motion.div
                  key={`result-${resultKey}`}
                  initial={{ opacity: 0, scale: 0.96, filter: "blur(12px)" }}
                  animate={{ opacity: 1, scale: 1, filter: "blur(0px)" }}
                  transition={{ duration: 0.5, ease: "easeOut" }}
                  className="flex flex-col gap-6"
                >
                  {/* Task 1 */}
                  <GlowCard glowColor="red" className="p-8">
                    <p className="text-sm text-red-400/70 uppercase tracking-widest font-mono mb-4 text-center">
                      Task 1 — Industry Result
                    </p>
                    <TextScramble
                      key={`t1-${resultKey}`}
                      as="h3"
                      speed={0.02}
                      duration={0.8}
                      className="text-3xl sm:text-4xl font-bold text-white mb-4 text-center"
                    >
                      {result.mstar_label}
                    </TextScramble>
                    <div className="flex items-center justify-center gap-3">
                      <code className="text-lg font-mono bg-black/50 text-red-300/80 px-4 py-2 rounded-xl border border-red-500/10">
                        {result.mstar_code}
                      </code>
                      <ChevronRight className="w-5 h-5 text-white/20" />
                      <span className="text-sm font-semibold text-white/30 tracking-widest">MSTAR-GLOBAL</span>
                    </div>
                  </GlowCard>

                  {/* Task 2 */}
                  <GlowCard glowColor="blue" className="p-8">
                    <p className="text-sm text-blue-400/70 uppercase tracking-widest font-mono mb-4 text-center">
                      Task 2 — Subindustry Result
                    </p>
                    <TextScramble
                      key={`t2-${resultKey}`}
                      as="h3"
                      speed={0.02}
                      duration={0.9}
                      className="text-3xl sm:text-4xl font-bold text-white mb-4 text-center"
                    >
                      {result.sub_label}
                    </TextScramble>
                    <div className="flex justify-center">
                      <code className="text-lg font-mono bg-black/50 text-blue-300/80 px-4 py-2 rounded-xl border border-blue-500/10">
                        {result.sub_code}
                      </code>
                    </div>
                  </GlowCard>
                </motion.div>
              )}

              {!result && !error && (
                <motion.div
                  key="placeholder"
                  className="rounded-3xl border border-white/5 bg-white/3 p-12 text-center flex flex-col items-center gap-5"
                >
                  <Cpu className="w-12 h-12 text-white/10" />
                  <p className="text-white/20 text-lg font-mono">
                    Ready for real-time GECS classification.
                  </p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </section>
  );
}
