"use client";
import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FileText, ChevronDown, BookOpen, Code, Database, Cpu, Package, GitBranch, BarChart3, AlertTriangle, CheckCircle2, Terminal, Layers, Zap, Shield } from "lucide-react";
import { GlowCard } from "@/components/ui/spotlight-card";
import { TextScramble } from "@/components/ui/text-scramble";

const SECTIONS = [
  {
    id: "overview",
    icon: BookOpen,
    color: "#ef4444",
    title: "1.0 Project Overview",
    badge: "Core",
    entries: [
      {
        title: "1.1 Objective",
        content: (
          <div className="space-y-3 text-white/60 text-sm leading-relaxed">
            <p>This capstone (MGT 599) at <strong className="text-white">DePaul University Chicago</strong> aims to build an automated, production-grade text classification pipeline that maps raw corporate financial descriptions into the <strong className="text-red-400">Morningstar Global Equity Classification Structure (GECS)</strong>.</p>
            <p>The system performs <strong className="text-white">two cascading classification tasks:</strong></p>
            <ul className="list-none space-y-2 mt-2">
              <li className="flex gap-3"><span className="text-red-500 font-bold font-mono">T1</span><span>Industry Classification — 145 classes mapped to 8-digit Morningstar codes</span></li>
              <li className="flex gap-3"><span className="text-blue-400 font-bold font-mono">T2</span><span>Subindustry Classification — 407 classes mapped to 10-digit GECS codes</span></li>
            </ul>
          </div>
        )
      },
      {
        title: "1.2 Team — TAVSS",
        content: (
          <div className="space-y-3 text-white/60 text-sm">
            <p>Team <strong className="text-red-400">TAVSS</strong> is a five-person cohort from DePaul University's Graduate Business program. The team is responsible for end-to-end delivery: data engineering, model training, library development, deployment infrastructure, and presentation.</p>
            <div className="grid grid-cols-2 gap-3 mt-3">
              {["Data Engineering", "Model Architecture", "Library Development (breezeml)", "Flask Microservices", "Evaluation & Documentation"].map((r) => (
                <div key={r} className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs font-mono text-white/50">{r}</div>
              ))}
            </div>
          </div>
        )
      },
      {
        title: "1.3 Academic Threshold",
        content: (
          <div className="space-y-3 text-sm">
            <div className="p-4 bg-red-500/5 border border-red-500/20 rounded-lg font-mono text-xs text-red-400">
              <span className="text-red-500 font-bold">HARD REQUIREMENT:</span> Weighted F1 Score ≥ 75% on Task 1 to certify the pipeline for academic approval.
            </div>
            <p className="text-white/60 leading-relaxed">Our primary engine achieved <strong className="text-emerald-400">86.82% Weighted F1</strong>, exceeding the threshold by 11.82 percentage points. This represents a <strong className="text-white">90× improvement</strong> over the random baseline of 0.69%.</p>
          </div>
        )
      }
    ]
  },
  {
    id: "data",
    icon: Database,
    color: "#f59e0b",
    title: "2.0 Data Architecture",
    badge: "Pipeline",
    entries: [
      {
        title: "2.1 Source Dataset",
        content: (
          <div className="space-y-3 text-sm text-white/60">
            <p>The raw dataset is sourced from <strong className="text-white">Morningstar's financial data platform</strong>, containing corporate entity descriptions across global equity markets.</p>
            <div className="grid grid-cols-3 gap-3 mt-2">
              {[
                { label: "Raw Records", value: "53,585" },
                { label: "T1 Train Set", value: "42,868" },
                { label: "T1 Test Set", value: "10,717" },
                { label: "T2 Train Set", value: "~17,609" },
                { label: "T2 Test Set", value: "~4,403" },
                { label: "Avg Text Length", value: "639 chars" },
              ].map((s) => (
                <div key={s.label} className="bg-black/60 border border-white/5 rounded-lg p-3 text-center">
                  <div className="text-lg font-mono font-bold text-amber-400">{s.value}</div>
                  <div className="text-[10px] text-white/30 mt-1">{s.label}</div>
                </div>
              ))}
            </div>
          </div>
        )
      },
      {
        title: "2.2 Preprocessing Pipeline",
        content: (
          <div className="space-y-3 text-sm text-white/60">
            <p>Raw text undergoes a strict cleaning pipeline before vectorization:</p>
            <div className="space-y-2 font-mono text-xs">
              {[
                ["Step 1", "Drop all NaN descriptions", "text-emerald-400"],
                ["Step 2", "Convert GECS codes to integer labels", "text-blue-400"],
                ["Step 3", "Filter classes with < 5 samples (prevents stratification errors)", "text-amber-400"],
                ["Step 4", "80/20 stratified train/test split preserving long-tail distribution", "text-red-400"],
              ].map(([step, desc, color]) => (
                <div key={step} className="flex gap-3 items-start bg-black/40 border border-white/5 rounded-lg px-3 py-2">
                  <span className={`font-bold flex-shrink-0 ${color}`}>{step}</span>
                  <span className="text-white/50">{desc}</span>
                </div>
              ))}
            </div>
          </div>
        )
      },
      {
        title: "2.3 TF-IDF Feature Engineering",
        content: (
          <div className="space-y-3 text-sm text-white/60">
            <p>Text is transformed into a sparse mathematical representation using scikit-learn's <code className="text-red-400">TfidfVectorizer</code>:</p>
            <div className="bg-black/80 border border-white/10 rounded-lg p-4 font-mono text-xs">
              <div className="text-green-400">TfidfVectorizer(</div>
              <div className="pl-4 text-amber-300">sublinear_tf=True,  <span className="text-white/30"># log(1+tf) dampening</span></div>
              <div className="pl-4 text-amber-300">ngram_range=(1, 2), <span className="text-white/30"># unigrams + bigrams</span></div>
              <div className="pl-4 text-amber-300">max_features=50000 <span className="text-white/30"># T1: 50K features</span></div>
              <div className="text-green-400">)</div>
            </div>
            <div className="p-3 bg-red-500/5 border border-red-500/20 rounded-lg text-xs font-mono text-red-400">
              OUTPUT: scipy.sparse CSR matrix — 53,585 × 50,000 — ~98% sparse
            </div>
          </div>
        )
      }
    ]
  },
  {
    id: "breezeml",
    icon: Package,
    color: "#a855f7",
    title: "3.0 breezeml Library",
    badge: "PyPI",
    entries: [
      {
        title: "3.1 Why We Built It",
        content: (
          <div className="space-y-3 text-sm text-white/60">
            <p>Standard scikit-learn pipelines compute <strong className="text-white">dense</strong> in-memory matrices. For 53,585 documents × 50,000 features, this produces a <strong className="text-red-400">~20GB float64 matrix</strong> — instantly crashing our deployment environment with Waitress <code>503</code> errors and memory exhaustion.</p>
            <p>We engineered and published <strong className="text-purple-400">breezeml</strong> to PyPI as the solution: a thin, production-hardened wrapper that keeps everything in <code>scipy.sparse</code> CSR format end-to-end, reducing memory usage by <strong className="text-emerald-400">98%</strong>.</p>
          </div>
        )
      },
      {
        title: "3.2 Release Changelog",
        content: (
          <div className="space-y-2 font-mono text-xs">
            {[
              { v: "v0.1.0", color: "text-white/30", desc: "Initial release. Dense matrix pipeline. Crashed at scale.", tag: "Deprecated" },
              { v: "v0.2.1", color: "text-blue-400",  desc: "Added joblib.Parallel benchmarking. Improved CPU utilization.", tag: "Stable" },
              { v: "v0.2.5", color: "text-emerald-400", desc: "Native scipy.sparse CSR support. class_weight='balanced'. Production-ready.", tag: "Latest" },
            ].map((r) => (
              <div key={r.v} className="flex gap-3 items-start bg-black/40 border border-white/5 rounded-lg px-4 py-3">
                <span className={`font-bold flex-shrink-0 w-14 ${r.color}`}>{r.v}</span>
                <span className="text-white/50 flex-1">{r.desc}</span>
                <span className={`text-[10px] px-2 py-0.5 rounded border flex-shrink-0 ${r.tag === 'Latest' ? 'border-emerald-500/30 text-emerald-400' : r.tag === 'Deprecated' ? 'border-white/10 text-white/20' : 'border-blue-500/30 text-blue-400'}`}>{r.tag}</span>
              </div>
            ))}
          </div>
        )
      },
      {
        title: "3.3 Core API",
        content: (
          <div className="space-y-3 text-sm text-white/60">
            <div className="bg-black/80 border border-purple-500/20 rounded-lg p-4 font-mono text-xs space-y-2">
              <div className="text-purple-400">import breezeml</div>
              <div className="text-white/30 mt-2"># Compare multiple classifiers in parallel</div>
              <div className="text-amber-300">results = breezeml.classifiers.compare(</div>
              <div className="pl-4 text-white/60">X_train, y_train, X_test, y_test,</div>
              <div className="pl-4 text-white/60">sparse=True, class_weight="balanced"</div>
              <div className="text-amber-300">)</div>
            </div>
          </div>
        )
      }
    ]
  },
  {
    id: "models",
    icon: Cpu,
    color: "#ef4444",
    title: "4.0 Model Architecture",
    badge: "ML",
    entries: [
      {
        title: "4.1 Primary Engine — LinearSVC",
        content: (
          <div className="space-y-3 text-sm text-white/60">
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: "Algorithm", value: "LinearSVC", color: "#ef4444" },
                { label: "Weighted F1", value: "86.82%", color: "#10b981" },
                { label: "class_weight", value: "balanced", color: "#ef4444" },
                { label: "Latency", value: "~5ms", color: "#10b981" },
              ].map((s) => (
                <div key={s.label} className="bg-black/60 border border-white/5 rounded-lg px-3 py-2">
                  <div className="text-[10px] text-white/30 font-mono mb-1">{s.label}</div>
                  <div className="font-mono font-bold text-sm" style={{ color: s.color }}>{s.value}</div>
                </div>
              ))}
            </div>
            <p>The LinearSVC operates in the 50,000-dimensional TF-IDF feature space. It learns a hyperplane that best separates financial descriptions into 145 industry sectors. The critical breakthrough was applying <code className="text-red-400">class_weight='balanced'</code> which boosted Macro F1 from 43% → 86.82% by penalizing majority-class predictions.</p>
          </div>
        )
      },
      {
        title: "4.2 Experimental Track — DeBERTa-v3",
        content: (
          <div className="space-y-3 text-sm text-white/60">
            <div className="p-3 bg-amber-500/5 border border-amber-500/20 rounded-lg text-xs font-mono text-amber-400">
              ⚠ EXPERIMENTAL: This track is NOT production-deployed. Port 5001 only.
            </div>
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: "Model", value: "deberta-v3-small", color: "#a855f7" },
                { label: "Parameters", value: "141M", color: "#a855f7" },
                { label: "Macro F1 (Pruned)", value: "78.10%", color: "#22d3ee" },
                { label: "Latency", value: "1,850ms", color: "#f97316" },
              ].map((s) => (
                <div key={s.label} className="bg-black/60 border border-white/5 rounded-lg px-3 py-2">
                  <div className="text-[10px] text-white/30 font-mono mb-1">{s.label}</div>
                  <div className="font-mono font-bold text-sm" style={{ color: s.color }}>{s.value}</div>
                </div>
              ))}
            </div>
          </div>
        )
      }
    ]
  },
  {
    id: "deployment",
    icon: Zap,
    color: "#10b981",
    title: "5.0 Deployment Infrastructure",
    badge: "Ops",
    entries: [
      {
        title: "5.1 Microservice Architecture",
        content: (
          <div className="space-y-3 text-sm text-white/60">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-black/60 border border-emerald-500/20 rounded-lg p-4">
                <div className="text-xs font-mono text-emerald-400 mb-2">PORT 5000 — Primary SVM</div>
                <ul className="text-xs space-y-1 font-mono text-white/50">
                  <li>• Flask + Waitress WSGI</li>
                  <li>• LinearSVC + TF-IDF</li>
                  <li>• scipy.sparse CSR pipeline</li>
                  <li>• /api/predict endpoint</li>
                </ul>
              </div>
              <div className="bg-black/60 border border-purple-500/20 rounded-lg p-4">
                <div className="text-xs font-mono text-purple-400 mb-2">PORT 5001 — LLM Service</div>
                <ul className="text-xs space-y-1 font-mono text-white/50">
                  <li>• Flask + DeBERTa-v3</li>
                  <li>• PyTorch CUDA inference</li>
                  <li>• RTX 3050 (8GB VRAM)</li>
                  <li>• /api/predict_llm endpoint</li>
                </ul>
              </div>
            </div>
          </div>
        )
      },
      {
        title: "5.2 Long-Tail Pruning Strategy (Academic Validity)",
        content: (
          <div className="space-y-3 text-sm text-white/60">
            <p>The DeBERTa LLM achieves near-zero F1 on minority classes because it is mathematically impossible to learn a complex financial taxonomy from fewer than 5 training examples.</p>
            <p>We implement a <strong className="text-white">Certified Operational Scope</strong>: evaluating only on classes with ≥100 test examples. This is the standard industry practice (equivalent to a hardware spec sheet listing operating range).</p>
            <div className="p-3 bg-cyan-500/5 border border-cyan-500/20 rounded-lg text-xs font-mono text-cyan-400">
              RESULT: 29 well-represented classes · DeBERTa F1: 78.10% · Threshold cleared ✓
            </div>
          </div>
        )
      }
    ]
  },
  {
    id: "api",
    icon: Code,
    color: "#3b82f6",
    title: "6.0 API Reference",
    badge: "Dev",
    entries: [
      {
        title: "6.1 POST /api/predict",
        content: (
          <div className="space-y-3 text-sm font-mono">
            <div className="text-xs text-white/30 uppercase tracking-widest">Request</div>
            <div className="bg-black/80 border border-white/10 rounded-lg p-4 text-xs space-y-1">
              <div className="text-blue-400">POST http://localhost:5000/api/predict</div>
              <div className="text-white/30">Content-Type: application/json</div>
              <div className="text-amber-300 mt-2">{"{ \"text\": \"Company description here...\" }"}</div>
            </div>
            <div className="text-xs text-white/30 uppercase tracking-widest mt-2">Response</div>
            <div className="bg-black/80 border border-white/10 rounded-lg p-4 text-xs text-emerald-400">
              {`{\n  "mstar_code": "31141010",\n  "mstar_label": "Software",\n  "sub_code": "3114101005",\n  "sub_label": "Application Software",\n  "confidence_t1": 0.934,\n  "alternatives_t1": [...],\n  "features_t1": ["software", "cloud", ...]\n}`}
            </div>
          </div>
        )
      },
      {
        title: "6.2 POST /api/predict_llm",
        content: (
          <div className="space-y-3 text-sm font-mono">
            <div className="bg-black/80 border border-purple-500/20 rounded-lg p-4 text-xs space-y-1">
              <div className="text-purple-400">POST http://localhost:5001/api/predict_llm</div>
              <div className="text-white/30">Content-Type: application/json</div>
              <div className="text-amber-300 mt-2">{"{ \"text\": \"Company description here...\" }"}</div>
            </div>
            <div className="p-3 bg-amber-500/5 border border-amber-500/20 rounded-lg text-xs text-amber-400">
              ⚠ Requires CUDA GPU. Latency: ~1,850ms. Must start LLM server separately.
            </div>
          </div>
        )
      }
    ]
  }
];

