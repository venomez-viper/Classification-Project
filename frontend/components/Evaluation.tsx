"use client";
import { motion } from "framer-motion";
import { useInView } from "framer-motion";
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
            cx="60" cy="60" r={r}
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
  { pct: 88.90, color: "#dc2626", label: "Task 1 Macro F1", sublabel: "145-class cascade SVM" },
  { pct: 55.41, color: "#60a5fa", label: "Task 2 Macro F1", sublabel: "428-class sub-industry" },
  { pct: 75,    color: "#34d399", label: "Rubric Threshold", sublabel: "Minimum Required F1" },
];

const INSIGHTS = [
  {
    title: "Why Macro F1 > Accuracy?",
    body: "With 145 classes of wildly varying sizes, raw accuracy gets inflated by majority classes. Macro F1 averages the F1 score equally across every class, so the model gets penalized for ignoring rare industries. This is the correct metric for imbalanced NLP classification.",
  },
  {
    title: "The Cascade Architecture Breakthrough",
    body: "Instead of one flat 145-class SVM, we built a 3-level cascade: L1 predicts the sector (11 classes), L2 narrows to the group, L3 picks the final MSTAR code. Each level trains only on its relevant slice, boosting Task 1 Macro F1 from 59.7% flat → 88.90% cascade.",
  },
  {
    title: "Task 2: 4-Level Sub-Industry Cascade",
    body: "Task 2 extends the cascade with an L4 level that maps each MSTAR code to 1–13 sub-industry candidates. LinearSVC selects among those candidates, reaching 55.41% Macro F1 on 428 classes — nearly matching the oracle ceiling of 62.26%.",
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
            Task 1 cascade SVM exceeds the rubric threshold of 75% by{" "}
            <span className="text-emerald-400 font-bold">+13.90 percentage points</span>.{" "}
            Task 2 sub-industry cascade reaches <span className="text-blue-400 font-bold">55.41%</span> across 428 classes.
          </p>
        </motion.div>

        {/* Progress Rings */}
        <div className="flex flex-wrap justify-center gap-12 mb-20">
          {METRICS.map((m) => (
            <Ring key={m.label} {...m} />
          ))}
        </div>

        {/* Success Criteria Banner */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="rounded-2xl border border-emerald-500/30 bg-emerald-500/5 p-6 text-center mb-12"
        >
          <div className="text-emerald-400 text-4xl font-black font-mono mb-2">✓ PASSING</div>
          <p className="text-white/60">Task 1 Macro F1 <strong className="text-white">88.90%</strong> exceeds the required threshold of <strong className="text-white">75%</strong> — beats fine-tuned DeBERTa by <strong className="text-emerald-400">+24.90 pp</strong></p>
        </motion.div>

        {/* Insights */}
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
