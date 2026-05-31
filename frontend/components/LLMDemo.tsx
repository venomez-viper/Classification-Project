"use client";
import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Activity,
  BrainCircuit,
  Cpu,
  Loader2,
  Network,
  Server,
  Sparkles,
  Terminal,
} from "lucide-react";
import { GlowCard } from "@/components/ui/spotlight-card";
import { TextScramble } from "@/components/ui/text-scramble";

// These examples are written in plain English — no financial jargon.
// The point: DeBERTa understands MEANING, not just keyword matching.
const EXAMPLES = [
  {
    label: "Plain English — Chips",
    text: "The company designs tiny silicon chips that go inside smartphones, laptops, and data centers to make them run fast.",
  },
  {
    label: "Plain English — Banking",
    text: "The business takes deposits from regular people and lends that money out as home loans and small business credit in local communities.",
  },
  {
    label: "Plain English — Medicine",
    text: "Scientists at this company spend years in laboratories trying to find new drugs that can stop cancer cells from growing.",
  },
  {
    label: "Plain English — Energy",
    text: "Workers drill deep holes into the earth and the ocean floor to find pockets of crude oil and natural gas that they pump out and sell.",
  },
  {
    label: "Plain English — Software",
    text: "The company sells software that helps large businesses manage their employees, finances, and supply chains from a single dashboard.",
  },
  {
    label: "Plain English — Defence",
    text: "The firm builds fighter jets, missiles, and radar systems under government contracts for national defence programs.",
  },
];

const PIPELINE = [
  { id: "input",  icon: Terminal,     label: "Raw text",            detail: "Any natural language description" },
  { id: "tok",    icon: Network,      label: "Tokenisation",        detail: "DeBERTa SentencePiece, 128K vocab" },
  { id: "layers", icon: BrainCircuit, label: "12 attention layers", detail: "Cross-word meaning, not keywords" },
  { id: "head",   icon: Sparkles,     label: "Classification head", detail: "Softmax over 145 Morningstar codes" },
];

const TERMINAL_LOGS = [
  "> Initialising CUDA device 0  [RTX 3050]...",
  "> Allocating 1.2 GB VRAM...",
  "> Loading DeBERTa-v3-small weights (180 M params)...",
  "> Model weights loaded. Status: ONLINE",
  "> Tokenising input sequence...",
  "> Attention mask generated.",
  "> Forward pass — layer  1 / 12...",
  "> Forward pass — layer  4 / 12...",
  "> Forward pass — layer  8 / 12...",
  "> Forward pass — layer 12 / 12...",
  "> Extracting logits from classification head...",
  "> Computing softmax probabilities over 145 classes...",
  "> Inference complete.",
];

type Alternative = { rank: number; code: string; label: string; confidence: number };

type Result = {
  success: boolean;
  engine?: string;
  mstar_code: string;
  mstar_label: string;
  confidence: number;
  alternatives?: Alternative[];
  task2_ready?: boolean;
  sub_code?: string;
  sub_label?: string;
  sub_confidence?: number;
  sub_alternatives?: Alternative[];
};

type T2Result = {
  sub_code: string;
  sub_label: string;
  confidence_t2: number;
  alternatives_t2?: Alternative[];
  source: "deberta" | "cascade";
};

function ConfidenceBar({ value }: { value: number }) {
  const safe = Math.max(0, Math.min(100, value));
  const color =
    safe >= 70 ? "from-emerald-500 to-teal-400"
    : safe >= 45 ? "from-cyan-500 to-blue-400"
    : "from-amber-500 to-yellow-400";

  return (
    <div>
      <div className="mb-2 flex items-center justify-between text-xs font-mono">
        <span className="text-purple-300/60">CONFIDENCE</span>
        <span className="text-white">{safe.toFixed(1)}%</span>
      </div>
      <div className="h-2 rounded-full bg-white/8 overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${safe}%` }}
          transition={{ duration: 0.7, ease: "easeOut" }}
          className={`h-full rounded-full bg-gradient-to-r ${color}`}
        />
      </div>
    </div>
  );
}

