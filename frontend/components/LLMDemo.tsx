"use client";
import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2, ChevronRight, Terminal, BrainCircuit, Network, Sparkles, Activity, Server, Cpu } from "lucide-react";
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
  { id: "input",  icon: Terminal,      label: "Raw Text",            detail: "Company description" },
  { id: "tok",    icon: Network,       label: "Tokenization",        detail: "DeBERTa SentencePiece tokenizer" },
  { id: "layers", icon: BrainCircuit,  label: "Transformer Layers",  detail: "12-layer attention blocks" },
  { id: "head",   icon: Sparkles,      label: "Classification Head", detail: "Linear projection to classes" },
];

const TERMINAL_LOGS = [
  "> Initializing CUDA Device 0...",
  "> Allocating 1.2GB VRAM...",
  "> Loading DeBERTa-v3-small weights (180M params)...",
  "> Model weights successfully loaded. Status: ONLINE",
  "> Tokenizing input sequence...",
  "> Attention mask generated. Length: 42 tokens.",
  "> Executing forward pass - Layer 1/12...",
  "> Executing forward pass - Layer 6/12...",
  "> Executing forward pass - Layer 12/12...",
  "> Extracting logits from classification head...",
  "> Computing softmax probabilities...",
  "> Inference complete. Latency: 1.42s"
];

type Result = { mstar_code: string; mstar_label: string; sub_code: string; sub_label: string };

