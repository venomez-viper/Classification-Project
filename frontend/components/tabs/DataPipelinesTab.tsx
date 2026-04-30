"use client";
import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Database, Filter, Layers, Zap, ArrowRight, CheckCircle2, AlertTriangle, Package } from "lucide-react";
import { TextScramble } from "@/components/ui/text-scramble";

// ─── Animated flow connector ───────────────────────────────────────────────────
function FlowArrow({ color = "#ef4444" }: { color?: string }) {
  return (
    <div className="flex justify-center py-2 relative">
      <div className="w-px h-10 bg-gradient-to-b from-transparent to-white/10" />
      <motion.div
        animate={{ y: [0, 4, 0] }} transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
        className="absolute bottom-0"
      >
        <ArrowRight className="w-4 h-4 rotate-90" style={{ color }} />
      </motion.div>
    </div>
  );
}

// ─── Stat pill ────────────────────────────────────────────────────────────────
function Stat({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="flex flex-col items-center bg-black/60 border border-white/5 rounded-xl px-5 py-3 text-center">
      <span className="text-xl font-black font-mono" style={{ color }}>{value}</span>
      <span className="text-[10px] text-white/30 font-mono mt-1 uppercase tracking-wider">{label}</span>
    </div>
  );
}

// ─── Pipeline stage card ──────────────────────────────────────────────────────
function PipelineStage({
  phase, title, icon: Icon, accentColor, children, stats, delay = 0
}: {
  phase: string; title: string; icon: React.ElementType;
  accentColor: string; children: React.ReactNode;
  stats?: { label: string; value: string; color: string }[];
  delay?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5, delay }}
      className="relative rounded-2xl border overflow-hidden"
      style={{ borderColor: `${accentColor}25`, background: `linear-gradient(135deg, #060606 60%, ${accentColor}08)` }}
    >
      {/* Glow blob */}
      <div className="absolute -right-20 -top-20 w-60 h-60 rounded-full blur-[80px] pointer-events-none opacity-30"
        style={{ backgroundColor: accentColor }} />

      <div className="relative z-10 p-6">
        <div className="flex items-start gap-5">
          {/* Icon */}
          <div className="w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0 border"
            style={{ backgroundColor: `${accentColor}15`, borderColor: `${accentColor}40`, boxShadow: `0 0 20px ${accentColor}20` }}>
            <Icon className="w-7 h-7" style={{ color: accentColor }} />
          </div>

          <div className="flex-1 min-w-0">
            <div className="text-[10px] font-mono uppercase tracking-[0.2em] mb-1 font-bold" style={{ color: accentColor }}>
              {phase}
            </div>
            <h3 className="text-xl font-black text-white tracking-tight mb-2">{title}</h3>
            <div className="text-sm text-white/50 leading-relaxed">{children}</div>
          </div>
        </div>

        {stats && (
          <div className="grid grid-cols-4 gap-3 mt-5">
            {stats.map(s => <Stat key={s.label} {...s} />)}
          </div>
        )}
      </div>

      {/* Bottom accent line */}
      <div className="h-px w-full" style={{ background: `linear-gradient(90deg, ${accentColor}50, transparent)` }} />
    </motion.div>
  );
}

// ─── Sparse matrix visual ─────────────────────────────────────────────────────
function SparseMatrixViz() {
  const rows = 8; const cols = 20;
  const [filled, setFilled] = useState(false);
  useEffect(() => { const t = setTimeout(() => setFilled(true), 200); return () => clearTimeout(t); }, []);
  return (
    <div className="grid gap-1" style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }}>
      {Array.from({ length: rows * cols }).map((_, i) => {
        const isFilled = Math.random() < 0.04;
        return (
          <div key={i}
            className="rounded-sm transition-all duration-700"
            style={{
              height: 8,
              backgroundColor: isFilled ? "#ef4444" : "rgba(255,255,255,0.04)",
              boxShadow: isFilled ? "0 0 4px #ef4444" : "none",
              transitionDelay: filled ? `${Math.random() * 800}ms` : "0ms",
            }}
          />
        );
      })}
    </div>
  );
}