export default function LLMDemo() {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeStep, setActiveStep] = useState(-1);
  const [result, setResult] = useState<Result | null>(null);
  const [t2, setT2] = useState<T2Result | null>(null);
  const [error, setError] = useState("");
  const [resultKey, setResultKey] = useState(0);
  const [logs, setLogs] = useState<string[]>([]);
  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  async function runInference() {
    if (!text.trim() || loading) return;
    setLoading(true);
    setResult(null);
    setT2(null);
    setError("");
    setActiveStep(0);
    setLogs([]);

    let logIndex = 0;
    const logInterval = setInterval(() => {
      if (logIndex < TERMINAL_LOGS.length) {
        setLogs((prev) => [...prev, TERMINAL_LOGS[logIndex]]);
        logIndex++;
      } else {
        clearInterval(logInterval);
      }
    }, 160);

    for (let i = 0; i < PIPELINE.length; i++) {
      setActiveStep(i);
      await new Promise((r) => setTimeout(r, 600));
    }

    try {
      // Fetch the compatibility endpoint and the canonical cascade endpoint in parallel.
      const [llmRes, cascadeRes] = await Promise.allSettled([
        fetch("/api/predict_llm",  { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ company_text: text, segment_text: text }) }),
        fetch("/api/predict",      { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ company_text: text, segment_text: text }) }),
      ]);

      if (llmRes.status === "rejected") throw new Error("Could not reach GECS-Sage on port 5003.");
      const llmData = await llmRes.value.json();
      if (!llmRes.value.ok) throw new Error(llmData.error || "GECS-Sage server error");

      setResult(llmData);
      setResultKey((k) => k + 1);
      setActiveStep(PIPELINE.length);

      // Resolve Task 2: prefer DeBERTa T2, fall back to cascade T2
      if (llmData.task2_ready && llmData.sub_code) {
        setT2({ sub_code: llmData.sub_code, sub_label: llmData.sub_label ?? llmData.sub_code, confidence_t2: llmData.sub_confidence ?? 0, sub_alternatives: llmData.sub_alternatives, source: "deberta" });
      } else if (cascadeRes.status === "fulfilled" && cascadeRes.value.ok) {
        const cData = await cascadeRes.value.json();
        if (cData.sub_code && cData.sub_code !== "N/A") {
          setT2({ sub_code: cData.sub_code, sub_label: cData.sub_label ?? cData.sub_code, confidence_t2: cData.confidence_t2 ?? 0, sub_alternatives: cData.alternatives_t2, source: "cascade" });
        }
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Could not reach GECS-Sage on port 5003.";
      setError(msg);
      setActiveStep(-1);
    } finally {
      setLoading(false);
      clearInterval(logInterval);
    }
  }

  return (
    <section className="min-h-screen py-16 px-6 relative overflow-hidden">
      {/* Grid background */}
      <div
        className="absolute inset-0 pointer-events-none opacity-20"
        style={{
          backgroundImage:
            "linear-gradient(rgba(147,51,234,0.2) 1px, transparent 1px), linear-gradient(90deg, rgba(147,51,234,0.2) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[400px] bg-purple-900/30 blur-[120px] rounded-full pointer-events-none" />

      <div className="max-w-7xl mx-auto relative z-10">

        {/* Telemetry bar */}
        <div className="flex flex-wrap items-center justify-between gap-4 mb-12 border-b border-purple-500/20 pb-4">
          <div className="flex flex-wrap items-center gap-6 text-xs sm:text-sm font-mono text-purple-300">
            <span className="flex items-center gap-2"><Server className="w-4 h-4 text-purple-500" /> MODEL: DEBERTA-V3-SMALL</span>
            <span className="flex items-center gap-2"><Cpu className="w-4 h-4 text-cyan-500" /> PARAMS: 180,000,000</span>
            <span className="flex items-center gap-2"><Activity className="w-4 h-4 text-emerald-500" /> ACCELERATOR: CUDA:0</span>
          </div>
          <div className="text-xs font-mono px-3 py-1 bg-purple-500/10 border border-purple-500/30 rounded text-purple-400">
            SYSTEM STATUS: ONLINE
          </div>
        </div>

        {/* Header */}
        <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} className="mb-12">
          <TextScramble as="p" speed={0.02} duration={0.8}
            className="text-cyan-400 text-base font-semibold uppercase tracking-widest mb-4 font-mono">
            TRANSFORMER INFERENCE — NATURAL LANGUAGE UNDERSTANDING
          </TextScramble>
          <h1 className="text-5xl sm:text-6xl font-bold text-white mb-4 tracking-tight">
            Write it in plain English.{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-cyan-400">
              DeBERTa gets it.
            </span>
          </h1>
          <p className="text-lg text-white/50 max-w-2xl">
            TF-IDF needs exact financial keywords. A transformer reads the{" "}
            <span className="text-white/80 font-semibold">meaning</span> of your sentence —
            even if you never use a single piece of industry jargon.
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-10">

          {/* LEFT: Input */}
          <div className="flex flex-col gap-6">
            <GlowCard glowColor="purple" className="flex-1 p-8 border-purple-500/20 bg-black/60 backdrop-blur-md">
              <div className="flex items-center gap-3 mb-6 pb-4 border-b border-purple-500/20">
                <div className="flex gap-1.5">
                  <span className="w-3 h-3 rounded-sm bg-red-500/80 shadow-[0_0_8px_rgba(239,68,68,0.6)]" />
                  <span className="w-3 h-3 rounded-sm bg-amber-400/80" />
                  <span className="w-3 h-3 rounded-sm bg-emerald-500/80" />
                </div>
                <span className="text-sm text-purple-300/50 ml-3 font-mono">natural_language_input.txt</span>
              </div>

              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={10}
                placeholder="Describe any company in plain English — no jargon needed..."
                className="w-full bg-transparent text-purple-50 text-lg leading-relaxed resize-none outline-none placeholder:text-purple-300/20 font-mono"
              />
            </GlowCard>

            {/* Example buttons */}
            <div className="grid grid-cols-2 gap-3">
              {EXAMPLES.map((ex) => (
                <button
                  key={ex.label}
                  onClick={() => setText(ex.text)}
                  className="px-3 py-2 rounded text-xs border border-cyan-500/30 bg-cyan-950/30 hover:bg-cyan-900/50 text-cyan-300 hover:text-cyan-100 transition-all font-mono uppercase tracking-wider text-left"
                >
                  {ex.label}
                </button>
              ))}
            </div>

            <button
              onClick={runInference}
              disabled={loading || !text.trim()}
              className="w-full py-5 rounded-md bg-purple-600/20 border border-purple-500/50 hover:bg-purple-600/40 disabled:opacity-35 disabled:cursor-not-allowed text-purple-100 font-bold text-lg tracking-[0.2em] font-mono transition-all hover:shadow-[0_0_30px_rgba(147,51,234,0.5)] flex items-center justify-center gap-4"
            >
              {loading
                ? <><Loader2 className="w-5 h-5 animate-spin text-purple-300" /> RUNNING INFERENCE...</>
                : <><BrainCircuit className="w-5 h-5 text-purple-300" /> EXECUTE DEBERTA</>}
            </button>
          </div>

          {/* RIGHT: Pipeline + results */}
          <div className="flex flex-col gap-8">

            <GlowCard glowColor="cyan" className="p-8 border-cyan-500/20 bg-black/60 backdrop-blur-md">
              {loading ? (
                <div className="bg-black/80 border border-purple-500/30 p-4 rounded font-mono text-xs text-green-400 overflow-y-auto max-h-[320px] shadow-[inset_0_0_20px_rgba(147,51,234,0.15)] flex flex-col gap-1">
                  {logs.map((log, i) => (
                    <motion.div key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}>
                      {log}
                    </motion.div>
                  ))}
                  <div ref={logsEndRef} />
                </div>
              ) : (
                <div className="flex flex-col gap-6">
                  <p className="text-xs text-cyan-400/50 uppercase tracking-widest font-mono">
                    Neural Pipeline Status
                  </p>
                  {PIPELINE.map((step, i) => {
                    const isActive = activeStep === i;
                    const isDone = activeStep > i;
                    return (
                      <div key={step.id} className="flex items-center gap-6">
                        <motion.div
                          animate={{
                            backgroundColor: isDone ? "rgba(6,182,212,0.2)" : isActive ? "rgba(168,85,247,0.3)" : "rgba(255,255,255,0.03)",
                            boxShadow: isActive ? "0 0 20px rgba(168,85,247,0.5)" : isDone ? "0 0 10px rgba(6,182,212,0.3)" : "none",
                            borderColor: isActive ? "rgba(168,85,247,0.8)" : isDone ? "rgba(6,182,212,0.5)" : "rgba(255,255,255,0.1)",
                          }}
                          transition={{ duration: 0.3 }}
                          className="w-12 h-12 border rounded-sm flex items-center justify-center flex-shrink-0"
                        >
                          <step.icon className={`w-5 h-5 ${isActive ? "text-purple-300" : isDone ? "text-cyan-300" : "text-white/20"}`} />
                        </motion.div>
                        <div className="flex-1">
                          <p className={`text-lg font-mono tracking-wide transition-colors ${isDone ? "text-cyan-400" : isActive ? "text-purple-400" : "text-white/30"}`}>
                            {step.label}
                          </p>
                          <p className="text-xs font-mono text-white/25 mt-1">{step.detail}</p>
                        </div>
                        {isDone && <span className="font-mono text-xs text-cyan-400 uppercase tracking-widest">Done</span>}
                        {isActive && <Loader2 className="w-4 h-4 animate-spin text-purple-400" />}
                      </div>
                    );
                  })}
                </div>
              )}
            </GlowCard>

            <AnimatePresence mode="wait">
              {error && (
                <motion.div
                  key="error"
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="rounded border border-red-500 bg-red-950/40 text-red-400 font-mono text-sm p-6 shadow-[0_0_15px_rgba(239,68,68,0.3)]"
                >
                  <p className="font-bold mb-2">INFERENCE ERROR</p>
                  <p>{error}</p>
                  <p className="mt-3 text-red-300/60 text-xs">
                    Make sure GECS-Sage is running: <span className="text-red-200">python server_legendary.py</span>
                  </p>
                </motion.div>
              )}

              {result && (
                <motion.div
                  key={`result-${resultKey}`}
                  initial={{ opacity: 0, scale: 0.96, filter: "blur(12px)" }}
                  animate={{ opacity: 1, scale: 1, filter: "blur(0px)" }}
                  transition={{ duration: 0.5, ease: "easeOut" }}
                  className="flex flex-col gap-5"
                >
                  {/* Task 1 — industry */}
                  <GlowCard glowColor="purple" className="p-8 border-purple-500/40 bg-purple-950/20 backdrop-blur-md">
                    <div className="flex justify-between items-center mb-5">
                      <p className="text-xs text-purple-400 uppercase tracking-[0.3em] font-mono">
                        Industry — Morningstar GECS
                      </p>
                      <span className="text-xs font-mono text-purple-300/60 bg-purple-400/10 px-2 py-1 rounded border border-purple-400/20">
                        {result.engine ?? "DeBERTa-v3-small"}
                      </span>
                    </div>

                    <TextScramble
                      key={`t1-${resultKey}`}
                      as="h3"
                      speed={0.02}
                      duration={0.8}
                      className="text-3xl sm:text-4xl font-bold text-white mb-2 text-center tracking-tight"
                    >
                      {result.mstar_label}
                    </TextScramble>
                    <p className="text-center font-mono text-sm text-purple-300/50 mb-5">{result.mstar_code}</p>

                    <ConfidenceBar value={result.confidence} />

                    {result.alternatives && result.alternatives.length > 1 && (
                      <div className="mt-5 space-y-2">
                        <p className="text-xs text-white/30 uppercase tracking-widest font-mono mb-2">Alternatives</p>
                        {result.alternatives.slice(1).map((alt) => (
                          <div key={alt.code} className="flex items-center justify-between gap-3 rounded border border-white/8 bg-black/30 px-3 py-2">
                            <div>
                              <div className="text-sm text-white/70">{alt.label}</div>
                              <code className="font-mono text-xs text-white/30">{alt.code}</code>
                            </div>
                            <div className="font-mono text-xs text-cyan-300 flex-shrink-0">{alt.confidence.toFixed(1)}%</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </GlowCard>

                  {/* Task 2 — subindustry */}
                  {t2 ? (
                    <GlowCard glowColor="cyan" className="p-8 border-cyan-500/40 bg-cyan-950/10 backdrop-blur-md">
                      <div className="flex justify-between items-center mb-5">
                        <p className="text-xs text-cyan-400 uppercase tracking-[0.3em] font-mono">
                          Sub-Industry — 428 classes
                        </p>
                        <span className={`text-xs font-mono px-2 py-1 rounded border ${t2.source === "deberta" ? "text-purple-300/60 bg-purple-400/10 border-purple-400/20" : "text-cyan-300/60 bg-cyan-400/10 border-cyan-400/20"}`}>
                          {t2.source === "deberta" ? "DeBERTa T2" : "Cascade SVM"}
                        </span>
                      </div>

                      <TextScramble
                        key={`t2-${resultKey}`}
                        as="h3"
                        speed={0.02}
                        duration={0.85}
                        className="text-3xl sm:text-4xl font-bold text-white mb-2 text-center tracking-tight"
                      >
                        {t2.sub_label}
                      </TextScramble>
                      <p className="text-center font-mono text-sm text-cyan-300/50 mb-5">{t2.sub_code}</p>

                      <ConfidenceBar value={t2.confidence_t2} />

                      {t2.sub_alternatives && t2.sub_alternatives.length > 1 && (
                        <div className="mt-5 space-y-2">
                          <p className="text-xs text-white/30 uppercase tracking-widest font-mono mb-2">Alternatives</p>
                          {t2.sub_alternatives.slice(1, 3).map((alt) => (
                            <div key={alt.code} className="flex items-center justify-between gap-3 rounded border border-white/8 bg-black/30 px-3 py-2">
                              <div>
                                <div className="text-sm text-white/70">{alt.label}</div>
                                <code className="font-mono text-xs text-white/30">{alt.code}</code>
                              </div>
                              <div className="font-mono text-xs text-cyan-300 flex-shrink-0">{alt.confidence.toFixed(1)}%</div>
                            </div>
                          ))}
                        </div>
                      )}
                    </GlowCard>
                  ) : result && (
                    <div className="rounded border border-dashed border-cyan-500/20 bg-cyan-950/10 px-6 py-5 font-mono text-xs text-cyan-400/40 text-center">
                      Sub-industry model offline — start server.py on port 5000 for cascade fallback.
                    </div>
                  )}
                </motion.div>
              )}

              {!error && !result && (
                <motion.div
                  key="placeholder"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="rounded border border-purple-500/15 bg-purple-950/10 px-8 py-12 text-center font-mono"
                >
                  <BrainCircuit className="mx-auto mb-4 h-12 w-12 text-purple-500/30" />
                  <p className="text-purple-300/30">
                    Write anything — no jargon required. DeBERTa reads meaning.
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