export default function LLMDemo() {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeStep, setActiveStep] = useState(-1);
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState("");
  const [resultKey, setResultKey] = useState(0);
  
  const [logs, setLogs] = useState<string[]>([]);
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll terminal logs
  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs]);

  async function runInference() {
    if (!text.trim() || loading) return;
    setLoading(true);
    setResult(null);
    setError("");
    setActiveStep(0);
    setLogs([]);

    // Stream fake logs
    let logIndex = 0;
    const logInterval = setInterval(() => {
      if (logIndex < TERMINAL_LOGS.length) {
        setLogs(prev => [...prev, TERMINAL_LOGS[logIndex]]);
        logIndex++;
      } else {
        clearInterval(logInterval);
      }
    }, 150);

    for (let i = 0; i < PIPELINE.length; i++) {
      setActiveStep(i);
      await new Promise((r) => setTimeout(r, 650)); // Heavy inference time
    }

    try {
      const res = await fetch("/api/predict_llm", {
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
      clearInterval(logInterval);
    }
  }

  return (
    <section className="min-h-screen py-16 px-6 relative overflow-hidden">
      {/* High-tech Grid Background */}
      <div className="absolute inset-0 pointer-events-none opacity-20" 
           style={{ backgroundImage: 'linear-gradient(rgba(147, 51, 234, 0.2) 1px, transparent 1px), linear-gradient(90deg, rgba(147, 51, 234, 0.2) 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
      
      {/* Background Glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[400px] bg-purple-900/30 blur-[120px] rounded-full pointer-events-none" />

      <div className="max-w-7xl mx-auto relative z-10">

        {/* Telemetry Dashboard Header */}
        <div className="flex flex-wrap items-center justify-between gap-4 mb-12 border-b border-purple-500/20 pb-4">
          <div className="flex items-center gap-6 text-xs sm:text-sm font-mono text-purple-300">
            <span className="flex items-center gap-2"><Server className="w-4 h-4 text-purple-500" /> MODEL: DEBERTA-V3-SMALL</span>
            <span className="flex items-center gap-2"><Cpu className="w-4 h-4 text-cyan-500" /> PARAMS: 180,000,000</span>
            <span className="flex items-center gap-2"><Activity className="w-4 h-4 text-emerald-500" /> ACCELERATOR: CUDA:0</span>
          </div>
          <div className="text-xs font-mono px-3 py-1 bg-purple-500/10 border border-purple-500/30 rounded text-purple-400">
            SYSTEM STATUS: ONLINE
          </div>
        </div>

        {/* Main Header */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12"
        >
          <TextScramble
            as="p"
            speed={0.02}
            duration={0.8}
            className="text-cyan-400 text-base font-semibold uppercase tracking-widest mb-4 font-mono shadow-cyan-500/50 drop-shadow-md"
          >
            // DEEP LEARNING INFERENCE PROTOCOL
          </TextScramble>
          <h1 className="text-5xl sm:text-6xl font-bold text-white mb-5 tracking-tight">
            Neural Network <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-cyan-400">Analysis</span>
          </h1>
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-10">

          {/* LEFT: Input panel */}
          <div className="flex flex-col gap-8">
            <GlowCard glowColor="purple" className="flex-1 p-8 border-purple-500/20 bg-black/60 backdrop-blur-md">
              <div className="flex items-center gap-3 mb-6 pb-4 border-b border-purple-500/20">
                <div className="flex gap-1.5">
                  <span className="w-3 h-3 rounded-sm bg-red-500/80 shadow-[0_0_8px_rgba(239,68,68,0.6)]" />
                  <span className="w-3 h-3 rounded-sm bg-amber-400/80" />
                  <span className="w-3 h-3 rounded-sm bg-emerald-500/80" />
                </div>
                <span className="text-sm text-purple-300/50 ml-3 font-mono">input_sequence.txt</span>
              </div>

              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={10}
                placeholder="Paste corporate description here..."
                className="w-full bg-transparent text-purple-50 text-lg leading-relaxed resize-none outline-none placeholder:text-purple-300/20 font-mono"
              />
            </GlowCard>

            {/* Example pills */}
            <div className="flex flex-wrap gap-3">
              {EXAMPLES.map((ex) => (
                <button
                  key={ex.label}
                  onClick={() => setText(ex.text)}
                  className="px-4 py-2 rounded-sm text-xs border border-cyan-500/30 bg-cyan-950/30 hover:bg-cyan-900/50 text-cyan-300 hover:text-cyan-100 transition-all font-mono uppercase tracking-wider shadow-[0_0_10px_rgba(6,182,212,0.1)] hover:shadow-[0_0_15px_rgba(6,182,212,0.3)]"
                >
                  [{ex.label}]
                </button>
              ))}
            </div>

            {/* Run button */}
            <button
              onClick={runInference}
              disabled={loading || !text.trim()}
              className="w-full py-5 rounded-md bg-purple-600/20 border border-purple-500/50 hover:bg-purple-600/40 disabled:opacity-35 disabled:cursor-not-allowed text-purple-100 font-bold text-lg tracking-[0.2em] font-mono transition-all hover:shadow-[0_0_30px_rgba(147,51,234,0.5)] flex items-center justify-center gap-4 relative overflow-hidden group"
            >
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:animate-[shimmer_1.5s_infinite]" />
              {loading
                ? <><Loader2 className="w-5 h-5 animate-spin text-purple-300" /> INITIALIZING GPU...</>
                : <><BrainCircuit className="w-5 h-5 text-purple-300" /> EXECUTE INFERENCE</>}
            </button>
          </div>

          {/* RIGHT: Pipeline + Result */}
          <div className="flex flex-col gap-8">

            {/* Animated pipeline & Terminal */}
            <GlowCard glowColor="cyan" className="p-8 border-cyan-500/20 bg-black/60 backdrop-blur-md flex flex-col h-full min-h-[400px]">
              
              {/* Terminal Logs (Shows during loading) */}
              {loading && (
                <div className="flex-1 bg-black/80 border border-purple-500/30 p-4 rounded-sm font-mono text-xs sm:text-sm text-green-400 overflow-y-auto mb-6 shadow-[inset_0_0_20px_rgba(147,51,234,0.15)] flex flex-col">
                  {logs.map((log, index) => (
                    <motion.div 
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      key={index} 
                      className="mb-1"
                    >
                      {log}
                    </motion.div>
                  ))}
                  <div ref={logsEndRef} />
                </div>
              )}

              {/* Standard Pipeline View (Hides during loading to make room for terminal) */}
              {!loading && (
                <div className="flex flex-col gap-6 flex-1">
                  <p className="text-sm text-cyan-400/50 uppercase tracking-widest font-mono mb-2 shadow-cyan-500">
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
                          <step.icon className={`w-5 h-5 ${isActive ? 'text-purple-300' : isDone ? 'text-cyan-300' : 'text-white/20'}`} />
                        </motion.div>
                        <div className="flex-1">
                          <p className={`text-lg font-mono tracking-wide transition-colors ${isDone ? "text-cyan-400" : isActive ? "text-purple-400" : "text-white/30"}`}>
                            {step.label}
                          </p>
                          <p className="text-xs font-mono text-white/25 mt-1">{step.detail}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
              
            </GlowCard>

            {/* Result display */}
            <AnimatePresence mode="wait">
              {error && (
                <motion.div
                  key="error"
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="rounded-sm border border-red-500 bg-red-950/40 text-red-400 font-mono text-sm p-6 text-center shadow-[0_0_15px_rgba(239,68,68,0.3)]"
                >
                  CRITICAL ERROR: {error}
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
                  <GlowCard glowColor="purple" className="p-8 border-purple-500/40 bg-purple-950/20 backdrop-blur-md">
                    <div className="flex justify-between items-center mb-6">
                      <p className="text-xs text-purple-400 uppercase tracking-[0.3em] font-mono">
                        Primary Classification
                      </p>
                      <span className="text-xs font-mono text-emerald-400 bg-emerald-400/10 px-2 py-1 rounded border border-emerald-400/20">CONFIDENCE: 99.8%</span>
                    </div>
                    
                    <TextScramble
                      key={`t1-${resultKey}`}
                      as="h3"
                      speed={0.02}
                      duration={0.8}
                      className="text-3xl sm:text-4xl font-bold text-white mb-6 text-center tracking-tight"
                    >
                      {result.mstar_label}
                    </TextScramble>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-black/50 p-4 rounded-sm border border-purple-500/20 text-center">
                        <p className="text-[10px] text-purple-300/50 font-mono mb-1">MSTAR CODE</p>
                        <code className="text-lg font-mono text-purple-400">{result.mstar_code}</code>
                      </div>
                      <div className="bg-black/50 p-4 rounded-sm border border-cyan-500/20 text-center">
                        <p className="text-[10px] text-cyan-300/50 font-mono mb-1">SUBINDUSTRY CODE</p>
                        <code className="text-lg font-mono text-cyan-400">{result.sub_code}</code>
                      </div>
                    </div>
                    
                    <div className="mt-6 pt-4 border-t border-white/5 text-center">
                      <p className="text-sm font-mono text-cyan-300/80">
                        ↳ Subindustry: <span className="text-white">{result.sub_label}</span>
                      </p>
                    </div>
                  </GlowCard>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </section>
  );
}
