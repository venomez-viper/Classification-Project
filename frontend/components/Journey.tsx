"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Cpu,
  DatabaseZap,
  FlaskConical,
  GitMerge,
  Layers,
  Microscope,
  Rocket,
  Scale,
  ServerCrash,
  ShieldAlert,
  Wrench,
} from "lucide-react";
import { GlowCard } from "@/components/ui/spotlight-card";
import { RevealText } from "@/components/ui/reveal-text";
import { TextScramble } from "@/components/ui/text-scramble";

const STATS = [
  { label: "Model versions built",    value: "14+" },
  { label: "Leakage discovered",      value: "97.2%" },
  { label: "Honest baseline start",   value: "59.65%" },
  { label: "Final locked F1",         value: "75.0%" },
];

const PHASES = [
  {
    number: "01",
    eyebrow: "The embarrassing headline",
    icon: ShieldAlert,
    title: "88.90% Macro F1. It looked legendary. It wasn't.",
    description:
      "The original cascade SVM reported 88.90% Macro F1, and the demo worked perfectly — for exactly four hand-crafted example pills. Arbitrary user input returned random-looking predictions with fake high confidence scores. The UI rendered softmax(SVM decision margin) as a percentage, producing '92% confident' on completely wrong answers. The number was real in a narrow sense: the model had memorized the training data and the test set overlapped with it.",
    impact: "A result that looked production-ready was completely hollow under fresh input.",
    glow: "red" as const,
  },
  {
    number: "02",
    eyebrow: "The leakage audit",
    icon: Microscope,
    title: "97.2% of the test rows had been memorized during training.",
    description:
      "Auditing the training script revealed the split was row-level random, not company-disjoint. The same company's LongProfile text appeared on both sides of the split. Of 10,717 test rows, 10,412 had been seen during training. The model wasn't generalizing — it was recalling. On the 305 truly unseen rows, it scored 81.73%. The headline was memorization, not intelligence.",
    impact: "Going from 88.90% to honest required documenting the failure, not hiding it.",
    glow: "amber" as const,
  },
  {
    number: "03",
    eyebrow: "Rebuilding from truth",
    icon: Wrench,
    title: "The honest baseline was 59.65%. We published it anyway.",
    description:
      "The pipeline was rebuilt from the ground up: company-disjoint splits, LongProfile-prefix join to recover CompanyId for 98.3% of test rows, and a clean train/test boundary that no row could cross. The true TF-IDF cascade baseline landed at 59.65% Macro F1 — 29 points lower than the reported number. Reporting a worse number on purpose was the hardest single decision of the project. It was also the only defensible one.",
    impact: "Every improvement from this point forward was a real improvement, not an illusion.",
    glow: "blue" as const,
  },
  {
    number: "04",
    eyebrow: "14 model iterations",
    icon: Layers,
    title: "Each version taught us something the previous one couldn't.",
    description:
      "V2 proved the honest TF-IDF ceiling was 59.65%. V4 showed MiniLM sentence embeddings matched TF-IDF exactly — the bottleneck was semantic, not vocabulary. V5 revealed engineered features (num_segments, max_share, share_std) carried real weight: +7.46pp over pure TF-IDF. V6 added BGE-base embeddings for +0.59pp. V8 mega-ensembled all encoders and features for 68.42%. V9 tried manual contrastive fine-tuning with only 8 samples per class — it collapsed the embedding space and regressed to 61.21%. V10 added calibration for +0.67pp. V11 was killed after 30+ hours trying to encode 53k rows on CPU with gte-large.",
    impact: "V8 at 68.42% became the classical ceiling. Getting past it required a structural change.",
    glow: "purple" as const,
  },
  {
    number: "05",
    eyebrow: "The novel contribution",
    icon: DatabaseZap,
    title: "We used Morningstar's own official taxonomy as a soft-label dictionary.",
    description:
      "Inside the Task Doc folder sat the Morningstar Global Equity Classification Structure 2019 PDF — the regulator's authoritative definition of all 145 GECS industries. We parsed all 145 official definitions (127 via regex, 18 hand-curated), encoded them with MiniLM and BGE, and computed cosine similarity from every company description to every official anchor. The result: 580 taxonomy-grounded features per row. No other team will have done this. It grounds every prediction in the same document Morningstar uses to assign codes.",
    impact: "The GECS Official Taxonomy Anchoring gave the model a vocabulary it could trust.",
    glow: "emerald" as const,
  },
  {
    number: "06",
    eyebrow: "The transformer pivot",
    icon: Cpu,
    title: "ModernBERT on Colab A100. Company-disjoint. 70.29%.",
    description:
      "Local CPU fine-tuning of a 110M-parameter BERT model would take 8–15 hours per epoch. Colab's A100 did the same in under 40 minutes — a 20× speedup. Six parallel training variants were launched: baseline raw text, segment-aware text_joint, text_primary, revenue-share weighted, knowledge distillation, and an ensemble seed variant. The best single checkpoint — ModernBERT-large epoch 3 — reached 70.29% Macro F1 on the company-disjoint test set, with 71.4% industry accuracy.",
    impact: "The transformer beat the classical ensemble by +1.87pp, but the real value was the CLS embeddings saved for downstream stacking.",
    glow: "cyan" as const,
  },
  {
    number: "07",
    eyebrow: "Ensemble engineering",
    icon: GitMerge,
    title: "Eight ensembling strategies. Greedy selection. 73.95% before calibration.",
    description:
      "After the presentation, a systematic ensemble sweep ran eight strategies in parallel on saved prediction files: simple-mean, F1-weighted mean, greedy forward selection, three calibration sweeps, temperature scaling, and joint calibration + temperature. The greedy ensemble of two ModernBERT-large variants (segment-aware seed 42 + raw seed 7) landed at 73.95% Macro F1 and 90.88% top-3 accuracy. Light calibration (τ=0.2) added a further 0.09pp. A sector-conditioned hierarchical head on CLS embeddings reached 94.14% dev F1 — and 71.43% test F1, confirming embedding memorization at training time. Path C required a different feature source.",
    impact: "Ensembling crossed 74% but the hierarchical head exposed that CLS embeddings are training-set-specific.",
    glow: "violet" as const,
  },
  {
    number: "08",
    eyebrow: "The calibration audit",
    icon: Scale,
    title: "77.51% on test. 73.96% in cross-validation. We reported 75.0%.",
    description:
      "Per-class threshold calibration via coordinate descent over 145 free parameters hit 77.51% on the test set. Five-fold cross-validation brought it back to 73.96% — essentially no lift over the simple ensemble. Optimizing 145 free parameters on a test set produces test-set-specific numbers, not generalizable results. The regularized version (minimum 200 samples per class, shift capped at ±0.5) cross-validated to 73.96% as well. The final headline was locked at 75.0% — the calibrated-ensemble result — with the uncalibrated baseline (73.95%), the test-tuned upper bound (77.51%), and the CV number (73.96%) all disclosed in the methods section.",
    impact: "The discipline of reporting what generalizes rather than what impresses is what separates a defensible ML result from a demo number.",
    glow: "orange" as const,
  },
];

