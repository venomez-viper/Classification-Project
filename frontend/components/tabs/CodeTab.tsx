"use client";
import React, { useState } from "react";
import { motion } from "framer-motion";
import { Code, Copy, Check, Terminal, Package, Cpu, Database, Zap } from "lucide-react";
import { TextScramble } from "@/components/ui/text-scramble";

// ─── Syntax token types ────────────────────────────────────────────────────────
type Token = { text: string; color: string };
type Line = Token[];

// ─── Simple hand-crafted syntax highlighter ───────────────────────────────────
const C = {
  keyword:   "#ff79c6",  // pink
  func:      "#50fa7b",  // green
  string:    "#f1fa8c",  // yellow
  comment:   "#6272a4",  // grey-blue
  number:    "#bd93f9",  // purple
  class:     "#8be9fd",  // cyan
  operator:  "#ff5555",  // red
  param:     "#ffb86c",  // orange
  plain:     "#f8f8f2",  // white
  decorator: "#50fa7b",  // green
  import:    "#ff79c6",  // pink
};

// Helper to build a line from token tuples
const L = (...tokens: [string, string][]): Line => tokens.map(([text, color]) => ({ text, color }));

// ─── Code Snippets ─────────────────────────────────────────────────────────────
const SNIPPETS = [
  {
    id: "pipeline",
    icon: Zap,
    label: "SVM Inference Pipeline",
    file: "hf_space/app.py",
    lang: "Python",
    color: "#ef4444",
    description: "The production inference endpoint deployed on Hugging Face Space. FastAPI + Gradio serve the 4-level cascade SVM over /api/predict — no GPU required, ~5ms latency.",
    lines: [
      L(["# ", C.comment], ["Deployed: akash-ag-gecs-classifier-space.hf.space", C.comment]),
      L(["app = FastAPI()", C.plain]),
      L(["", C.plain]),
      L(["async def ", C.keyword], ["_json_predict", C.func], ["(request: ", C.class], ["Request", C.class], ["):", C.plain]),
      L(["    payload = ", C.plain], ["await ", C.keyword], ["request.", C.plain], ["json", C.func], ["()", C.plain]),
      L(["    text = str(payload.", C.plain], ["get", C.func], ["(", C.plain], ["'text'", C.string], [") or payload.", C.plain], ["get", C.func], ["(", C.plain], ["'company_text'", C.string], [", ", C.plain], ["''", C.string], [")).strip()", C.plain]),
      L(["", C.plain]),
      L(["    ", C.plain], ["# 4-level cascade: Sector → Group → Industry → Sub-industry", C.comment]),
      L(["    X       = T1_ASSETS[", C.plain], ["'vectorizer'", C.string], ["].", C.plain], ["transform", C.func], ["([text])", C.plain]),
      L(["    sector  = T1_ASSETS[", C.plain], ["'l1'", C.string], ["].", C.plain], ["predict", C.func], ["(X)[", C.plain], ["0", C.number], ["]", C.plain]),
      L(["    group   = T1_ASSETS[", C.plain], ["'l2'", C.string], ["][sector].", C.plain], ["predict", C.func], ["(X)[", C.plain], ["0", C.number], ["]", C.plain]),
      L(["    mstar   = T1_ASSETS[", C.plain], ["'l3'", C.string], ["][group].", C.plain], ["predict", C.func], ["(X)[", C.plain], ["0", C.number], ["]", C.plain]),
      L(["", C.plain]),
      L(["    ", C.plain], ["# Task 2: constrained to Task 1 parent (428 sub-industry codes)", C.comment]),
      L(["    X_seg = T2_EXTRA[", C.plain], ["'seg_vec'", C.string], ["].", C.plain], ["transform", C.func], ["([text])", C.plain]),
      L(["    sub   = T2_EXTRA[", C.plain], ["'l4'", C.string], ["][mstar].", C.plain], ["predict", C.func], ["(X_seg)[", C.plain], ["0", C.number], ["]", C.plain]),
      L(["", C.plain]),
      L(["    return ", C.keyword], ["JSONResponse", C.class], ["({", C.plain]),
      L(["        ", C.plain], ["'mstar_code'", C.string], [":    mstar,", C.plain]),
      L(["        ", C.plain], ["'mstar_label'", C.string], [":   _get_mstar_label(mstar),", C.plain]),
      L(["        ", C.plain], ["'confidence_t1'", C.string], [": t1_conf,", C.plain]),
      L(["        ", C.plain], ["'sub_code'", C.string], [":     sub,", C.plain]),
      L(["        ", C.plain], ["'sub_label'", C.string], [":    _get_sub_label(sub),", C.plain]),
      L(["    ", C.plain], ["})", C.plain]),
      L(["", C.plain]),
      L(["app.", C.plain], ["add_api_route", C.func], ["(", C.plain], ["'/api/predict'", C.string], [", _json_predict, methods=[", C.plain], ["'POST'", C.string], ["])", C.plain]),
      L(["app = gr.", C.plain], ["mount_gradio_app", C.func], ["(app, demo, path=", C.plain], ["'/'", C.string], [")", C.plain]),
    ],
  },
  {
    id: "breezeml",
    icon: Package,
    label: "breezeml Core",
    file: "breezeml/classifiers.py",
    lang: "Python",
    color: "#a855f7",
    description: "The heart of the breezeml library - a parallel, sparse-aware classifier comparison engine published to PyPI.",
    lines: [
      L(["from ", C.keyword], ["sklearn.svm ", C.class], ["import ", C.keyword], ["LinearSVC", C.class]),
      L(["from ", C.keyword], ["scipy.sparse ", C.class], ["import ", C.keyword], ["issparse", C.func]),
      L(["from ", C.keyword], ["joblib ", C.class], ["import ", C.keyword], ["Parallel, delayed", C.func]),
      L(["", C.plain]),
      L(["def ", C.keyword], ["compare", C.func], ["(X_train, y_train, X_test, y_test,", C.plain]),
      L(["        sparse=", C.plain], ["True", C.keyword], [", class_weight=", C.plain], ["'balanced'", C.string], ["):", C.plain]),
      L(["    ", C.plain], ["\"\"\"Benchmark classifiers in parallel with sparse support.\"\"\"", C.comment]),
      L(["", C.plain]),
      L(["    if ", C.keyword], ["sparse ", C.plain], ["and not ", C.keyword], ["issparse", C.func], ["(X_train):", C.plain]),
      L(["        ", C.plain], ["raise ", C.keyword], ["ValueError", C.class], ["(", C.plain], ["'Input must be scipy.sparse CSR'", C.string], [")", C.plain]),
      L(["", C.plain]),
      L(["    def ", C.keyword], ["_fit_score", C.func], ["(name, clf):", C.plain]),
      L(["        clf.", C.plain], ["fit", C.func], ["(X_train, y_train)", C.plain]),
      L(["        score = clf.", C.plain], ["score", C.func], ["(X_test, y_test)", C.plain]),
      L(["        return ", C.keyword], ["{", C.plain], ["'name'", C.string], [": name, ", C.plain], ["'score'", C.string], [": score}", C.plain]),
      L(["", C.plain]),
      L(["    classifiers = [", C.plain]),
      L(["        (", C.plain], ["'LinearSVC'", C.string], [", LinearSVC(class_weight=class_weight)),", C.plain]),
      L(["    ]", C.plain]),
      L(["", C.plain]),
      L(["    results = Parallel(n_jobs=", C.plain], ["-1", C.number], [")(", C.plain]),
      L(["        delayed(_fit_score)(n, c) for n, c in classifiers", C.plain]),
      L(["    )", C.plain]),
      L(["    return ", C.keyword], ["sorted", C.func], ["(results, key=", C.plain], ["lambda", C.keyword], [" x: x[", C.plain], ["'score'", C.string], ["], reverse=", C.keyword], ["True", C.keyword], [")", C.plain]),
    ],
  },
  {
    id: "tfidf",
    icon: Database,
    label: "TF-IDF + Sparse Training",
    file: "train_model.py",
    lang: "Python",
    color: "#f59e0b",
    description: "The full training pipeline - TF-IDF vectorization into sparse CSR matrices followed by LinearSVC training with balanced class weights.",
    lines: [
      L(["from ", C.keyword], ["sklearn.feature_extraction.text ", C.class], ["import ", C.keyword], ["TfidfVectorizer", C.class]),
      L(["from ", C.keyword], ["sklearn.svm ", C.class], ["import ", C.keyword], ["LinearSVC", C.class]),
      L(["from ", C.keyword], ["sklearn.model_selection ", C.class], ["import ", C.keyword], ["train_test_split", C.func]),
      L(["", C.plain]),
      L(["# ", C.comment], ["Vectorize with 60,000 bigram features", C.comment]),
      L(["vectorizer = TfidfVectorizer(", C.plain]),
      L(["    sublinear_tf=", C.plain], ["True", C.keyword], [",", C.plain]),
      L(["    ngram_range=(", C.plain], ["1", C.number], [", ", C.plain], ["2", C.number], ["),", C.plain]),
      L(["    max_features=", C.plain], ["60000", C.number]),
      L([")", C.plain]),
      L(["", C.plain]),
      L(["X_train_sparse = vectorizer.", C.plain], ["fit_transform", C.func], ["(X_train)", C.plain]),
      L(["X_test_sparse  = vectorizer.", C.plain], ["transform", C.func], ["(X_test)   ", C.plain], ["# scipy CSR matrix", C.comment]),
      L(["", C.plain]),
      L(["# ", C.comment], ["The breakthrough: class_weight='balanced'", C.comment]),
      L(["# ", C.comment], ["Classical ceiling: 68.42% → Ensemble: 75.0%", C.comment]),
      L(["clf = LinearSVC(", C.plain]),
      L(["    class_weight=", C.plain], ["'balanced'", C.string], [",", C.plain]),
      L(["    dual=", C.plain], ["False", C.keyword],  [",      ", C.plain], ["# faster for n_samples > n_features", C.comment]),
      L(["    max_iter=", C.plain], ["2000", C.number]),
      L([")", C.plain]),
      L(["", C.plain]),
      L(["clf.", C.plain], ["fit", C.func], ["(X_train_sparse, y_train)", C.plain]),
      L(["print", C.func], ["(f'Task 1 F1: {", C.plain], ["f1_score", C.func], ["(y_test, clf.", C.plain], ["predict", C.func], ["(X_test_sparse)):.4f}')", C.plain]),
    ],
  },
  {
    id: "disjoint",
    icon: Database,
    label: "Company-Disjoint Split",
    file: "scripts/build_disjoint_split.py",
    lang: "Python",
    color: "#10b981",
    description: "The split that made the project honest. Row-level random splits memorized 97.2% of test rows. This script groups by CompanyId and assigns entire companies to train or test - no company appears on both sides.",
    lines: [
      L(["import ", C.keyword], ["pandas ", C.class], ["as ", C.keyword], ["pd", C.class]),
      L(["from ", C.keyword], ["sklearn.model_selection ", C.class], ["import ", C.keyword], ["GroupShuffleSplit", C.func]),
      L(["", C.plain]),
      L(["# ", C.comment], ["Load joined file with CompanyId recovered from LongProfile prefix", C.comment]),
      L(["df = pd.", C.plain], ["read_csv", C.func], ["(", C.plain], ["'task1_train_with_companyid.csv'", C.string], [")", C.plain]),
      L(["", C.plain]),
      L(["# ", C.comment], ["GroupShuffleSplit: entire companies go to one split only", C.comment]),
      L(["gss = GroupShuffleSplit(n_splits=", C.plain], ["1", C.number], [", test_size=", C.plain], ["0.2", C.number], [", random_state=", C.plain], ["42", C.number], [")", C.plain]),
      L(["train_idx, test_idx = next(gss.", C.plain], ["split", C.func], ["(df, groups=df[", C.plain], ["'CompanyId'", C.string], ["]))", C.plain]),
      L(["", C.plain]),
      L(["train = df.", C.plain], ["iloc", C.plain], ["[train_idx]", C.plain]),
      L(["test  = df.", C.plain], ["iloc", C.plain], ["[test_idx]", C.plain]),
      L(["", C.plain]),
      L(["# ", C.comment], ["Verify zero overlap", C.comment]),
      L(["overlap = ", C.plain], ["set", C.func], ["(train[", C.plain], ["'CompanyId'", C.string], ["])  &  ", C.plain], ["set", C.func], ["(test[", C.plain], ["'CompanyId'", C.string], ["])", C.plain]),
      L(["assert ", C.keyword], ["len", C.func], ["(overlap) == ", C.plain], ["0", C.number], [",  ", C.plain], ["'LEAK DETECTED'", C.string]),
      L(["", C.plain]),
      L(["print", C.func], ["(f'Train: {len(train)} rows · {train[", C.plain], ["\"CompanyId\"", C.string], ["].nunique()} companies')", C.plain]),
      L(["print", C.func], ["(f'Test:  {len(test)} rows  · {test[", C.plain], ["\"CompanyId\"", C.string], ["].nunique()} companies')", C.plain]),
      L(["# ", C.comment], ["→ Train: 42,868 rows · 5,341 companies", C.comment]),
      L(["# ", C.comment], ["→ Test:  10,717 rows · 1,336 companies  (zero overlap)", C.comment]),
    ],
  },
  {
    id: "modernbert",
    icon: Cpu,
    label: "ModernBERT Cascade",
    file: "colab/train_modernbert_large.py",
    lang: "Python",
    color: "#a855f7",
    description: "The ModernBERT-large fine-tuning loop that reached 70.29% Macro F1 on epoch 3 - trained on Colab A100 in ~40 min/epoch vs 8-15h on CPU. CLS embeddings from this checkpoint fed the greedy ensemble.",
    lines: [
      L(["from ", C.keyword], ["transformers ", C.class], ["import ", C.keyword], ["AutoModelForSequenceClassification, Trainer", C.class]),
      L(["from ", C.keyword], ["transformers ", C.class], ["import ", C.keyword], ["TrainingArguments", C.class]),
      L(["", C.plain]),
      L(["model = AutoModelForSequenceClassification.", C.plain], ["from_pretrained", C.func], ["(", C.plain]),
      L(["    ", C.plain], ["'answerdotai/ModernBERT-large'", C.string], [",", C.plain]),
      L(["    num_labels=", C.plain], ["145", C.number], [",    ", C.plain], ["# 145 GECS industry classes", C.comment]),
      L([")", C.plain]),
      L(["", C.plain]),
      L(["args = TrainingArguments(", C.plain]),
      L(["    output_dir=", C.plain], ["'./modernbert_large_gecs'", C.string], [",", C.plain]),
      L(["    num_train_epochs=", C.plain], ["5", C.number], [",", C.plain]),
      L(["    per_device_train_batch_size=", C.plain], ["16", C.number], [",", C.plain]),
      L(["    learning_rate=", C.plain], ["2e-5", C.number], [",", C.plain]),
      L(["    warmup_ratio=", C.plain], ["0.1", C.number], [",", C.plain]),
      L(["    weight_decay=", C.plain], ["0.01", C.number], [",", C.plain]),
      L(["    evaluation_strategy=", C.plain], ["'epoch'", C.string], [",", C.plain]),
      L(["    metric_for_best_model=", C.plain], ["'eval_macro_f1'", C.string], [",", C.plain]),
      L(["    fp16=", C.plain], ["True", C.keyword], [",   ", C.plain], ["# A100 native fp16 - 20× speedup over CPU", C.comment]),
      L([")", C.plain]),
      L(["", C.plain]),
      L(["trainer = Trainer(model=model, args=args,", C.plain]),
      L(["    train_dataset=train_ds, eval_dataset=test_ds,", C.plain]),
      L(["    compute_metrics=compute_macro_f1,", C.plain]),
      L([")", C.plain]),
      L(["trainer.", C.plain], ["train", C.func], ["()", C.plain]),
      L(["# ", C.comment], ["Epoch 3 → 70.29% Macro F1 on company-disjoint test set", C.comment]),
    ],
  },
  {
    id: "augment",
    icon: Cpu,
    label: "LLM Data Augmentation",
    file: "data_augmentation/expand_descriptions.py",
    lang: "Python",
    color: "#22d3ee",
    description: "Uses a free, offline Flan-T5 model to expand short company descriptions into rich 3-sentence financial profiles for data augmentation.",
    lines: [
      L(["from ", C.keyword], ["transformers ", C.class], ["import ", C.keyword], ["pipeline", C.func]),
      L(["import ", C.keyword], ["torch", C.class]),
      L(["", C.plain]),
      L(["# ", C.comment], ["Runs 100% offline on CUDA GPU (no API cost)", C.comment]),
      L(["device = ", C.plain], ["0 ", C.number], ["if ", C.keyword], ["torch.cuda.", C.class], ["is_available", C.func], ["() else ", C.plain], ["-1", C.number]),
      L(["generator = pipeline(", C.plain]),
      L(["    ", C.plain], ["'text2text-generation'", C.string], [",", C.plain]),
      L(["    model=", C.plain], ["'google/flan-t5-base'", C.string], [",", C.plain]),
      L(["    device=device", C.plain]),
      L([")", C.plain]),
      L(["", C.plain]),
      L(["def ", C.keyword], ["expand_description", C.func], ["(text, industry):", C.plain]),
      L(["    prompt = (", C.plain]),
      L(["        f", C.plain], ["\"Expand this company description into a 3-sentence \"", C.string]),
      L(["        f", C.plain], ["\"financial profile for '{industry}': {text}\"", C.string]),
      L(["    )", C.plain]),
      L(["", C.plain]),
      L(["    out = generator(prompt,", C.plain]),
      L(["        max_length=", C.plain], ["150", C.number], [", min_length=", C.plain], ["40", C.number], [",", C.plain]),
      L(["        do_sample=", C.plain], ["True", C.keyword], [", temperature=", C.plain], ["0.7", C.number]),
      L(["    )", C.plain]),
      L(["    return ", C.keyword], ["out[", C.plain], ["0", C.number], ["][", C.plain], ["'generated_text'", C.string], ["].", C.plain], ["strip", C.func], ["()", C.plain]),
    ],
  },
];

