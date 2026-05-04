"use client";
import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";

const STEPS = [
  {
    step: "01",
    title: "Raw Text Input",
    desc: "LongProfile + SegmentName + SegmentDescription concatenated into a single rich text string per company segment.",
    code: 'df["Combined"] = df["LongProfile"] + " " + df["SegmentName"] + " " + df["SegmentDescription"]',
    color: "violet",
  },
  {
    step: "02",
    title: "TF-IDF Vectorization",
    desc: "60,000 sublinear log-scaled features extracted via bigram TF-IDF. Sparse CSR matrix — no dense conversion, no memory explosion.",
    code: 'TfidfVectorizer(max_features=60000, sublinear_tf=True, ngram_range=(1,2))',
    color: "blue",
  },
  {
    step: "03",
    title: "L1 — Sector Classifier",
    desc: "LinearSVC trained on 11 broad sectors. Routes each input to its economic sector before any fine-grained prediction.",
    code: 'LinearSVC(C=1.0, dual=False, class_weight="balanced")  # 11 classes',
    color: "cyan",
  },
  {
    step: "04",
    title: "L2 & L3 — Group → MSTAR Cascade",
    desc: "L2 narrows to an industry group within the predicted sector. L3 selects the final Morningstar GECS code from that group's candidates only.",
    code: 'cascade_predict(text, assets)  # sector → group → mstar_code',
    color: "emerald",
  },
  {
    step: "05",
    title: "L4 — Sub-Industry (Task 2)",
    desc: "Each MSTAR code has 1–13 sub-industry candidates. A final LinearSVC chooses among them, reaching 55.41% Macro F1 across 428 classes.",
    code: 'cascade_predict_t2(text, assets)  # mstar → sub_code (428 classes)',
    color: "amber",
  },
];

const colorBorder: Record<string, string> = {
  violet: "border-red-500/30",
  blue: "border-blue-500/30",
  cyan: "border-cyan-500/30",
  emerald: "border-emerald-500/30",
  amber: "border-amber-500/30",
};
const colorText: Record<string, string> = {
  violet: "text-red-400",
  blue: "text-blue-400",
  cyan: "text-cyan-400",
  emerald: "text-emerald-400",
  amber: "text-amber-400",
};

export default function ModelDevelopment() {
  return (
    <section id="model" className="py-32 px-6 section-glow">
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <p className="text-red-400 text-sm font-semibold uppercase tracking-widest mb-3">Model Architecture</p>
          <h2 className="text-4xl sm:text-5xl font-bold text-white mb-5">
            The Classification Pipeline
          </h2>
          <p className="text-white/50 text-lg max-w-2xl mx-auto">
            A 4-level cascade reads the Morningstar taxonomy hierarchy instead of flattening it —
            88.90% Macro F1 on 145 industries, 55.41% on 428 sub-industries. No GPU required.
          </p>
        </motion.div>

        <div className="space-y-4">
          {STEPS.map((step, i) => (
            <motion.div
              key={step.step}
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className={`rounded-2xl border ${colorBorder[step.color]} bg-white/3 p-6 flex flex-col md:flex-row md:items-center gap-5`}
            >
              <span className={`text-3xl font-black font-mono ${colorText[step.color]} opacity-40 flex-shrink-0 w-10`}>
                {step.step}
              </span>
              <div className="flex-1">
                <h3 className={`text-lg font-bold mb-1 ${colorText[step.color]}`}>{step.title}</h3>
                <p className="text-white/50 text-sm mb-3">{step.desc}</p>
                <code className="text-xs font-mono bg-black/40 text-white/60 px-3 py-2 rounded-lg block">{step.code}</code>
              </div>
              {i < STEPS.length - 1 && (
                <ArrowRight className="hidden md:block w-5 h-5 text-white/20 flex-shrink-0" />
              )}
            </motion.div>
          ))}
        </div>

        {/* Two model note */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mt-10 grid md:grid-cols-2 gap-6"
        >
          <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-6">
            <p className="text-red-300 font-bold mb-2">Task 1 — Industry Cascade · 88.90% Macro F1</p>
            <p className="text-white/50 text-sm">3-level cascade (Sector → Group → MSTAR). 60,000 TF-IDF features. Trained on 53,587 segments. Predicts 1 of 145 Morningstar GECS codes. Outperforms DeBERTa by +24.90 pp on CPU.</p>
          </div>
          <div className="rounded-xl border border-blue-500/20 bg-blue-500/5 p-6">
            <p className="text-blue-300 font-bold mb-2">Task 2 — Sub-Industry Cascade · 55.41% Macro F1</p>
            <p className="text-white/50 text-sm">4-level cascade adds an L4 step: routes through T1 MSTAR prediction, then picks among 1–13 sub-industry candidates per code. 428 classes. Oracle ceiling: 62.26%.</p>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
