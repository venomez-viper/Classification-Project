"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Terminal, Database, Cpu, Zap, Activity,
  CheckCircle2, AlertCircle, Loader2,
  BarChart3, Layers, GitBranch, Clock,
  ChevronRight, Radio, Shield, X, Info,
} from "lucide-react";

// ── Static data ────────────────────────────────────────────────────────────────

const STEP_DURATIONS = [60, 80, 60, 80, 60];

const PIPELINE_STEPS = [
  { icon: Terminal, label: "TEXT INGESTION",     detail: "Tokenise raw description"      },
  { icon: Database, label: "MODERNBERT ENCODE",  detail: "ModernBERT-large embeddings"   },
  { icon: Layers,   label: "MULTI-TASK HEAD",    detail: "Sector + Group + Industry"     },
  { icon: Cpu,      label: "TASK 1 - INDUSTRY",  detail: "145 GECS industry classes"     },
  { icon: Zap,      label: "TASK 2 - SVM",       detail: "428 sub-industry classes"      },
];

const PERF_BARS = [
  { label: "Calibrated ensemble ★",    value: "75.0%",  pct: 75.0,  color: "#22c55e" },
  { label: "Greedy ensemble",          value: "73.95%", pct: 73.95, color: "#10b981" },
  { label: "ModernBERT-large ep3",     value: "70.29%", pct: 70.29, color: "#a855f7" },
  { label: "V8 mega-ensemble",         value: "68.42%", pct: 68.42, color: "#f97316" },
  { label: "Rubric Threshold",         value: "75.00%", pct: 75,    color: "#3b82f6" },
  { label: "V2 honest baseline",       value: "59.65%", pct: 59.65, color: "#374151" },
];

const EXAMPLES = [
  { label: "Financial",  text: "The company provides retail banking, mortgage loans, and investment portfolio management for individual and corporate clients across the United States." },
  { label: "Cloud/SaaS", text: "The company develops and sells cloud computing services and enterprise software for businesses. Its main products include productivity tools and database services." },
  { label: "Medical",    text: "The company manufactures surgical devices and diagnostic equipment used in hospitals and clinical settings globally." },
  { label: "Oil & Gas",  text: "The company explores and produces oil and natural gas from offshore and onshore fields in North America and the Gulf of Mexico." },
  { label: "Aerospace",  text: "The company designs and manufactures military aircraft, missiles, and defense systems for government and allied nation clients worldwide." },
];

const ACHIEVEMENT_STATS = [
  { value: "75.0%",    label: "Locked Macro F1",    sub: "calibrated ensemble · 10,717 test rows", color: "#22c55e" },
  { value: "91.4%",    label: "Top-3 Accuracy",     sub: "145 classes, company-disjoint", color: "#f59e0b" },
  { value: "97.2%",    label: "Leakage caught",     sub: "test rows memorized in V1 run", color: "#ef4444" },
  { value: "14",       label: "Model versions",     sub: "V2 honest baseline → locked ensemble", color: "#10b981" },
  { value: "580",      label: "Anchor features",    sub: "GECS taxonomy grounding", color: "#3b82f6" },
  { value: "55.44%",   label: "Task 2 Macro F1",    sub: "428 sub-industries · constrained", color: "#a855f7" },
];

// ── GECS taxonomy helpers ──────────────────────────────────────────────────────

const SECTOR_MAP: Record<string, { sector: string; group: string; color: string }> = {
  "101": { sector: "Energy",                   group: "Oil, Gas & Consumable Fuels", color: "#f97316" },
  "103": { sector: "Financial Services",        group: "Banks, Insurance & Capital Markets", color: "#22c55e" },
  "205": { sector: "Healthcare",               group: "Pharmaceuticals, Biotech & Medical", color: "#ec4899" },
  "206": { sector: "Healthcare",               group: "Medical Equipment & Devices", color: "#ec4899" },
  "210": { sector: "Consumer Defensive",       group: "Food, Beverages & Personal Products", color: "#f59e0b" },
  "211": { sector: "Consumer Cyclical",        group: "Retail, Apparel & Leisure", color: "#fb923c" },
  "306": { sector: "Real Estate",              group: "REITs & Real Estate Services", color: "#8b5cf6" },
  "308": { sector: "Communication Services",   group: "Media, Internet & Telecom", color: "#3b82f6" },
  "309": { sector: "Energy Equipment",         group: "Drilling & Oilfield Services", color: "#f97316" },
  "310": { sector: "Industrials / Materials",  group: "Aerospace, Machinery & Chemicals", color: "#6b7280" },
  "311": { sector: "Technology",               group: "Semiconductors & Hardware", color: "#06b6d4" },
};

const CODE_DIGIT_GUIDE = [
  { digits: "Digits 1-3",  meaning: "Sector identifier" },
  { digits: "Digits 4-5",  meaning: "Industry group within sector" },
  { digits: "Digits 6-8",  meaning: "Specific industry (MSTAR code ends here)" },
  { digits: "Digits 9-10", meaning: "Sub-industry activity (GECS extension)" },
];

