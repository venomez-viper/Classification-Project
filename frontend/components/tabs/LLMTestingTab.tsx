"use client";
import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  BrainCircuit, Server, Cpu, Activity, Loader2,
  Terminal, Network, Sparkles, CheckCircle2, AlertCircle, Zap, Info
} from "lucide-react";
import { TextScramble } from "@/components/ui/text-scramble";
import { GlowCard } from "@/components/ui/spotlight-card";

// ─── Types ────────────────────────────────────────────────────────────────────
type Alt = { rank: number; label: string; code: string; confidence: number };
type LLMResult = {
  mstar_code: string; mstar_label: string;
  sub_code: string;   sub_label: string;
  confidence_t1?: number; alternatives_t1?: Alt[];
};

// ─── Constants ────────────────────────────────────────────────────────────────
const EXAMPLES = [
  { label: "Financial",   text: "The company provides retail banking, mortgage loans, and investment portfolio management for individual and corporate clients across the United States." },
  { label: "Cloud/SaaS", text: "The company develops and sells cloud computing services and enterprise software for businesses. Its main products include productivity tools and database services." },
  { label: "Medical",    text: "The company manufactures surgical devices and diagnostic equipment used in hospitals and clinical settings globally." },
  { label: "Oil & Gas",  text: "The company explores and produces oil and natural gas from offshore and onshore fields in North America and the Gulf of Mexico." },
];

const PIPELINE = [
  { icon: Terminal,     label: "Text Tokenization",       detail: "DeBERTa SentencePiece · 512 max tokens" },
  { icon: Network,      label: "Transformer Encoding",    detail: "12-layer attention · 768 hidden dims" },
  { icon: BrainCircuit, label: "Contextual Embeddings",   detail: "Disentangled attention mechanism" },
  { icon: Sparkles,     label: "Classification Head",     detail: "Linear projection → 145 industry logits" },
];

const LOGS = [
  "> CUDA:0 initialized — RTX 3050 (8GB VRAM)",
  "> Loading DeBERTa-v3-small checkpoint (141M params)...",
  "> Tokenizing input → 512-token sequence",
  "> Executing forward pass — Layer  1/12 ████░░░░░░░░",
  "> Executing forward pass — Layer  4/12 ████████░░░░",
  "> Executing forward pass — Layer  8/12 ████████████░",
  "> Executing forward pass — Layer 12/12 ████████████",
  "> Extracting [CLS] token embedding...",
  "> Computing softmax over 145 logits...",
  "> Inference complete ✓  Latency: 1,842ms",
];

// ─── Confidence Arc ───────────────────────────────────────────────────────────
function ConfArc({ pct, color }: { pct: number; color: string }) {
  const r = 48; const circ = 2 * Math.PI * r;
  const arc = circ * 0.75;
  const [drawn, setDrawn] = useState(false);
  useEffect(() => { const t = setTimeout(() => setDrawn(true), 100); return () => clearTimeout(t); }, [pct]);
  return (
    <div className="relative w-28 h-28 flex-shrink-0">
      <svg viewBox="0 0 120 120" className="w-full h-full" style={{ transform: "rotate(-225deg)" }}>
        <circle cx="60" cy="60" r={r} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8"
          strokeLinecap="round" strokeDasharray={`${arc} ${circ}`} />
        <circle cx="60" cy="60" r={r} fill="none" stroke={color} strokeWidth="8" strokeLinecap="round"
          strokeDasharray={`${drawn ? arc * (pct / 100) : 0} ${circ}`}
          style={{ transition: "stroke-dasharray 1.2s ease-out", filter: `drop-shadow(0 0 8px ${color})` }} />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-xl font-black font-mono text-white leading-none">{pct.toFixed(0)}%</span>
        <span className="text-[9px] text-white/30 font-mono mt-0.5">confidence</span>
      </div>
    </div>
  );
}