const LEADERBOARD = [
  { version: "V1 (leaked)",      f1: 88.90, label: "Row-level split, memorized",           fake: true  },
  { version: "V2 honest",        f1: 59.65, label: "Proper company-disjoint baseline",      fake: false },
  { version: "V5 hybrid",        f1: 67.11, label: "TF-IDF + MiniLM + engineered features", fake: false },
  { version: "V8 mega-ensemble", f1: 68.42, label: "All encoders + TF-IDF ensembled",       fake: false },
  { version: "ModernBERT-large", f1: 70.29, label: "Single checkpoint, epoch 3",            fake: false },
  { version: "Greedy ensemble",  f1: 73.95, label: "2 ModernBERT variants, post-presentation", fake: false },
  { version: "Final locked",     f1: 75.00, label: "Calibrated ensemble — headline",        hero: true  },
];

const TAKEAWAYS = [
  {
    icon: FlaskConical,
    title: "Honesty over optics",
    text: "Publishing 59.65% when you had 88.90% on the board is uncomfortable. It is also the only scientifically defensible position. The audit became the strongest part of the project.",
  },
  {
    icon: Layers,
    title: "Every iteration taught something",
    text: "14 model versions didn't all succeed. V9 regressed. V11 was killed. V3 showed cascade error propagation. Those failures informed every subsequent design choice.",
  },
  {
    icon: Rocket,
    title: "Methodology is the product",
    text: "The project's value isn't the final F1. It's the leakage documentation, the GECS anchor contribution, the calibration audit, and the cross-validation discipline — work another team won't have done.",
  },
];

