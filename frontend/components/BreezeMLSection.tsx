"use client";
import { motion } from "framer-motion";
import { Package, Zap, Shield, GitMerge, Cpu, TrendingUp } from "lucide-react";
import { TextScramble } from "@/components/ui/text-scramble";

const VERSIONS = [
  {
    version: "v0.2.1",
    date: "Apr 22, 2026",
    title: "Parallel Benchmarking",
    icon: Cpu,
    color: "blue",
    changes: [
      "Integrated joblib.Parallel(n_jobs=-1) into classifiers.compare()",
      "All 12 baseline models now train concurrently across all CPU cores",
      "Turns O(N) sequential benchmark into O(1) parallel execution",
      "Massive speedup for model leaderboards on large datasets",
    ],
  },
  {
    version: "v0.2.2 → v0.2.3",
    date: "Apr 22, 2026",
    title: "Sparse Matrix Support",
    icon: Zap,
    color: "violet",
    changes: [
      "All classifier functions now accept X= and y= keyword arguments",
      "Bypasses the memory-heavy ColumnTransformer pipeline entirely",
      "scipy.sparse matrices passed natively without toarray() conversion",
      "Prevents out-of-memory crashes from dense TF-IDF expansion",
    ],
  },
  {
    version: "v0.2.3",
    date: "Apr 22, 2026",
    title: "Primal SVM Formulation",
    icon: Shield,
    color: "red",
    critical: true,
    changes: [
      "Hand-patched all LinearSVC references with dual=False",
      "Fixes the O(n_samples²) dual formulation deadlock",
      "Training time dropped from 20+ minutes to under 2 seconds",
      "Mathematically correct for n_samples > n_features (text datasets)",
    ],
  },
  {
    version: "v0.2.4",
    date: "Apr 22, 2026",
    title: "Polymorphic Save() Fix",
    icon: GitMerge,
    color: "green",
    changes: [
      "Patched breezeml.save() to check hasattr(model, 'save')",
      "Falls back to joblib.dump() for raw scikit-learn Pipelines",
      "EasyModel objects still use their native .save() method",
      "Prevents fatal AttributeError on Pipeline objects",
    ],
  },
  {
    version: "v0.2.5",
    date: "Apr 22, 2026",
    title: "Balanced Class Weights",
    icon: TrendingUp,
    color: "gold",
    critical: true,
    changes: [
      "Added class_weight='balanced' to all LinearSVC initializations",
      "Forces penalty multiplication for misclassified rare classes",
      "Exposed why class weighting matters for rare GECS labels",
      "Eliminates need for SMOTE oversampling entirely",
    ],
  },
  {
    version: "Level 2",
    date: "May 2026",
    title: "Hierarchical Cascade Classifier",
    icon: TrendingUp,
    color: "green",
    critical: true,
    changes: [
      "Extended breezeml with a 3-level cascade: Sector → Industry Group → Morningstar Code",
      "Each level uses a dedicated LinearSVC trained only on classes within that branch",
      "Proved the hierarchy-first cascade approach used as the HF Space production backend",
      "Established the Task 1 to Task 2 routing pattern used by GECS-Sage",
      "Runs fast enough for a local analyst-in-the-loop demo",
    ],
  },
];

const colorMap: Record<string, string> = {
  blue: "border-blue-500/30 bg-blue-500/5 text-blue-300",
  violet: "border-red-500/30 bg-red-500/5 text-red-300",
  red: "border-red-500/30 bg-red-500/5 text-red-300",
  green: "border-emerald-500/30 bg-emerald-500/5 text-emerald-300",
  gold: "border-amber-500/30 bg-amber-500/5 text-amber-300",
};

const dotMap: Record<string, string> = {
  blue: "bg-blue-400",
  violet: "bg-red-400",
  red: "bg-red-400",
  green: "bg-emerald-400",
  gold: "bg-amber-400",
};