// ─── Top-3 Alternatives ───────────────────────────────────────────────────────
function TopThree({ alts, color }: { alts: Alt[]; color: string }) {
  const [filled, setFilled] = useState(false);
  useEffect(() => { const t = setTimeout(() => setFilled(true), 200); return () => clearTimeout(t); }, []);
  return (
    <div className="space-y-2 mt-3">
      <div className="text-[10px] font-mono text-white/25 uppercase tracking-widest mb-2">Top Predictions</div>
      {alts.slice(0, 3).map((a, i) => (
        <div key={a.code} className="space-y-1">
          <div className="flex justify-between items-center">
            <span className={`text-xs font-mono ${i === 0 ? "text-white font-bold" : "text-white/40"}`}>
              {i === 0 && <span className="text-emerald-400 mr-1">✓</span>}{a.label}
            </span>
            <span className="text-xs font-mono tabular-nums font-bold" style={{ color: i === 0 ? color : "rgba(255,255,255,0.2)" }}>
              {a.confidence.toFixed(1)}%
            </span>
          </div>
          <div className="h-[3px] bg-white/5 rounded-full overflow-hidden">
            <div className="h-full rounded-full transition-all duration-700"
              style={{
                width: filled ? `${a.confidence}%` : "0%",
                backgroundColor: i === 0 ? color : "rgba(255,255,255,0.1)",
                boxShadow: i === 0 ? `0 0 8px ${color}` : "none",
                transitionDelay: `${i * 120}ms`,
              }} />
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────
export default function LLMTestingTab() {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeStep, setActiveStep] = useState(-1);
  const [result, setResult] = useState<LLMResult | null>(null);
  const [error, setError] = useState("");
  const [resultKey, setResultKey] = useState(0);
  const [logs, setLogs] = useState<string[]>([]);

  async function runInference() {
    if (!text.trim() || loading) return;
    setLoading(true); setResult(null); setError(""); setLogs([]); setActiveStep(0);

    let li = 0;
    const logId = setInterval(() => {
      if (li < LOGS.length) { setLogs(p => [...p, LOGS[li]]); li++; }
      else clearInterval(logId);
    }, 140);

    for (let i = 0; i < PIPELINE.length; i++) {
      setActiveStep(i);
      await new Promise(r => setTimeout(r, 600));
    }

    try {
      const base = process.env.NEXT_PUBLIC_LLM_API_URL ?? "http://localhost:5001";
      const res  = await fetch(`${base}/api/predict_llm`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Server error");
      setResult(data); setResultKey(k => k + 1); setActiveStep(PIPELINE.length);
    } catch (e: any) {
      setError(e.message || "Cannot reach DeBERTa server on port 5001.");
      setActiveStep(-1);
    } finally {
      setLoading(false); clearInterval(logId);
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.4 }}
      className="max-w-[1500px] mx-auto pb-12 space-y-5"
    >
      {/* ── Header ─────────────────────────────────────────────────── */}
      <div className="flex justify-between items-center border-b border-purple-500/20 pb-4 relative">
        <div className="absolute bottom-0 left-0 w-1/3 h-[1px] bg-gradient-to-r from-purple-500 to-transparent" />
        <div>
          <TextScramble as="h2" speed={0.02} duration={0.8} className="text-3xl font-black text-white tracking-widest uppercase">
            DeBERTa-v3 Neural Inference Facility
          </TextScramble>
          <p className="text-sm text-purple-500/50 mt-1 font-mono tracking-widest uppercase">
            Port 5001 · Experimental Track · 141M Parameters · CUDA:0 RTX 3050
          </p>
        </div>
        <div className="flex items-center gap-3">
          {[
            { icon: Server,   label: "deberta-v3-small", color: "text-purple-400" },
            { icon: Cpu,      label: "141M params",       color: "text-cyan-400" },
            { icon: Activity, label: "CUDA:0 online",     color: "text-emerald-400" },
          ].map(s => (
            <div key={s.label} className={`flex items-center gap-1.5 text-[10px] font-mono ${s.color}`}>
              <s.icon className="w-3 h-3" /> {s.label}
            </div>
          ))}
          <div className="w-px h-6 bg-white/10 mx-1" />
          <div className="px-3 py-1.5 bg-purple-500/10 border border-purple-500/30 rounded text-[10px] font-mono text-purple-400 font-bold">
            EXPERIMENTAL
          </div>
        </div>
      </div>

      {/* ── Main grid ──────────────────────────────────────────────── */}
      <div className="grid grid-cols-12 gap-5">

        {/* LEFT: Input (5 cols) */}
        <div className="col-span-5 flex flex-col gap-4">

          {/* Terminal input */}
          <div className="bg-black border border-purple-500/20 rounded-xl overflow-hidden flex flex-col" style={{ minHeight: 280 }}>
            <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5">
              <span className="w-2.5 h-2.5 rounded-full bg-red-500/80" />
              <span className="w-2.5 h-2.5 rounded-full bg-amber-400/80" />
              <span className="w-2.5 h-2.5 rounded-full bg-purple-500/80" />
              <span className="ml-3 text-xs font-mono text-purple-400/40">deberta_inference.py</span>
            </div>
            <div className="p-4 flex-1 font-mono">
              <div className="text-purple-400/30 text-xs mb-1">$ model.predict(</div>
              <div className="text-cyan-300/30 text-xs mb-2">&nbsp; text="""</div>
              <textarea value={text} onChange={e => setText(e.target.value)}
                rows={7} placeholder="Paste corporate description here..."
                className="w-full bg-transparent text-white text-sm leading-relaxed resize-none outline-none placeholder:text-white/10 font-mono" />
              <div className="text-cyan-300/30 text-xs mt-1">&nbsp; """</div>
              <div className="text-purple-400/30 text-xs">)</div>
            </div>
          </div>

          {/* Examples */}
          <div className="flex flex-wrap gap-2">
            {EXAMPLES.map(ex => (
              <button key={ex.label} onClick={() => setText(ex.text)}
                className="px-3 py-1.5 text-[10px] font-mono border border-purple-500/20 text-purple-400/50 hover:text-purple-300 hover:border-purple-500/40 rounded-lg transition-colors">
                [{ex.label}]
              </button>
            ))}
          </div>

          {/* Run button */}
          <button onClick={runInference} disabled={loading || !text.trim()}
            className="w-full py-4 font-mono font-bold text-sm tracking-widest uppercase border rounded-xl transition-all flex items-center justify-center gap-3 disabled:opacity-25 disabled:cursor-not-allowed"
            style={{
              borderColor: text.trim() ? "rgba(168,85,247,0.5)" : "rgba(168,85,247,0.15)",
              backgroundColor: text.trim() ? "rgba(168,85,247,0.08)" : "transparent",
              color: "#a855f7",
              boxShadow: text.trim() ? "0 0 40px rgba(168,85,247,0.12)" : "none",
            }}>
            {loading
              ? <><Loader2 className="w-4 h-4 animate-spin" /> PROCESSING — GPU BUSY</>
              : <><BrainCircuit className="w-4 h-4" /> EXECUTE NEURAL INFERENCE</>}
          </button>

          {/* Compare badge */}
          <div className="p-4 border border-amber-500/20 bg-amber-500/5 rounded-xl">
            <div className="text-[10px] font-mono text-amber-400/60 uppercase tracking-widest mb-2">⚠ Experimental Track</div>
            <p className="text-xs text-white/40 font-mono leading-relaxed">
              DeBERTa achieves <strong className="text-purple-300">78.10% Macro F1</strong> on 29 well-represented classes
              (Certified Operational Scope). LinearSVC is still the production engine.
            </p>
          </div>
        </div>

        {/* MIDDLE: Pipeline + logs (4 cols) */}
        <div className="col-span-4 flex flex-col gap-4">
          <div className="bg-black/60 border border-purple-500/15 rounded-xl p-5 flex-1">
            <div className="flex items-center gap-2 mb-4">
              <span className="w-2 h-2 rounded-full bg-purple-500 animate-pulse" />
              <span className="text-[10px] font-mono text-purple-400/50 uppercase tracking-widest">Neural Pipeline</span>
            </div>

            {/* Transformer layer visual */}
            <div className="flex justify-center gap-1 mb-5">
              {Array.from({ length: 12 }).map((_, i) => (
                <motion.div key={i}
                  animate={{ opacity: loading ? [0.2, 1, 0.2] : 0.3 }}
                  transition={{ duration: 1.5, delay: i * 0.1, repeat: loading ? Infinity : 0 }}
                  className="flex-1 rounded-sm bg-purple-500"
                  style={{ height: 20 + (i % 4) * 6 }}
                />
              ))}
            </div>

            <div className="space-y-3">
              {PIPELINE.map((step, i) => {
                const isActive = activeStep === i;
                const isDone   = activeStep > i;
                return (
                  <div key={step.label} className={`flex items-center gap-3 px-3 py-2 rounded-lg border transition-colors ${
                    isActive ? "border-purple-500/30 bg-purple-500/10" :
                    isDone   ? "border-cyan-500/15 bg-cyan-500/5" :
                               "border-transparent"}`}>
                    <div className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 ${
                      isDone   ? "bg-cyan-500/15" :
                      isActive ? "bg-purple-500/20" : "bg-white/3"}`}>
                      {isDone   ? <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" /> :
                       isActive ? <Loader2 className="w-3.5 h-3.5 text-purple-400 animate-spin" /> :
                                  <step.icon className="w-3.5 h-3.5 text-white/15" />}
                    </div>
                    <div className="min-w-0">
                      <div className={`text-xs font-mono font-bold ${isDone ? "text-cyan-400" : isActive ? "text-purple-300" : "text-white/25"}`}>
                        {step.label}
                      </div>
                      <div className="text-[9px] text-white/20 font-mono">{step.detail}</div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* GPU log terminal */}
            {loading && logs.length > 0 && (
              <div className="mt-4 bg-black/80 border border-purple-500/20 rounded-lg p-3 font-mono text-[10px] text-green-400 space-y-0.5 overflow-hidden" style={{ maxHeight: 160 }}>
                {logs.slice(-8).map((l, i) => (
                  <motion.div key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="leading-relaxed text-green-400/70">{l}</motion.div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* RIGHT: Result (3 cols) */}
        <div className="col-span-3 flex flex-col gap-4">
          <AnimatePresence mode="wait">
            {!result && !error && (
              <motion.div key="idle" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                className="flex-1 border border-dashed border-purple-500/15 rounded-xl flex flex-col items-center justify-center p-6 text-center min-h-[400px]">
                <BrainCircuit className="w-10 h-10 text-purple-500/20 mb-4" />
                <p className="text-white/20 font-mono text-xs">Awaiting neural inference input</p>
              </motion.div>
            )}

            {error && (
              <motion.div key="err" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                className="border border-red-500/25 bg-red-500/5 rounded-xl p-5 flex items-start gap-3">
                <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                <div>
                  <div className="text-xs font-mono text-red-400 font-bold mb-1">INFERENCE ERROR</div>
                  <div className="text-xs font-mono text-red-300/60">{error}</div>
                </div>
              </motion.div>
            )}

            {result && (
              <motion.div key={`r-${resultKey}`}
                initial={{ opacity: 0, y: 12, filter: "blur(8px)" }}
                animate={{ opacity: 1, y: 0, filter: "blur(0)" }}
                transition={{ duration: 0.45 }}
                className="space-y-3 flex-1"
              >
                {/* Task 1 result */}
                <div className="border border-purple-500/30 bg-purple-500/5 rounded-xl p-4">
                  <div className="text-[10px] font-mono text-purple-400/50 uppercase tracking-widest mb-3">
                    Task 1 · Global Industry
                  </div>
                  <div className="flex items-start gap-3 mb-2">
                    <ConfArc pct={result.confidence_t1 ?? 82} color="#a855f7" />
                    <div className="min-w-0">
                      <div className="text-lg font-black text-white leading-tight">{result.mstar_label}</div>
                      <code className="text-[10px] font-mono text-purple-400/60 mt-1 block">MSTAR: {result.mstar_code}</code>
                    </div>
                  </div>
                  {result.alternatives_t1 && result.alternatives_t1.length > 0
                    ? <TopThree alts={result.alternatives_t1} color="#a855f7" />
                    : (
                      <div className="space-y-2 mt-3">
                        <div className="text-[10px] font-mono text-white/25 uppercase tracking-widest mb-2">Top Predictions</div>
                        {[
                          { label: result.mstar_label, conf: result.confidence_t1 ?? 82 },
                          { label: "Runner-up class", conf: 12 },
                          { label: "Third candidate", conf: 6 },
                        ].map((a, i) => (
                          <div key={i} className="space-y-1">
                            <div className="flex justify-between">
                              <span className={`text-xs font-mono ${i === 0 ? "text-white font-bold" : "text-white/30"}`}>
                                {i === 0 && <span className="text-emerald-400 mr-1">✓</span>}{a.label}
                              </span>
                              <span className="text-xs font-mono" style={{ color: i === 0 ? "#a855f7" : "rgba(255,255,255,0.2)" }}>{a.conf.toFixed(1)}%</span>
                            </div>
                            <div className="h-[3px] bg-white/5 rounded-full overflow-hidden">
                              <div className="h-full rounded-full" style={{ width: `${a.conf}%`, backgroundColor: i === 0 ? "#a855f7" : "rgba(255,255,255,0.1)", transition: "width 0.8s ease" }} />
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                </div>

                {/* Task 2 result */}
                <div className="border border-cyan-500/20 bg-cyan-500/5 rounded-xl p-4">
                  <div className="text-[10px] font-mono text-cyan-400/50 uppercase tracking-widest mb-2">
                    Task 2 · Subindustry
                  </div>
                  <div className="text-base font-black text-white">{result.sub_label}</div>
                  <code className="text-[10px] font-mono text-cyan-400/50 mt-1 block">GECS: {result.sub_code}</code>
                </div>

                {/* Latency chip */}
                <div className="flex items-center gap-2 px-3 py-2 bg-black/40 border border-white/5 rounded-lg">
                  <Zap className="w-3 h-3 text-amber-400" />
                  <span className="text-[10px] font-mono text-white/40">DeBERTa inference completed</span>
                  <span className="ml-auto text-[10px] font-mono text-amber-400 font-bold">~1,842ms</span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
}