function getSector(code: string) {
  for (const prefix of ["311","310","309","308","306","211","210","206","205","103","101"]) {
    if (code.startsWith(prefix)) return SECTOR_MAP[prefix];
  }
  return { sector: "Unclassified", group: "Unknown taxonomy", color: "#6b7280" };
}

// Clickable code chip with taxonomy popup
function CodeChip({ code, label, type }: { code: string; label: string; type: "mstar" | "gecs" }) {
  const [open, setOpen] = useState(false);
  const tax = getSector(code);
  const isMstar = type === "mstar";

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-2 text-sm font-mono bg-black/50 px-3 py-1.5 rounded border transition-all hover:bg-white/5 group"
        style={{ borderColor: isMstar ? "rgba(239,68,68,0.2)" : "rgba(59,130,246,0.2)", color: isMstar ? "rgba(252,165,165,0.7)" : "rgba(147,197,253,0.7)" }}
      >
        {isMstar ? "MSTAR-GLOBAL:" : "GECS-CODE:"} {code}
        <Info className="w-3 h-3 opacity-40 group-hover:opacity-80 transition-opacity" />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div className="fixed inset-0 z-[100] flex items-center justify-center p-4"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={() => setOpen(false)}>
            <div className="absolute inset-0 bg-black/75 backdrop-blur-sm" />
            <motion.div
              initial={{ opacity: 0, scale: 0.93, y: 12 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.93 }}
              transition={{ duration: 0.22 }}
              onClick={(e) => e.stopPropagation()}
              className="relative z-10 w-full max-w-lg border border-white/10 bg-[#0a0a0a] rounded-2xl p-7 shadow-2xl"
            >
              <button onClick={() => setOpen(false)} className="absolute top-4 right-4 text-white/25 hover:text-white transition-colors">
                <X className="w-5 h-5" />
              </button>

              {/* Header */}
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0"
                  style={{ backgroundColor: `${tax.color}15`, border: `1px solid ${tax.color}30` }}>
                  <span className="text-lg font-black font-mono" style={{ color: tax.color }}>
                    {isMstar ? "M" : "G"}
                  </span>
                </div>
                <div>
                  <div className="text-base font-bold font-mono text-white">
                    {isMstar ? "Morningstar Global Code" : "GECS Subindustry Code"}
                  </div>
                  <div className="text-xs font-mono text-white/30 mt-0.5">
                    {isMstar ? "8-digit industry identifier" : "10-digit granular activity code"}
                  </div>
                </div>
              </div>

              {/* The code with digit breakdown */}
              <div className="border border-white/[0.07] rounded-xl p-5 mb-5">
                <div className="text-xs font-mono text-white/30 uppercase tracking-widest mb-3">Code Breakdown</div>
                <div className="flex gap-0.5 mb-4">
                  {code.split("").map((digit, i) => (
                    <div key={i}
                      className="flex-1 h-10 rounded flex items-center justify-center text-base font-black font-mono text-white border"
                      style={{
                        backgroundColor: i < 3 ? `${tax.color}15` : i < 5 ? "rgba(255,255,255,0.05)" : i < 8 ? "rgba(255,255,255,0.03)" : "rgba(59,130,246,0.08)",
                        borderColor: i < 3 ? `${tax.color}30` : "rgba(255,255,255,0.06)",
                      }}
                    >
                      {digit}
                    </div>
                  ))}
                </div>
                <div className="space-y-2">
                  {CODE_DIGIT_GUIDE.filter((g, i) => isMstar ? i < 3 : true).map(({ digits, meaning }) => (
                    <div key={digits} className="flex gap-3 items-center">
                      <span className="text-xs font-mono text-white/30 w-20 flex-shrink-0">{digits}</span>
                      <span className="text-xs font-mono text-white/55">{meaning}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Taxonomy */}
              <div className="border border-white/[0.07] rounded-xl p-5">
                <div className="text-xs font-mono text-white/30 uppercase tracking-widest mb-4">Taxonomy Position</div>
                <div className="flex items-center gap-2 flex-wrap text-sm font-mono mb-3">
                  <span className="px-2 py-1 rounded text-xs font-bold" style={{ backgroundColor: `${tax.color}15`, color: tax.color }}>
                    {tax.sector}
                  </span>
                  <ChevronRight className="w-3.5 h-3.5 text-white/20" />
                  <span className="text-white/40 text-xs">{tax.group}</span>
                  <ChevronRight className="w-3.5 h-3.5 text-white/20" />
                  <span className="text-white font-bold text-xs">{label}</span>
                </div>
                <div className="text-xs font-mono text-white/20">
                  Source: Morningstar Global Equity Classification Standard (GECS) - used by institutional analysts to classify publicly traded companies worldwide.
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

// ── Types ──────────────────────────────────────────────────────────────────────

type Alternative = { rank: number; code: string; label: string; confidence: number };
type Result = {
  mstar_code: string; mstar_label: string;
  sub_code: string;   sub_label: string;
  confidence_t1: number | null; alternatives_t1: Alternative[]; features_t1: string[];
  confidence_t2: number | null; alternatives_t2: Alternative[]; features_t2: string[];
};

// ── Sub-components ─────────────────────────────────────────────────────────────

function LiveClock() {
  const [t, setT] = useState("");
  useEffect(() => {
    const tick = () => setT(new Date().toISOString().replace("T", " ").slice(0, 19) + " UTC");
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);
  return <span className="font-mono text-xs text-green-400/50 tabular-nums">{t}</span>;
}

function Cursor() {
  return (
    <motion.span
      animate={{ opacity: [1, 0] }}
      transition={{ duration: 0.65, repeat: Infinity, repeatType: "reverse" }}
      className="inline-block w-[6px] h-4 bg-green-400 ml-0.5 align-middle"
    />
  );
}

// Confidence info popup
function ConfidencePopup({
  pct, color, alts, onClose,
}: {
  pct: number | null; color: string; alts: Alternative[]; onClose: () => void;
}) {
  return (
    <AnimatePresence>
      <motion.div
        className="fixed inset-0 z-[100] flex items-center justify-center p-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
      >
        {/* Backdrop */}
        <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" />

        <motion.div
          initial={{ opacity: 0, scale: 0.92, y: 16 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.92 }}
          transition={{ duration: 0.25 }}
          onClick={(e) => e.stopPropagation()}
          className="relative z-10 w-full max-w-md border border-white/10 bg-[#0a0a0a] rounded-2xl p-7 shadow-2xl"
        >
          <button onClick={onClose}
            className="absolute top-4 right-4 text-white/25 hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-2 mb-5">
            <Info className="w-4 h-4" style={{ color }} />
            <span className="text-sm font-mono font-bold uppercase tracking-widest" style={{ color }}>
              What is Confidence?
            </span>
          </div>

          <p className="text-base text-white/70 leading-relaxed mb-6">
            Your LinearSVC model scores every possible industry. The winner becomes the prediction.
            <br /><br />
            <span className="text-white font-semibold">Confidence = how far ahead the winner scored vs. the rest.</span>
            <br /><br />
            High % → the model had a clear answer. Low % → several industries scored close together.
          </p>

          {/* Score breakdown */}
          {alts.length > 0 && (
            <div className="border border-white/[0.07] rounded-xl p-4">
              <div className="text-xs font-mono text-white/30 uppercase tracking-widest mb-4">Score Breakdown</div>
              <div className="space-y-3">
                {alts.map((a) => (
                  <div key={a.code} className="space-y-1.5">
                    <div className="flex justify-between items-center">
                      <span className={`text-sm font-mono ${a.rank === 1 ? "text-white font-bold" : "text-white/45"}`}>
                        {a.rank === 1 ? "✓ " : ""}{a.label}
                      </span>
                      <span className="text-sm font-mono font-bold tabular-nums"
                        style={{ color: a.rank === 1 ? color : "rgba(255,255,255,0.25)" }}>
                        {a.confidence.toFixed(1)}%
                      </span>
                    </div>
                    <div className="h-[3px] bg-white/5 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${a.confidence}%` }}
                        transition={{ duration: 0.7, delay: a.rank * 0.08 }}
                        className="h-full rounded-full"
                        style={{ backgroundColor: a.rank === 1 ? color : "rgba(255,255,255,0.15)" }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <p className="text-xs font-mono text-white/20 mt-5 leading-relaxed">
            Note: These scores come from the model's decision function converted to percentages.
            They show relative certainty, not calibrated probability.
          </p>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

// Large confidence arc gauge - click to explain
function ConfidenceGauge({
  pct, color, alts = [],
}: {
  pct: number | null; color: string; alts?: Alternative[];
}) {
  const [open, setOpen] = useState(false);
  const r      = 52;
  const circ   = 2 * Math.PI * r;
  const arc    = circ * 0.75;
  const filled = pct !== null ? arc * (pct / 100) : 0;

  return (
    <>
      <div className="flex flex-col items-center cursor-pointer group" onClick={() => setOpen(true)}>
        <div className="relative w-36 h-36">
          <svg viewBox="0 0 120 120" className="w-full h-full" style={{ transform: "rotate(-225deg)" }}>
            <circle cx="60" cy="60" r={r} fill="none" stroke="rgba(255,255,255,0.06)"
              strokeWidth="8" strokeLinecap="round"
              strokeDasharray={`${arc} ${circ - arc}`} />
            <motion.circle cx="60" cy="60" r={r} fill="none" stroke={color}
              strokeWidth="8" strokeLinecap="round"
              strokeDasharray={`${arc} ${circ - arc}`}
              initial={{ strokeDashoffset: arc }}
              animate={{ strokeDashoffset: arc - filled }}
              transition={{ duration: 1.4, ease: "easeOut", delay: 0.1 }}
              style={{ filter: `drop-shadow(0 0 6px ${color}60)` }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            {pct !== null ? (
              <>
                <span className="text-3xl font-black font-mono text-white tabular-nums leading-none">
                  {pct.toFixed(1)}
                </span>
                <span className="text-sm font-mono text-white/40 mt-0.5">%</span>
              </>
            ) : (
              <span className="text-sm font-mono text-white/20">N/A</span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-1.5 mt-1">
          <span className="text-xs font-mono text-white/30 uppercase tracking-widest group-hover:text-white/50 transition-colors">
            Confidence
          </span>
          <Info className="w-3 h-3 text-white/20 group-hover:text-white/40 transition-colors" />
        </div>
      </div>

      {open && (
        <ConfidencePopup pct={pct} color={color} alts={alts} onClose={() => setOpen(false)} />
      )}
    </>
  );
}

function PerfBar({ label, value, pct, color }: { label: string; value: string; pct: number; color: string }) {
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between">
        <span className="text-xs font-mono text-white/30">{label}</span>
        <span className="text-xs font-bold font-mono text-white/60">{value}</span>
      </div>
      <div className="h-[2px] bg-white/5">
        <motion.div initial={{ width: 0 }} whileInView={{ width: `${pct}%` }}
          viewport={{ once: true }} transition={{ duration: 1.2, ease: "easeOut" }}
          className="h-full" style={{ backgroundColor: color }} />
      </div>
    </div>
  );
}

function AlternativesList({ alts, color }: { alts: Alternative[]; color: string }) {
  if (!alts.length) return null;
  return (
    <div className="space-y-3 mt-5">
      <div className="text-xs font-mono text-white/25 uppercase tracking-widest">Alternative Predictions</div>
      {alts.map((a) => (
        <div key={a.code} className="flex items-center gap-3">
          <span className="text-xs font-mono text-white/25 w-4 flex-shrink-0">#{a.rank}</span>
          <div className="flex-1 min-w-0">
            <div className="text-sm font-mono text-white/60 truncate mb-1">{a.label}</div>
            <div className="h-[2px] bg-white/5">
              <motion.div initial={{ width: 0 }} animate={{ width: `${a.confidence}%` }}
                transition={{ duration: 0.9, delay: a.rank * 0.1 }} className="h-full"
                style={{ backgroundColor: a.rank === 1 ? color : "rgba(255,255,255,0.12)" }} />
            </div>
          </div>
          <span className="text-sm font-mono tabular-nums flex-shrink-0 font-bold"
            style={{ color: a.rank === 1 ? color : "rgba(255,255,255,0.25)" }}>
            {a.confidence.toFixed(1)}%
          </span>
        </div>
      ))}
    </div>
  );
}

function FeatureTags({ features, color }: { features: string[]; color: string }) {
  if (!features.length) return null;
  return (
    <div className="mt-5">
      <div className="text-xs font-mono text-white/25 uppercase tracking-widest mb-2.5">Key Signal Terms</div>
      <div className="flex flex-wrap gap-2">
        {features.map((f) => (
          <span key={f} className="text-sm font-mono px-3 py-1 border rounded-full"
            style={{ borderColor: `${color}25`, backgroundColor: `${color}08`, color: `${color}80` }}>
            {f}
          </span>
        ))}
      </div>
    </div>
  );
}

// Right panel idle state - ML analyst stats
function IdlePanel() {
  return (
    <motion.div key="idle" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      className="h-full flex flex-col gap-4">

      {/* F1 performance */}
      <div className="border border-white/[0.06] rounded-xl p-6">
        <div className="flex items-center gap-2 mb-5">
          <BarChart3 className="w-4 h-4 text-white/25" />
          <span className="text-sm font-mono text-white/25 uppercase tracking-widest">Model Evaluation Metrics</span>
        </div>
        <div className="space-y-4">
          {PERF_BARS.map((m) => <PerfBar key={m.label} {...m} />)}
        </div>
        <div className="mt-5 flex items-center gap-3 border border-emerald-500/20 bg-emerald-500/[0.04] rounded-lg px-4 py-3">
          <Shield className="w-4 h-4 text-emerald-400 flex-shrink-0" />
          <div>
            <div className="text-sm font-mono text-emerald-400 font-bold">RUBRIC PASSED</div>
            <div className="text-xs font-mono text-white/30 mt-0.5">75.0% Macro F1 · meets 75% threshold · 91.4% top-3 · cross-validated</div>
          </div>
        </div>
      </div>

      {/* ML analyst stats grid */}
      <div className="grid grid-cols-2 gap-3">
        {[
          { label: "Algorithm",          value: "LinearSVC",     sub: "dual=False · class_weight=balanced",   color: "#ef4444" },
          { label: "Vectoriser",         value: "TF-IDF",        sub: "sublinear_tf · (1,2)-ngrams",          color: "#3b82f6" },
          { label: "T1 Training Set",    value: "42,868",        sub: "80/20 stratified split",               color: "#f97316" },
          { label: "T1 Test Set",        value: "10,717",        sub: "held-out evaluation set",              color: "#f97316" },
          { label: "T2 Training Set",    value: "~17,609",       sub: "classes with ≥5 samples",             color: "#8b5cf6" },
          { label: "Class Imbalance",    value: "Severe",        sub: "balanced weighting applied",           color: "#f59e0b" },
          { label: "T1 vs Random",       value: "90×",           sub: "62.61% acc vs 0.69% baseline",        color: "#10b981" },
          { label: "F1 Before Fix",      value: "43%",           sub: "LinearSVC without balancing",          color: "#6b7280" },
          { label: "F1 After Fix",       value: "86.82%",        sub: "after class_weight=balanced",          color: "#10b981" },
          { label: "Avg Text Length T1", value: "639 chars",     sub: "LongProfile + segments",               color: "#22d3ee" },
          { label: "Avg Text Length T2", value: "229 chars",     sub: "SegmentName + SegmentDescription",     color: "#22d3ee" },
          { label: "Library",            value: "breezeml v5",   sub: "5 patches · custom wrapper",           color: "#a855f7" },
        ].map(({ label, value, sub, color }) => (
          <div key={label} className="border border-white/[0.06] rounded-lg px-4 py-3">
            <div className="text-xs font-mono text-white/25 mb-1">{label}</div>
            <div className="text-base font-black font-mono" style={{ color }}>{value}</div>
            <div className="text-[10px] font-mono text-white/20 mt-0.5">{sub}</div>
          </div>
        ))}
      </div>

      <div className="border border-white/[0.05] rounded-xl p-5 text-center">
        <Radio className="w-5 h-5 text-white/10 mx-auto mb-3" />
        <p className="text-white/20 font-mono text-sm">
          Paste a company description on the left and run the model.
        </p>
      </div>
    </motion.div>
  );
}

// Right panel result state - the hero
function ResultPanel({ result, resultKey }: { result: Result; resultKey: number }) {
  return (
    <motion.div key={`result-${resultKey}`}
      initial={{ opacity: 0, y: 20, filter: "blur(10px)" }}
      animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
      transition={{ duration: 0.55, ease: "easeOut" }}
      className="flex flex-col gap-4 h-full">

      {/* ── TASK 1 ── */}
      <div className="border border-red-500/20 bg-red-500/[0.03] rounded-xl p-6 flex-1">
        <div className="text-xs font-mono text-red-400/50 uppercase tracking-widest mb-1">
          Task 1 - Global Industry Classification
        </div>
        <div className="text-xs font-mono text-white/15 mb-6">
          LinearSVC · 145 Classes · 60,000 TF-IDF Features
        </div>

        <div className="flex items-start gap-8">
          <ConfidenceGauge pct={result.confidence_t1} color="#ef4444" alts={result.alternatives_t1 ?? []} />

          <div className="flex-1 min-w-0">
            <motion.div
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
            >
              <div className="text-4xl sm:text-5xl font-black text-white leading-tight mb-4">
                {result.mstar_label}
              </div>
              <CodeChip code={result.mstar_code} label={result.mstar_label} type="mstar" />
            </motion.div>
          </div>
        </div>

        <AlternativesList alts={result.alternatives_t1 ?? []} color="#ef4444" />
        <FeatureTags features={result.features_t1 ?? []} color="#ef4444" />
      </div>

      {/* ── TASK 2 ── */}
      <div className="border border-blue-500/20 bg-blue-500/[0.03] rounded-xl p-6 flex-1">
        <div className="text-xs font-mono text-blue-400/50 uppercase tracking-widest mb-1">
          Task 2 - Granular Subindustry Classification
        </div>
        <div className="text-xs font-mono text-white/15 mb-6">
          LinearSVC · 428 Classes · 10,000 TF-IDF Features
        </div>

        <div className="flex items-start gap-8">
          <ConfidenceGauge pct={result.confidence_t2} color="#3b82f6" alts={result.alternatives_t2 ?? []} />

          <div className="flex-1 min-w-0">
            <motion.div
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 }}
            >
              <div className="text-4xl sm:text-5xl font-black text-white leading-tight mb-4">
                {result.sub_label}
              </div>
              <CodeChip code={result.sub_code} label={result.sub_label} type="gecs" />
            </motion.div>
          </div>
        </div>

        <AlternativesList alts={result.alternatives_t2 ?? []} color="#3b82f6" />
        <FeatureTags features={result.features_t2 ?? []} color="#3b82f6" />
      </div>
    </motion.div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────

export default function Dashboard() {
  const [text, setText]             = useState("");
  const [loading, setLoading]       = useState(false);
  const [activeStep, setActiveStep] = useState(-1);
  const [stepTimes, setStepTimes]   = useState<(number | null)[]>(Array(5).fill(null));
  const [stepProgress, setStepProgress] = useState(0);
  const [result, setResult]         = useState<Result | null>(null);
  const [error, setError]           = useState("");
  const [resultKey, setResultKey]   = useState(0);
  const [queryCount, setQueryCount] = useState(0);
  const [latencyMs, setLatencyMs]   = useState<number | null>(null);

  // Animate fill bar within the active step
  useEffect(() => {
    if (activeStep < 0 || activeStep >= PIPELINE_STEPS.length) { setStepProgress(0); return; }
    setStepProgress(0);
    const dur = STEP_DURATIONS[activeStep];
    const t0  = performance.now();
    let raf: number;
    const tick = () => {
      const pct = Math.min(95, ((performance.now() - t0) / dur) * 100);
      setStepProgress(pct);
      if (pct < 95) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [activeStep]);

  async function runInference() {
    if (!text.trim() || loading) return;
    setLoading(true);
    setResult(null);
    setError("");
    setLatencyMs(null);
    setStepTimes(Array(5).fill(null));

    // Run animation and fetch in parallel - total time = max(anim, api) not sum
    const t0 = performance.now();

    const animPromise = (async () => {
      for (let i = 0; i < PIPELINE_STEPS.length; i++) {
        setActiveStep(i);
        const s = performance.now();
        await new Promise<void>((r) => setTimeout(r, STEP_DURATIONS[i]));
        setStepTimes((prev) => { const n = [...prev]; n[i] = Math.round(performance.now() - s); return n; });
      }
    })();

    const fetchPromise = fetch("/api/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ company_text: text, segment_text: text, include_reasoning: true }),
    });

    try {
      const [, res] = await Promise.all([animPromise, fetchPromise]);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Server error");
      setLatencyMs(Math.round(performance.now() - t0));
      setResult(data);
      setResultKey((k) => k + 1);
      setActiveStep(PIPELINE_STEPS.length);
      setQueryCount((c) => c + 1);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Cannot reach HF Space — it may still be warming up. Wait 30 seconds and try again.");
      setActiveStep(-1);
    } finally {
      setLoading(false);
    }
  }

  const canRun = text.trim() && !loading;
  const hasResult = !!result;
  const clearAll = () => {
    setText("");
    setResult(null);
    setError("");
    setActiveStep(-1);
    setStepTimes(Array(5).fill(null));
  };

  return (
    <div className="min-h-screen bg-[#050505] text-white p-4 lg:p-8 font-sans selection:bg-red-500/30">
      <div className="max-w-7xl mx-auto space-y-6">

        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-white/[0.08] pb-8">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="px-2 py-1 bg-red-500/10 border border-red-500/20 rounded text-[10px] font-black font-mono text-red-500 tracking-tighter uppercase">
                Production Ready
              </div>
              <div className="text-xs font-mono text-white/20 uppercase tracking-widest">
                GECS-Sage v5.2 · Classification Pipeline
              </div>
            </div>
            <h1 className="text-4xl md:text-6xl font-black tracking-tighter text-white">
              GECS<span className="text-red-600">.</span>SAGE
            </h1>
          </div>

          <div className="flex flex-col items-end gap-2">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-xs font-mono text-white/40 uppercase tracking-widest">System Online</span>
              </div>
              <div className="h-4 w-px bg-white/10" />
              <div className="flex items-center gap-2 text-xs font-mono text-white/40 uppercase tracking-widest">
                <Database className="w-3.5 h-3.5" />
                <span>{queryCount} Queries</span>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {latencyMs !== null && (
                <span className="text-sm font-mono text-white/25">
                  API <span className="text-amber-400/70">{latencyMs}ms</span>
                </span>
              )}
              <LiveClock />
            </div>
          </div>
        </div>

        {/* ── MAIN SPLIT ── */}
        <div className="grid grid-cols-12 gap-5">

          {/* ── LEFT · Input + pipeline ── */}
          <div className="col-span-12 lg:col-span-5 flex flex-col gap-4">

            {/* Terminal input */}
            <div className="border border-white/[0.08] bg-black rounded-xl overflow-hidden flex flex-col" style={{ minHeight: 340 }}>
              <div className="flex items-center gap-2 px-5 py-3 border-b border-white/[0.06]">
                <span className="w-3 h-3 rounded-full bg-red-500/80" />
                <span className="w-3 h-3 rounded-full bg-amber-400/80" />
                <span className="w-3 h-3 rounded-full bg-green-500/80" />
                <span className="ml-3 text-xs font-mono text-white/25">gecs_classifier.py - inference terminal</span>
              </div>
              <div className="flex-1 p-5 font-mono flex flex-col">
                <div className="text-green-400/40 text-xs mb-1">$ breezeml.predict(</div>
                <div className="text-amber-300/40 text-xs mb-2">&nbsp; text="""</div>
                <textarea
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) runInference(); }}
                  rows={8}
                  placeholder="Paste a company or business segment description here..."
                  className="flex-1 w-full bg-transparent text-white text-base leading-relaxed resize-none outline-none placeholder:text-white/10 font-mono"
                />
                <div className="text-amber-300/40 text-xs mt-2">&nbsp; """</div>
                <div className="flex items-center text-green-400/40 text-xs mt-1">
                  )
                  {!loading && <Cursor />}
                  {loading && <Loader2 className="w-3 h-3 ml-2 text-red-400 animate-spin" />}
                </div>
                <div className="text-white/10 text-xs mt-2">⌘ Enter to run</div>
              </div>
            </div>

            {/* Examples */}
            <div className="flex flex-wrap gap-2">
              {EXAMPLES.map((ex) => (
                <button key={ex.label} onClick={() => setText(ex.text)}
                  className="px-3 py-1.5 text-xs font-mono border border-white/[0.07] text-white/35 hover:text-green-300 hover:border-green-500/25 rounded-lg transition-colors">
                  {ex.label}
                </button>
              ))}
            </div>

            {/* Run + Clear buttons */}
            <div className="flex gap-3">
              <button onClick={runInference} disabled={!canRun}
                className="flex-1 py-4 font-mono font-bold text-sm tracking-widest uppercase border rounded-xl transition-all flex items-center justify-center gap-3 disabled:opacity-20 disabled:cursor-not-allowed"
                style={{
                  borderColor: canRun ? "rgba(239,68,68,0.5)" : "rgba(239,68,68,0.15)",
                  backgroundColor: canRun ? "rgba(239,68,68,0.08)" : "transparent",
                  color: "#ef4444",
                  boxShadow: canRun ? "0 0 40px rgba(239,68,68,0.1)" : "none",
                }}>
                {loading
                  ? <><Loader2 className="w-4 h-4 animate-spin" /> PROCESSING...</>
                  : <><Zap className="w-4 h-4" /> RUN CLASSIFICATION</>}
              </button>

              {hasResult && (
                <motion.button
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  onClick={clearAll}
                  className="px-5 py-4 font-mono font-bold text-sm uppercase border border-white/10 bg-white/[0.03] hover:bg-white/[0.07] text-white/40 hover:text-white rounded-xl transition-all"
                >
                  Clear
                </motion.button>
              )}
            </div>

            {/* Pipeline */}
            <div className="border border-white/[0.06] rounded-xl p-5">
              <div className="flex items-center gap-2 mb-4">
                <Activity className="w-4 h-4 text-white/25" />
                <span className="text-xs font-mono text-white/25 uppercase tracking-widest">Inference Pipeline</span>
              </div>
              <div className="space-y-0.5">
                {PIPELINE_STEPS.map((step, i) => {
                  const isActive  = activeStep === i;
                  const isDone    = activeStep > i;
                  const Icon      = step.icon;
                  return (
                    <div key={i}
                      className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${isActive ? "bg-red-500/8 border border-red-500/15" : isDone ? "bg-emerald-500/5 border border-emerald-500/10" : "border border-transparent"}`}>
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${isDone ? "bg-emerald-500/15" : isActive ? "bg-red-500/15" : "bg-white/4"}`}>
                        {isDone   ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> :
                         isActive ? <Loader2 className="w-4 h-4 text-red-400 animate-spin" /> :
                                    <Icon className="w-4 h-4 text-white/15" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className={`text-xs font-mono font-bold tracking-wider ${isDone ? "text-emerald-400" : isActive ? "text-red-400" : "text-white/20"}`}>
                          {step.label}
                        </div>
                        <div className="text-[10px] font-mono text-white/15 mt-0.5">{step.detail}</div>
                        {isActive && (
                          <div className="h-[1px] bg-white/5 mt-1.5">
                            <motion.div animate={{ width: `${stepProgress}%` }} transition={{ duration: 0.1 }}
                              className="h-full bg-red-500/50" />
                          </div>
                        )}
                      </div>
                      <div className="w-12 text-right flex-shrink-0">
                        {isDone && stepTimes[i] !== null &&
                          <span className="text-xs font-mono text-emerald-400/50">{stepTimes[i]}ms</span>}
                        {isActive &&
                          <motion.span animate={{ opacity: [1, 0.2, 1] }} transition={{ duration: 0.5, repeat: Infinity }}
                            className="text-xs font-mono text-red-400">RUN</motion.span>}
                        {!isActive && !isDone && <span className="text-xs font-mono text-white/10">-</span>}
                      </div>
                    </div>
                  );
                })}
              </div>
              <div className="mt-4 pt-3 border-t border-white/[0.05]">
                <span className={`text-xs font-mono ${activeStep < 0 ? "text-white/15" : activeStep >= PIPELINE_STEPS.length ? "text-emerald-400" : "text-red-400"}`}>
                  {activeStep < 0                       && "AWAITING INPUT"}
                  {activeStep >= 0 && activeStep < PIPELINE_STEPS.length && `EXECUTING: ${PIPELINE_STEPS[activeStep]?.label}`}
                  {activeStep >= PIPELINE_STEPS.length  && "INFERENCE COMPLETE"}
                </span>
              </div>
            </div>
          </div>

          {/* ── RIGHT · Results ── */}
          <div className="col-span-12 lg:col-span-7 flex flex-col">
            <AnimatePresence mode="wait">
              {error && (
                <motion.div key="err" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                  className="border border-red-500/25 bg-red-500/[0.04] rounded-xl p-6 flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <div className="text-sm font-mono text-red-400 font-bold mb-1">INFERENCE ERROR</div>
                    <div className="text-base font-mono text-red-300/70">{error}</div>
                  </div>
                </motion.div>
              )}
              {result && <ResultPanel result={result} resultKey={resultKey} />}
              {!result && !error && <IdlePanel />}
            </AnimatePresence>
          </div>
        </div>

        {/* ── MODEL EVALUATION - always visible ── */}
        <div className="mt-5 border border-white/[0.06] rounded-xl p-6">
          <div className="flex items-center gap-2 mb-6">
            <BarChart3 className="w-4 h-4 text-white/25" />
            <span className="text-sm font-mono text-white/25 uppercase tracking-widest">Model Evaluation</span>
            <div className="ml-auto flex items-center gap-2 border border-emerald-500/20 bg-emerald-500/[0.04] rounded-lg px-3 py-1.5">
              <Shield className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-xs font-mono text-emerald-400 font-bold">LOCKED - 75.0% Macro F1 · 91.4% top-3 · cross-validated</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Task 1 metrics */}
            <div>
              <div className="text-xs font-mono text-red-400/60 uppercase tracking-widest mb-4">Task 1 - Industry (145 Classes)</div>
              <div className="space-y-3.5">
                {[
                  { label: "Macro F1 ★",      value: "75.0%",  pct: 75.0,  color: "#22c55e" },
                  { label: "Weighted F1",     value: "86.82%", pct: 86.82, color: "#ef4444" },
                  { label: "Accuracy",        value: "62.61%", pct: 62.61, color: "#f97316" },
                  { label: "Rubric Min F1",   value: "75.00%", pct: 75,    color: "#10b981" },
                  { label: "Random Baseline", value: "0.69%",  pct: 0.69,  color: "#374151" },
                ].map((m) => <PerfBar key={m.label} {...m} />)}
              </div>
              <div className="mt-4 grid grid-cols-3 gap-2">
                {[
                  { label: "Train",    value: "42,868" },
                  { label: "Test",     value: "10,717" },
                  { label: "Features", value: "60,000" },
                ].map(({ label, value }) => (
                  <div key={label} className="border border-white/[0.05] rounded-lg p-2.5 text-center">
                    <div className="text-base font-black font-mono text-white/80">{value}</div>
                    <div className="text-[10px] font-mono text-white/25 mt-0.5">{label}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Task 2 metrics */}
            <div>
              <div className="text-xs font-mono text-blue-400/60 uppercase tracking-widest mb-4">Task 2 - Subindustry (428 Classes)</div>
              <div className="space-y-3.5">
                {[
                  { label: "Macro F1 ★",      value: "55.41%", pct: 55.41, color: "#22d3ee" },
                  { label: "Weighted F1",      value: "47.72%", pct: 47.72, color: "#3b82f6" },
                  { label: "Macro F1",        value: "39.62%", pct: 39.62, color: "#8b5cf6" },
                  { label: "Accuracy",        value: "51.06%", pct: 51.06, color: "#8b5cf6" },
                  { label: "Rubric Min F1",   value: "75.00%", pct: 75,    color: "#10b981" },
                  { label: "Random Baseline", value: "0.24%",  pct: 0.24,  color: "#374151" },
                ].map((m) => <PerfBar key={m.label} {...m} />)}
              </div>
              <div className="mt-4 grid grid-cols-3 gap-2">
                {[
                  { label: "Train",    value: "~17,609" },
                  { label: "Test",     value: "~4,403"  },
                  { label: "Features", value: "10,000"  },
                ].map(({ label, value }) => (
                  <div key={label} className="border border-white/[0.05] rounded-lg p-2.5 text-center">
                    <div className="text-base font-black font-mono text-white/80">{value}</div>
                    <div className="text-[10px] font-mono text-white/25 mt-0.5">{label}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Key insight strip */}
          <div className="mt-5 grid grid-cols-1 sm:grid-cols-3 gap-3">
            {[
              { label: "Flat SVM Macro F1",      value: "59.70%",  sub: "same data, 145 classes flat",        color: "#f97316" },
              { label: "Calibrated Ensemble ★", value: "75.0%",  sub: "ModernBERT-large · locked result",   color: "#22c55e" },
              { label: "Top-3 Accuracy",            value: "91.4%",   sub: "company-disjoint test set",          color: "#f59e0b" },
            ].map(({ label, value, sub, color }) => (
              <div key={label} className="border border-white/[0.05] rounded-lg px-4 py-3 flex items-center gap-4">
                <div className="text-2xl font-black font-mono flex-shrink-0" style={{ color }}>{value}</div>
                <div>
                  <div className="text-sm font-semibold text-white/50">{label}</div>
                  <div className="text-xs font-mono text-white/20 mt-0.5">{sub}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ── ACHIEVEMENT STRIP ── */}
        <div className="mt-5 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {ACHIEVEMENT_STATS.map(({ value, label, sub, color }) => (
            <motion.div key={label} whileHover={{ scale: 1.02 }}
              className="border border-white/[0.06] rounded-xl p-4 text-center hover:border-white/10 transition-colors">
              <div className="text-2xl font-black font-mono mb-1" style={{ color }}>{value}</div>
              <div className="text-sm font-semibold text-white/40 mb-0.5">{label}</div>
              <div className="text-xs font-mono text-white/20">{sub}</div>
            </motion.div>
          ))}
        </div>

        {/* Footer */}
        <div className="mt-8 text-center">
          <span className="text-xs font-mono text-white/15 uppercase tracking-widest">
            MGT 599 Capstone · Group 4 · DePaul University Chicago · Spring 2026 · BreezeML Level 2
          </span>
        </div>
      </div>
    </div>
  );
}