export default function BreezeMLSection() {
  return (
    <section id="breezeml" className="py-32 px-6 section-glow">
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-6"
        >
          <TextScramble as="p" speed={0.02} duration={0.7} className="text-red-400 text-sm font-semibold uppercase tracking-widest mb-3">
            Library Engineering
          </TextScramble>
          <h2 className="text-4xl sm:text-5xl font-bold text-white mb-5">
            breezeml: Our Own PyPI Library
          </h2>
          <p className="text-white/50 text-lg max-w-3xl mx-auto">
            Rather than bypassing library limitations, we dogfooded our own{" "}
            <a
              href="https://pypi.org/project/breezeml/"
              target="_blank"
              className="text-red-400 hover:text-red-300 underline underline-offset-2"
            >
              breezeml
            </a>{" "}
            framework, patching it live across 5 versions to support the sparse NLP
            pipeline, fix mathematical deadlocks, and reach production-grade accuracy.
          </p>
        </motion.div>

        {/* What is breezeml */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mb-14 rounded-2xl border border-red-500/20 bg-red-500/5 p-8"
        >
          <div className="flex items-center gap-3 mb-4">
            <Package className="w-6 h-6 text-red-400" />
            <TextScramble as="code" speed={0.025} duration={0.8} characterSet="abcdefghijklmnopqrstuvwxyz0123456789 ." className="text-red-300 font-mono text-lg font-bold">
              pip install breezeml
            </TextScramble>
            <span className="px-2 py-0.5 rounded-full bg-red-500/20 text-red-300 text-xs font-mono">v0.2.5</span>
          </div>
          <p className="text-white/60 leading-relaxed">
            <strong className="text-white">breezeml</strong> is a production-grade, beginner-friendly
            machine learning framework built on top of scikit-learn, authored by{" "}
            <strong className="text-red-300">Akash Anipakalu Giridhar</strong>. It provides a clean,
            zero-boilerplate API for classification, regression, clustering, and model benchmarking.
            During this Capstone, we identified critical performance limitations, shipped 5 public
            versions to PyPI, and then extended breezeml into Level 2: a hierarchy-first
            cascade architecture that became the foundation for the audited GECS-Sage demo.
          </p>
          <div className="mt-4 font-mono text-sm bg-black/40 rounded-lg p-4 text-white/70">
            <span className="text-red-400">from</span> breezeml <span className="text-red-400">import</span> classifiers<br />
            model, report = classifiers.<span className="text-white">linear_svm</span>(<span className="text-amber-300">X</span>=X_vec, <span className="text-amber-300">y</span>=y)
          </div>
        </motion.div>

        {/* Version Timeline */}
        <div className="relative">
          {/* Timeline line */}
          <div className="absolute left-6 top-0 bottom-0 w-px bg-gradient-to-b from-red-500/50 via-blue-500/30 to-transparent hidden md:block" />

          <div className="space-y-6">
            {VERSIONS.map((v, i) => (
              <motion.div
                key={v.version}
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="md:pl-16 relative"
              >
                {/* Timeline dot */}
                <div className={`absolute left-4 top-5 w-4 h-4 rounded-full border-2 border-slate-950 ${dotMap[v.color]} hidden md:block`} />

                <div className={`rounded-2xl border p-6 ${colorMap[v.color]} ${v.critical ? "ring-1 ring-amber-500/20" : ""}`}>
                  {v.critical && (
                    <span className="inline-block mb-3 px-2 py-0.5 rounded text-xs font-bold bg-amber-500/20 text-amber-300 uppercase tracking-wider">
                      Critical Fix
                    </span>
                  )}
                  <div className="flex flex-wrap items-center gap-3 mb-3">
                    <v.icon className="w-5 h-5 opacity-80" />
                    <code className="font-mono font-bold text-base">{v.version}</code>
                    <span className="text-white/30 text-sm">·</span>
                    <TextScramble as="span" speed={0.02} duration={0.5} className="font-semibold text-white">
                      {v.title}
                    </TextScramble>
                    <span className="text-white/30 text-xs ml-auto">{v.date}</span>
                  </div>
                  <ul className="space-y-1.5">
                    {v.changes.map((c) => (
                      <li key={c} className="flex items-start gap-2 text-sm text-white/60">
                        <span className="mt-1.5 w-1 h-1 rounded-full bg-current flex-shrink-0 opacity-60" />
                        {c}
                      </li>
                    ))}
                  </ul>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