export default function DataPipelinesTab() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.4 }}
      className="max-w-[1200px] mx-auto pb-12 space-y-0"
    >
      {/* Header */}
      <div className="flex justify-between items-end border-b border-red-500/20 pb-4 mb-8 relative">
        <div className="absolute bottom-0 left-0 w-1/3 h-[1px] bg-gradient-to-r from-red-500 to-transparent" />
        <div>
          <TextScramble as="h2" speed={0.02} duration={0.8} className="text-3xl font-black text-white tracking-widest uppercase">
            Data Architecture & Pipeline
          </TextScramble>
          <p className="text-sm text-red-500/50 mt-1 font-mono tracking-widest uppercase">
            Ingestion → Stratification → Vectorization → Sparse Matrix
          </p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-xs font-mono text-emerald-400">
          <CheckCircle2 className="w-3.5 h-3.5" /> 53,585 records processed
        </div>
      </div>

      {/* ── Stage 1 ──────────────────────────────────────────────── */}
      <PipelineStage phase="Phase 01 · Raw Ingestion" title="Morningstar Financial Data" icon={Database} accentColor="#3b82f6" delay={0.05}
        stats={[
          { label: "Total Records", value: "53,585", color: "#3b82f6" },
          { label: "Industries", value: "145", color: "#60a5fa" },
          { label: "Subindustries", value: "407", color: "#93c5fd" },
          { label: "Avg Text Len", value: "639 chars", color: "#bfdbfe" },
        ]}
      >
        Ingested <strong className="text-white">53,585</strong> raw corporate financial descriptions from Morningstar's GECS taxonomy.
        Each record contains a <code className="text-blue-400 bg-blue-500/10 px-1 rounded">LongProfile</code> + segment fields
        mapped to 8-digit Morningstar codes for Task 1 and 10-digit GECS codes for Task 2.
      </PipelineStage>

      <FlowArrow color="#3b82f6" />

      {/* ── Stage 2 ──────────────────────────────────────────────── */}
      <PipelineStage phase="Phase 02 · Preprocessing" title="Cleaning, Labels & Stratified Split" icon={Filter} accentColor="#f59e0b" delay={0.1}
        stats={[
          { label: "T1 Train", value: "42,868", color: "#f59e0b" },
          { label: "T1 Test", value: "10,717", color: "#fbbf24" },
          { label: "T2 Train", value: "~17,609", color: "#fcd34d" },
          { label: "Split Ratio", value: "80 / 20", color: "#fde68a" },
        ]}
      >
        Dropped all NaN descriptions. Converted GECS codes to integer class labels.
        Filtered classes with <strong className="text-amber-400">&lt;5 samples</strong> to prevent stratification errors during train/test splitting.
        Applied <code className="text-amber-400 bg-amber-500/10 px-1 rounded">train_test_split(stratify=y)</code> preserving the natural long-tail distribution across both tasks.
      </PipelineStage>

      <FlowArrow color="#f59e0b" />

      {/* ── Stage 3 ──────────────────────────────────────────────── */}
      <PipelineStage phase="Phase 03 · Vectorization" title="TF-IDF Sparse Feature Engineering" icon={Layers} accentColor="#ef4444" delay={0.15}>
        <div className="space-y-3">
          <p>
            Transformed text into mathematical vectors using <code className="text-red-400 bg-red-500/10 px-1 rounded">TfidfVectorizer(sublinear_tf=True, ngram_range=(1,2), max_features=50000)</code>.
            Sublinear TF dampening prevents high-frequency terms from dominating the signal.
          </p>

          {/* Code block */}
          <div className="bg-black/80 border border-red-500/20 rounded-xl p-4 font-mono text-xs">
            <div className="text-green-400">vectorizer = TfidfVectorizer(</div>
            <div className="pl-4 text-amber-300">sublinear_tf=<span className="text-blue-400">True</span>,    <span className="text-white/30"># log(1+tf) dampen</span></div>
            <div className="pl-4 text-amber-300">ngram_range=(<span className="text-purple-400">1</span>, <span className="text-purple-400">2</span>),   <span className="text-white/30"># unigrams + bigrams</span></div>
            <div className="pl-4 text-amber-300">max_features=<span className="text-purple-400">50_000</span>  <span className="text-white/30"># T1 feature cap</span></div>
            <div className="text-green-400">)</div>
            <div className="mt-2 text-white/40">X_train = vectorizer.fit_transform(texts)  <span className="text-white/20"># → scipy.sparse CSR</span></div>
          </div>

          {/* Sparse matrix visualization */}
          <div className="bg-black/60 border border-red-500/10 rounded-xl p-4">
            <div className="text-[10px] font-mono text-white/30 uppercase tracking-widest mb-3">Sparse CSR Matrix Visualization — 4% density</div>
            <SparseMatrixViz />
            <div className="flex justify-between mt-3 text-[10px] font-mono text-white/20">
              <span>■ Non-zero TF-IDF features</span>
              <span>53,585 × 50,000 · ~98% sparse · ~40MB RAM vs ~20GB dense</span>
            </div>
          </div>
        </div>
      </PipelineStage>

      <FlowArrow color="#ef4444" />

      {/* ── Stage 4: Output ───────────────────────────────────────── */}
      <PipelineStage phase="Phase 04 · Model Training" title="LinearSVC with class_weight='balanced'" icon={Zap} accentColor="#10b981" delay={0.2}
        stats={[
          { label: "T1 Features", value: "50,000", color: "#10b981" },
          { label: "T2 Features", value: "10,000", color: "#34d399" },
          { label: "T1 Classes", value: "145", color: "#6ee7b7" },
          { label: "T2 Classes", value: "407", color: "#a7f3d0" },
        ]}
      >
        The sparse CSR matrices feed directly into <code className="text-emerald-400 bg-emerald-500/10 px-1 rounded">LinearSVC(class_weight='balanced', dual=False)</code>.
        The <strong className="text-emerald-400">critical breakthrough</strong>: balanced weighting forced the loss function to penalize misclassified minority classes — boosting Macro F1 from <strong className="text-red-400">43%</strong> → <strong className="text-emerald-400">86.82%</strong>.
      </PipelineStage>
    </motion.div>
  );
}