export default function Journey() {
  return (
    <section className="relative min-h-screen overflow-hidden bg-black text-white">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute inset-0 opacity-40" style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px)",
          backgroundSize: "72px 72px",
        }} />
        <div className="absolute -top-24 left-[12%] h-[28rem] w-[28rem] rounded-full bg-red-700/18 blur-[140px]" />
        <div className="absolute top-[28rem] right-[8%] h-[30rem] w-[30rem] rounded-full bg-cyan-500/12 blur-[160px]" />
        <div className="absolute bottom-[-8rem] left-[28%] h-[24rem] w-[24rem] rounded-full bg-emerald-500/10 blur-[140px]" />
      </div>

      <div className="relative z-10 px-6 py-20 md:py-28">
        <div className="mx-auto max-w-7xl">

          {/* Hero header */}
          <motion.div
            initial={{ opacity: 0, y: 28 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7 }}
            className="grid gap-12 lg:grid-cols-[1.15fr_0.85fr] lg:items-end"
          >
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-red-500/20 bg-red-500/10 px-4 py-2 text-xs uppercase tracking-[0.32em] text-red-300">
                <span className="h-2 w-2 rounded-full bg-red-400" />
                Journey Page
              </div>

              <div className="mt-8 mb-6">
                <RevealText
                  text="JOURNEY"
                  textColor="text-white"
                  overlayColor="text-red-500"
                  fontSize="text-[60px] sm:text-[96px] lg:text-[132px]"
                  letterDelay={0.06}
                  overlayDelay={0.035}
                />
              </div>

              <h1 className="max-w-4xl text-3xl sm:text-5xl lg:text-6xl font-black tracking-tight leading-[0.96]">
                From 88.90% that was fake
                <span className="block text-white/55">to 75.0% that was earned.</span>
              </h1>

              <p className="mt-6 max-w-3xl text-lg sm:text-xl leading-relaxed text-white/58">
                Eight phases, fourteen model versions, one leakage audit, a novel taxonomy-grounding
                contribution, and the discipline to report cross-validated numbers instead of test-set-tuned ones.
              </p>

              <div className="mt-10 flex flex-wrap gap-3">
                <Link
                  href="/about"
                  className="inline-flex items-center gap-2 rounded-2xl bg-white px-5 py-3 text-sm font-semibold text-black hover:bg-red-50 transition-colors"
                >
                  Project page
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  href="/team"
                  className="inline-flex items-center gap-2 rounded-2xl border border-white/15 px-5 py-3 text-sm font-semibold text-white/78 hover:text-white hover:border-white/25 transition-colors"
                >
                  Meet the team
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            </div>

            <GlowCard glowColor="cyan" className="border-white/8 bg-white/[0.03] p-0 overflow-hidden">
              <div className="border-b border-white/8 px-6 py-5">
                <TextScramble
                  as="p"
                  speed={0.02}
                  duration={0.9}
                  className="text-xs uppercase tracking-[0.3em] text-cyan-300/85"
                >
                  The numbers, honestly
                </TextScramble>
                <h2 className="mt-3 text-2xl font-bold text-white">The project never moved in a straight line.</h2>
              </div>

              <div className="grid grid-cols-2 gap-px bg-white/8">
                {STATS.map((stat) => (
                  <div key={stat.label} className="bg-black/65 px-6 py-6">
                    <div className="text-xs uppercase tracking-[0.28em] text-white/35">{stat.label}</div>
                    <div className="mt-3 text-2xl sm:text-3xl font-black text-white">{stat.value}</div>
                  </div>
                ))}
              </div>

              <div className="px-6 py-6 text-sm leading-relaxed text-white/52">
                The goal was not to report the highest number. It was to report the right number — one that would survive on data the model had never seen.
              </div>
            </GlowCard>
          </motion.div>

          {/* Takeaways */}
          <div className="mt-20 grid gap-4 md:grid-cols-3">
            {TAKEAWAYS.map((item, index) => (
              <motion.div
                key={item.title}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-120px" }}
                transition={{ duration: 0.55, delay: index * 0.08 }}
                className="rounded-[28px] border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl"
              >
                <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-2xl border border-white/10 bg-white/5">
                  <item.icon className="h-5 w-5 text-white/80" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">{item.title}</h3>
                <p className="text-white/55 leading-relaxed">{item.text}</p>
              </motion.div>
            ))}
          </div>

          {/* Model leaderboard */}
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.6 }}
            className="mt-24"
          >
            <div className="mb-8">
              <TextScramble
                as="p"
                speed={0.018}
                duration={0.8}
                className="text-xs uppercase tracking-[0.32em] text-amber-400/80 mb-4"
              >
                Model leaderboard — honest progression
              </TextScramble>
              <h2 className="text-3xl sm:text-5xl font-black tracking-tight">
                Every number we actually hit.
              </h2>
            </div>

            <GlowCard glowColor="amber" className="border-white/8 bg-black/40 p-6">
              <div className="space-y-3">
                {LEADERBOARD.map((row) => {
                  const pct = row.f1;
                  const maxPct = 88.90;
                  const barWidth = (pct / maxPct) * 100;
                  return (
                    <motion.div
                      key={row.version}
                      initial={{ opacity: 0, x: -16 }}
                      whileInView={{ opacity: 1, x: 0 }}
                      viewport={{ once: true }}
                      className={`flex items-center gap-3 rounded-xl px-4 py-3 ${
                        row.hero
                          ? "border border-emerald-500/30 bg-emerald-500/8"
                          : row.fake
                          ? "border border-red-500/20 bg-red-500/5"
                          : "border border-white/6 bg-white/[0.02]"
                      }`}
                    >
                      <div className="w-36 flex-shrink-0">
                        <div className={`text-xs font-mono font-bold ${
                          row.hero ? "text-emerald-300" : row.fake ? "text-red-400" : "text-white/60"
                        }`}>
                          {row.version}
                        </div>
                      </div>
                      <div className="flex-1 h-4 rounded bg-white/5 overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          whileInView={{ width: `${barWidth}%` }}
                          viewport={{ once: true }}
                          transition={{ duration: 1.0, ease: [0.22, 1, 0.36, 1] }}
                          className={`h-full rounded ${
                            row.hero
                              ? "bg-gradient-to-r from-emerald-500 to-teal-400 shadow-[0_0_10px_rgba(16,185,129,0.4)]"
                              : row.fake
                              ? "bg-gradient-to-r from-red-600/60 to-red-400/40"
                              : "bg-gradient-to-r from-white/20 to-white/10"
                          }`}
                        />
                      </div>
                      <div className={`w-14 text-right text-sm font-mono font-bold flex-shrink-0 ${
                        row.hero ? "text-emerald-300" : row.fake ? "text-red-400 line-through" : "text-white/50"
                      }`}>
                        {pct.toFixed(2)}%
                      </div>
                      <div className="hidden sm:block text-xs text-white/30 flex-shrink-0 w-56">{row.label}</div>
                    </motion.div>
                  );
                })}
              </div>
              <div className="mt-5 pt-4 border-t border-white/6 text-xs text-white/25">
                The red bar (88.90%) is crossed out because it was generated from memorized test data. Every other number above was earned on rows the model had never seen.
              </div>
            </GlowCard>
          </motion.div>

          {/* Phase section header */}
          <div className="mt-24 mb-10 flex items-end justify-between gap-6">
            <div>
              <TextScramble
                as="p"
                speed={0.018}
                duration={0.8}
                className="text-xs uppercase tracking-[0.32em] text-red-400/80 mb-4"
              >
                Eight decisive phases
              </TextScramble>
              <h2 className="text-3xl sm:text-5xl font-black tracking-tight">
                Not a timeline. A pressure chamber.
              </h2>
            </div>
          </div>

          {/* Phases */}
          <div className="space-y-8">
            {PHASES.map((phase, index) => (
              <motion.div
                key={phase.number}
                initial={{ opacity: 0, y: 28 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-120px" }}
                transition={{ duration: 0.6, delay: index * 0.04 }}
                className="grid gap-6 lg:grid-cols-[0.32fr_0.68fr]"
              >
                <div className="lg:sticky lg:top-28 lg:h-fit">
                  <div className="rounded-[28px] border border-white/10 bg-black/35 p-6">
                    <div className="text-xs uppercase tracking-[0.3em] text-white/35">Phase {phase.number}</div>
                    <div className="mt-4 flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-white/5">
                      <phase.icon className="h-6 w-6 text-white/78" />
                    </div>
                    <div className="mt-5 text-sm uppercase tracking-[0.28em] text-red-300/80">{phase.eyebrow}</div>
                    <div className="mt-4 text-sm leading-relaxed text-white/45">{phase.impact}</div>
                  </div>
                </div>

                <GlowCard glowColor={phase.glow} className="border-white/8 bg-white/[0.03] p-0 overflow-hidden">
                  <div className="border-b border-white/8 px-7 py-6">
                    <div className="text-xs uppercase tracking-[0.3em] text-white/35 mb-3">Phase {phase.number}</div>
                    <h3 className="text-2xl sm:text-3xl font-bold tracking-tight text-white max-w-3xl">
                      {phase.title}
                    </h3>
                  </div>

                  <div className="grid gap-px bg-white/8 lg:grid-cols-[1fr_0.32fr]">
                    <div className="bg-black/65 px-7 py-7">
                      <p className="text-lg leading-8 text-white/58">{phase.description}</p>
                    </div>
                    <div className="bg-black/55 px-6 py-7">
                      <div className="text-[11px] uppercase tracking-[0.28em] text-white/32">Net effect</div>
                      <p className="mt-4 text-sm leading-7 text-white/55">{phase.impact}</p>
                    </div>
                  </div>
                </GlowCard>
              </motion.div>
            ))}
          </div>

          {/* Final decision wall */}
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-120px" }}
            transition={{ duration: 0.65 }}
            className="mt-24"
          >
            <div className="mb-8">
              <TextScramble
                as="p"
                speed={0.018}
                duration={0.8}
                className="text-xs uppercase tracking-[0.32em] text-emerald-300/80 mb-4"
              >
                Final decision wall
              </TextScramble>
              <h2 className="text-3xl sm:text-5xl font-black tracking-tight">
                The reported number is the honest number.
                <span className="block text-white/55">Not the highest one we saw on test.</span>
              </h2>
            </div>

            <div className="grid gap-6 lg:grid-cols-3">
              <GlowCard glowColor="emerald" className="border-white/8 bg-emerald-500/[0.06]">
                <div className="text-xs uppercase tracking-[0.28em] text-emerald-300/75 mb-4">Headline result</div>
                <h3 className="text-2xl font-black text-white mb-4">Calibrated Ensemble</h3>
                <div className="text-5xl font-black text-white mb-1">75.0%</div>
                <div className="text-sm text-emerald-400 font-semibold mb-5">Task 1 · calibrated · disclosed</div>
                <p className="text-white/58 leading-7 text-sm">
                  Greedy ensemble of the two strongest ModernBERT-large variants, with light
                  temperature calibration (τ=0.2). Top-3 accuracy: 91.4%. Top-5 accuracy: 95.3%.
                  This is the number that survived cross-validation.
                </p>
              </GlowCard>

              <GlowCard glowColor="amber" className="border-white/8 bg-white/[0.03]">
                <div className="text-xs uppercase tracking-[0.28em] text-amber-300/75 mb-4">Test-tuned upper bound</div>
                <h3 className="text-2xl font-black text-white mb-4">Per-class calibration</h3>
                <div className="text-5xl font-black text-white mb-1">77.51%</div>
                <div className="text-sm text-amber-400 font-semibold mb-5">Not the headline · explained in methods</div>
                <p className="text-white/58 leading-7 text-sm">
                  145 free calibration parameters optimized on the test set produced 77.51%. Five-fold
                  cross-validation brought it back to 73.96% — essentially no lift. Reported as the
                  upper bound with full disclosure, not as the headline.
                </p>
              </GlowCard>

              <GlowCard glowColor="red" className="border-white/8 bg-white/[0.03]">
                <div className="text-xs uppercase tracking-[0.28em] text-red-300/75 mb-4">The structural ceiling</div>
                <h3 className="text-2xl font-black text-white mb-4">Conglomerate wall</h3>
                <div className="text-5xl font-black text-white mb-1">~76%</div>
                <div className="text-sm text-red-400 font-semibold mb-5">Data-bound, not model-bound</div>
                <p className="text-white/58 leading-7 text-sm">
                  55.2% of training rows have inherent label ambiguity: same LongProfile text,
                  different codes per conglomerate segment. A perfect classifier on single-code
                  companies plus 60% on multi-code mathematically caps Macro F1 near 76%.
                </p>
              </GlowCard>
            </div>

            <div className="mt-8 rounded-[28px] border border-white/10 bg-white/[0.03] p-8">
              <div className="flex items-start gap-4">
                <CheckCircle2 className="h-6 w-6 text-emerald-400 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="text-xl font-bold text-white mb-3">What this project actually produced</h3>
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 text-sm text-white/55 leading-relaxed">
                    <div className="rounded-xl border border-white/8 bg-black/30 px-4 py-3">
                      A complete leakage audit documenting the 88.90% contamination with reproduction steps
                    </div>
                    <div className="rounded-xl border border-white/8 bg-black/30 px-4 py-3">
                      An honest evaluation pipeline with company-disjoint splits — a methodology other teams won&apos;t have
                    </div>
                    <div className="rounded-xl border border-white/8 bg-black/30 px-4 py-3">
                      14 documented model variants with reproducible training scripts across classical and transformer approaches
                    </div>
                    <div className="rounded-xl border border-white/8 bg-black/30 px-4 py-3">
                      GECS Official Taxonomy Anchoring — 580 features derived from Morningstar&apos;s own definition document
                    </div>
                    <div className="rounded-xl border border-white/8 bg-black/30 px-4 py-3">
                      A calibration audit with cross-validation discipline — the test-tuned 77.51% was audited and excluded from the headline
                    </div>
                    <div className="rounded-xl border border-white/8 bg-black/30 px-4 py-3">
                      75.0% macro F1 / 91.4% top-3 accuracy — a result that generalizes, not one that impresses only on test data
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>

          {/* CTA */}
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="mt-20 pt-12 border-t border-white/8 flex flex-wrap items-center justify-center gap-4"
          >
            <Link
              href="/demo"
              className="inline-flex items-center gap-2 rounded-2xl bg-red-600 px-6 py-3.5 text-sm font-bold text-white hover:bg-red-500 transition-colors"
            >
              Try the live classifier
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/hf"
              className="inline-flex items-center gap-2 rounded-2xl border border-white/15 px-6 py-3.5 text-sm font-semibold text-white/78 hover:text-white hover:border-white/25 transition-colors"
            >
              HF Space demo
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/team"
              className="inline-flex items-center gap-2 rounded-2xl border border-white/15 px-6 py-3.5 text-sm font-semibold text-white/78 hover:text-white hover:border-white/25 transition-colors"
            >
              Meet the team
              <ArrowRight className="h-4 w-4" />
            </Link>
          </motion.div>

        </div>
      </div>
    </section>
  );
}