// ─── Code Block Renderer ──────────────────────────────────────────────────────
function CodeBlock({ lines, onCopy, copied }: { lines: Line[]; onCopy: () => void; copied: boolean }) {
  return (
    <div className="relative group">
      <button
        onClick={onCopy}
        className="absolute top-3 right-3 z-10 flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-xs font-mono text-white/40 hover:text-white hover:bg-white/10 transition-all opacity-0 group-hover:opacity-100"
      >
        {copied ? <><Check className="w-3 h-3 text-emerald-400" /> Copied!</> : <><Copy className="w-3 h-3" /> Copy</>}
      </button>

      <div className="bg-[#0d1117] border border-white/10 rounded-xl overflow-hidden">
        {/* Mac-style titlebar */}
        <div className="flex items-center gap-1.5 px-4 py-3 border-b border-white/10 bg-black/40">
          <span className="w-3 h-3 rounded-full bg-red-500/80" />
          <span className="w-3 h-3 rounded-full bg-amber-400/80" />
          <span className="w-3 h-3 rounded-full bg-emerald-500/80" />
        </div>

        <div className="overflow-x-auto p-5">
          <table className="border-collapse w-full">
            <tbody>
              {lines.map((line, i) => (
                <tr key={i} className="hover:bg-white/[0.02] transition-colors">
                  <td className="pr-6 text-right select-none text-white/20 font-mono text-xs align-top pt-0.5 w-8 flex-shrink-0">
                    {i + 1}
                  </td>
                  <td className="font-mono text-sm leading-6 whitespace-pre">
                    {line.length === 1 && line[0].text === "" ? (
                      <span>&nbsp;</span>
                    ) : (
                      line.map((tok, j) => (
                        <span key={j} style={{ color: tok.color }}>{tok.text}</span>
                      ))
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ─── Main Tab ─────────────────────────────────────────────────────────────────
export default function CodeTab() {
  const [active, setActive] = useState("pipeline");
  const [copied, setCopied] = useState(false);

  const current = SNIPPETS.find((s) => s.id === active)!;

  function handleCopy() {
    const text = current.lines
      .map((line) => line.map((t) => t.text).join(""))
      .join("\n");
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.4 }}
      className="max-w-[1400px] mx-auto pb-12 space-y-6"
    >
      {/* Header */}
      <div className="flex justify-between items-end border-b border-red-500/20 pb-4 relative">
        <div className="absolute bottom-0 left-0 w-1/3 h-[1px] bg-gradient-to-r from-red-500 to-transparent" />
        <div>
          <TextScramble as="h2" speed={0.02} duration={0.8} className="text-3xl font-black text-white tracking-widest uppercase">
            Code Showcase
          </TextScramble>
          <p className="text-sm text-red-500/50 mt-1 font-mono tracking-widest uppercase">
            Real production code written by TAVSS · Python · Flask · breezeml
          </p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-white/5 border border-white/10 rounded-lg font-mono text-xs text-white/40">
          <Terminal className="w-3 h-3" />
          {current.lines.length} lines · {current.lang}
        </div>
      </div>

      {/* File tabs */}
      <div className="flex gap-2 flex-wrap">
        {SNIPPETS.map((s) => {
          const Icon = s.icon;
          const isActive = s.id === active;
          return (
            <button
              key={s.id}
              onClick={() => { setActive(s.id); setCopied(false); }}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg border text-sm font-mono transition-all ${
                isActive
                  ? "text-white font-bold"
                  : "text-white/30 border-white/5 bg-black/20 hover:text-white/60 hover:bg-white/5"
              }`}
              style={isActive ? { borderColor: `${s.color}40`, backgroundColor: `${s.color}10`, color: s.color, boxShadow: `0 0 20px ${s.color}20` } : {}}
            >
              <Icon className="w-4 h-4" />
              {s.file}
            </button>
          );
        })}
      </div>

      {/* Description card */}
      <motion.div
        key={current.id + "_desc"}
        initial={{ opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-start gap-4 p-4 rounded-xl border bg-black/30"
        style={{ borderColor: `${current.color}20` }}
      >
        <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
          style={{ backgroundColor: `${current.color}15`, border: `1px solid ${current.color}30` }}>
          <Code className="w-4 h-4" style={{ color: current.color }} />
        </div>
        <div>
          <div className="text-xs font-mono uppercase tracking-widest mb-1" style={{ color: current.color }}>
            {current.label}
          </div>
          <p className="text-sm text-white/50 leading-relaxed">{current.description}</p>
        </div>
      </motion.div>

      {/* Code block */}
      <motion.div
        key={current.id}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <CodeBlock lines={current.lines} onCopy={handleCopy} copied={copied} />
      </motion.div>
    </motion.div>
  );
}
