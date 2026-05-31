"use client";
import { motion, useInView } from "framer-motion";
import { useRef } from "react";

function Ring({ pct, color, label, sublabel }: { pct: number; color: string; label: string; sublabel: string }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true });
  const r = 54;
  const circ = 2 * Math.PI * r;
  const dash = inView ? (pct / 100) * circ : 0;

  return (
    <div ref={ref} className="flex flex-col items-center gap-3">
      <div className="relative w-36 h-36">
        <svg viewBox="0 0 120 120" className="w-full h-full -rotate-90">
          <circle cx="60" cy="60" r={r} fill="none" stroke="white" strokeOpacity={0.06} strokeWidth="8" />
          <motion.circle
            cx="60"
            cy="60"
            r={r}
            fill="none"
            stroke={color}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={circ}
            initial={{ strokeDashoffset: circ }}
            animate={{ strokeDashoffset: circ - dash }}
            transition={{ duration: 1.5, ease: "easeOut", delay: 0.3 }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.span
            className="text-2xl font-black font-mono text-white"
            initial={{ opacity: 0 }}
            animate={inView ? { opacity: 1 } : {}}
            transition={{ delay: 0.5 }}
          >
            {pct}%
          </motion.span>
        </div>
      </div>
      <div className="text-center">
        <div className="text-sm font-bold text-white">{label}</div>
        <div className="text-xs text-white/40 mt-1">{sublabel}</div>
      </div>
    </div>
  );
}

const METRICS = [
  { pct: 75.0,  color: "#dc2626", label: "Task 1 F1", sublabel: "Calibrated ensemble · locked" },
  { pct: 55.44, color: "#60a5fa", label: "Task 2 Macro F1", sublabel: "428-class constrained cascade" },
  { pct: 91.4,  color: "#34d399", label: "Top-3 Accuracy", sublabel: "Company-disjoint test set" },
];

const INSIGHTS = [
  {
    title: "Why Macro F1 > Accuracy?",
    body: "With 145 classes of wildly varying sizes, raw accuracy gets inflated by majority classes. Macro F1 averages every class equally, so the model is penalized for ignoring rare industries.",
  },
  {
    title: "The Audit Became the Breakthrough",
    body: "The system was heavily evaluated and audited. The story centers on catching a 97.2% leakage, rebuilding with company-disjoint splits, and locking 75.0% Macro F1 through a cross-validated calibrated ensemble.",
  },
  {
    title: "Task 2: Constrained Sub-Industry Cascade",
    body: "Task 2 maps each Task 1 industry to its valid sub-industry candidates. The current constrained cascade reaches 55.44% Macro F1 across 428 classes while preserving the parent-child GECS structure.",
  },
];

export default function Evaluation() {
  return (
    <section id="evaluation" className="py-32 px-6 section-glow">
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <p className="text-red-400 text-sm font-semibold uppercase tracking-widest mb-3">Evaluation</p>
          <h2 className="text-4xl sm:text-5xl font-bold text-white mb-5">
            Model Performance Metrics
          </h2>
          <p className="text-white/50 text-lg max-w-2xl mx-auto">
            75.0% Macro F1 locked after catching a 97.2% leakage in our original result, rebuilding with company-disjoint splits, and running 14 model versions. Task 2 reaches{" "}
            <span className="text-blue-400 font-bold">55.44%</span> across 428 constrained classes.
          </p>
        </motion.div>

        <div className="flex flex-wrap justify-center gap-12 mb-20">
          {METRICS.map((m) => (
            <Ring key={m.label} {...m} />
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="rounded-2xl border border-emerald-500/30 bg-emerald-500/5 p-6 text-center mb-12"
        >
          <div className="text-emerald-400 text-4xl font-black font-mono mb-2">AUDITED</div>
          <p className="text-white/60">
            The calibrated ModernBERT-large ensemble achieves <strong className="text-white">75.0%</strong> Macro F1 - cross-validated, fully disclosed, and the real generalization number.
          </p>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-5">
          {INSIGHTS.map((ins, i) => (
            <motion.div
              key={ins.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="rounded-xl border border-white/8 bg-white/3 p-6"
            >
              <h3 className="text-base font-bold text-white mb-3">{ins.title}</h3>
              <p className="text-white/50 text-sm leading-relaxed">{ins.body}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
