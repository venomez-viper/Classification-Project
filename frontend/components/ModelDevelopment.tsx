"use client";
import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";

const STEPS = [
  {
    step: "01",
    title: "Raw Text Input",
    desc: "Company and segment descriptions are combined into a single classification payload.",
    code: 'payload = {"company_text": company_text, "segment_text": segment_text}',
    color: "violet",
  },
  {
    step: "02",
    title: "Feature Extraction",
    desc: "The deployable baseline uses sparse text features and cached model artifacts rather than retraining at inference time.",
    code: "vectorizer.transform([text])",
    color: "blue",
  },
  {
    step: "03",
    title: "Task 1 Industry",
    desc: "The locked result is the calibrated ModernBERT-large ensemble at 75.0% Macro F1 / 91.4% top-3 accuracy over 145 GECS industry classes.",
    code: "task1 = predict_industry(company_text)",
    color: "cyan",
  },
  {
    step: "04",
    title: "Task 2 Constraint",
    desc: "The Task 1 industry code restricts Task 2 to valid GECS child sub-industries before the L4 classifier ranks candidates.",
    code: "valid_children = task1_to_task2_map[task1.code]",
    color: "emerald",
  },
  {
    step: "05",
    title: "Structured Response",
    desc: "The API returns Task 1, Task 2, alternatives, prediction ID, model version, and latency trace for analyst review.",
    code: "return { task1, task2, alternatives, trace }",
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
            A 4-level GECS-Sage flow reads the Morningstar hierarchy instead of flattening it. The locked result is a calibrated ModernBERT-large ensemble at 75.0% Macro F1 (91.4% top-3) plus 55.44% constrained Task 2.
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

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mt-10 grid md:grid-cols-2 gap-6"
        >
          <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-6">
            <p className="text-red-300 font-bold mb-2">Task 1 Industry · 75.0% Macro F1 · 91.4% Top-3</p>
            <p className="text-white/50 text-sm">Calibrated greedy ensemble of two ModernBERT-large variants. Trained on company-disjoint splits. Cross-validated — the test-tuned upper bound (77.51%) is disclosed but not reported as the headline.</p>
          </div>
          <div className="rounded-xl border border-blue-500/20 bg-blue-500/5 p-6">
            <p className="text-blue-300 font-bold mb-2">Task 2 Sub-Industry Cascade · 55.44% Macro F1</p>
            <p className="text-white/50 text-sm">The L4 classifier ranks valid sub-industry candidates under the Task 1 parent. It covers 428 classes and preserves the GECS hierarchy during inference.</p>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