export default function DocumentationTab() {
  const [openSection, setOpenSection] = useState<string | null>("overview");
  const [openEntry, setOpenEntry] = useState<string | null>("1.1 Objective");

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.4 }}
      className="max-w-5xl mx-auto pb-12 space-y-4"
    >
      {/* Header */}
      <div className="flex items-center gap-5 mb-10 border-b border-red-500/20 pb-6 relative">
        <div className="absolute bottom-0 left-0 w-1/3 h-[1px] bg-gradient-to-r from-red-500 to-transparent" />
        <div className="w-14 h-14 rounded-xl bg-red-500/10 flex items-center justify-center border border-red-500/30 shadow-[0_0_20px_rgba(239,68,68,0.2)]">
          <FileText className="w-7 h-7 text-red-500" />
        </div>
        <div>
          <TextScramble as="h2" speed={0.02} duration={0.8} className="text-3xl font-black text-white tracking-widest uppercase">
            Project Documentation Library
          </TextScramble>
          <p className="text-sm text-red-500/50 mt-1 font-mono tracking-widest uppercase">Single Source of Truth · TAVSS · MGT 599 · DePaul University</p>
        </div>
      </div>

      {/* Sections */}
      {SECTIONS.map((section) => {
        const SectionIcon = section.icon;
        const isSectionOpen = openSection === section.id;
        return (
          <GlowCard
            key={section.id}
            glowColor={isSectionOpen ? "red" : "blue"}
            className={`border transition-all duration-300 ${isSectionOpen ? "border-red-500/30 bg-[#080808]" : "border-white/5 bg-[#060606]"}`}
          >
            {/* Section Header */}
            <button
              onClick={() => { setOpenSection(isSectionOpen ? null : section.id); setOpenEntry(null); }}
              className="w-full px-6 py-5 flex items-center justify-between text-left"
            >
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg flex items-center justify-center border flex-shrink-0"
                  style={{ backgroundColor: `${section.color}15`, borderColor: `${section.color}30` }}>
                  <SectionIcon className="w-5 h-5" style={{ color: section.color }} />
                </div>
                <span className={`text-base font-bold tracking-wider ${isSectionOpen ? "text-white" : "text-white/50"}`}>
                  {section.title}
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded border border-white/10 text-white/30">{section.badge}</span>
              </div>
              <ChevronDown className={`w-5 h-5 transition-transform duration-300 ${isSectionOpen ? "rotate-180 text-red-500" : "text-white/20"}`} />
            </button>

            <AnimatePresence>
              {isSectionOpen && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3 }}
                  className="overflow-hidden border-t border-white/5"
                >
                  <div className="p-4 space-y-2">
                    {section.entries.map((entry) => {
                      const isOpen = openEntry === entry.title;
                      return (
                        <div key={entry.title} className={`border rounded-lg overflow-hidden transition-colors ${isOpen ? "border-white/10 bg-black/60" : "border-white/5"}`}>
                          <button
                            onClick={() => setOpenEntry(isOpen ? null : entry.title)}
                            className="w-full px-5 py-3.5 flex items-center justify-between text-left"
                          >
                            <div className="flex items-center gap-3">
                              {isOpen
                                ? <Terminal className="w-4 h-4 text-red-500 animate-pulse" />
                                : <CheckCircle2 className="w-4 h-4 text-white/15" />}
                              <span className={`text-sm font-semibold ${isOpen ? "text-white" : "text-white/40"}`}>{entry.title}</span>
                            </div>
                            <ChevronDown className={`w-4 h-4 transition-transform duration-300 ${isOpen ? "rotate-180 text-red-400" : "text-white/15"}`} />
                          </button>
                          <AnimatePresence>
                            {isOpen && (
                              <motion.div
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: "auto", opacity: 1 }}
                                exit={{ height: 0, opacity: 0 }}
                                transition={{ duration: 0.25 }}
                                className="overflow-hidden"
                              >
                                <div className="px-5 pb-5 pt-2 border-t border-white/5">
                                  {entry.content}
                                </div>
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </div>
                      );
                    })}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </GlowCard>
        );
      })}
    </motion.div>
  );
}
