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
  Rocket,
  ServerCrash,
  Wrench,
} from "lucide-react";
import { GlowCard } from "@/components/ui/spotlight-card";
import { RevealText } from "@/components/ui/reveal-text";
import { TextScramble } from "@/components/ui/text-scramble";

const STATS = [
  { label: "Rows touched", value: "42K+" },
  { label: "Training ceiling", value: "1+ hour epochs" },
  { label: "GPU reality", value: "RTX 3050 / 4GB" },
  { label: "Final decision", value: "SVM wins" },
];

const PHASES = [
  {
    number: "01",
    eyebrow: "Infrastructure shock",
    icon: ServerCrash,
    title: "Colab looked convenient until the workload hit back.",
    description:
      "The original DeBERTa plan started in Google Colab, but the dataset volume and sequence length pushed epoch times past one hour. Sessions died before the model could settle, so the architecture decision was no longer theoretical. We had to move fast and re-own the training environment.",
    impact: "Cloud convenience broke before the experiment matured.",
    glow: "red" as const,
  },
  {
    number: "02",
    eyebrow: "Compute discipline",
    icon: Cpu,
    title: "A local Windows GPU became the lab, with almost no room for waste.",
    description:
      "Training moved onto a single RTX 3050 with 4GB of VRAM. That forced gradient accumulation, tighter batch behavior, and aggressive memory cleanup. The pipeline became less glamorous and much more deliberate, which ended up being exactly what the project needed.",
    impact: "Every batch became an engineering choice, not a default setting.",
    glow: "blue" as const,
  },
  {
    number: "03",
    eyebrow: "Truth in the labels",
    icon: AlertTriangle,
    title: "The real enemy was not tooling. It was class imbalance.",
    description:
      "The model kept collapsing toward dominant classes because the label distribution was brutally uneven. Some industries had deep coverage, while others barely existed. Macro F1 exposed the problem immediately: accuracy theater was easy, balanced performance was not.",
    impact: "The neural network learned the majority too quickly and the edge cases barely at all.",
    glow: "amber" as const,
  },
  {
    number: "04",
    eyebrow: "Intervention mode",
    icon: Wrench,
    title: "We built extra data pressure instead of pretending the dataset was fair.",
    description:
      "Minority classes were expanded with generated long-form descriptions using a local flan-t5-base workflow, then reinforced with class-weighted loss. The point was not to create hype around augmentation. It was to force the model to care about rare industries it would otherwise ignore.",
    impact: "The data track became engineered, not merely collected.",
    glow: "purple" as const,
  },
  {
    number: "05",
    eyebrow: "Final verdict",
    icon: CheckCircle2,
    title: "The LLM was respectable. The cascade SVM was production-ready.",
    description:
      "DeBERTa reached 64% Macro F1, which proved the training work was real. But the 3-level cascade TF-IDF + LinearSVC pipeline reached 88.90% Macro F1 on Task 1 and 55.41% on 428 sub-industries — deployed on CPU with no GPU required. That is the kind of result that changes a project from flashy to trustworthy.",
    impact: "The cascade system won because it read the taxonomy hierarchy instead of ignoring it.",
    glow: "emerald" as const,
  },
];

const TAKEAWAYS = [
  {
    icon: DatabaseZap,
    title: "Constraint-aware engineering",
    text: "This page is about what happens when model ambition meets hardware, time, and real label imbalance.",
  },
  {
    icon: FlaskConical,
    title: "Experimentation with consequences",
    text: "Each phase changed the next one. Tooling, metrics, augmentation, and deployment all fed into the decision.",
  },
  {
    icon: Rocket,
    title: "A product-minded ending",
    text: "The journey mattered because it ended in a deployable choice, not just an interesting notebook result.",
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
                The deep-learning route was real,
                <span className="block text-white/55">but the production answer came from discipline.</span>
              </h1>

              <p className="mt-6 max-w-3xl text-lg sm:text-xl leading-relaxed text-white/58">
                This is the story of timeouts, memory ceilings, imbalance, augmentation, and the moment
                a simpler model proved stronger than the louder one.
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
                  Pressure Map
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
                The goal was not to make the most advanced-looking page in the report. It was to survive the constraints,
                keep the experiments honest, and exit with a model that deserved deployment.
              </div>
            </GlowCard>
          </motion.div>

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

          <div className="mt-24 mb-10 flex items-end justify-between gap-6">
            <div>
              <TextScramble
                as="p"
                speed={0.018}
                duration={0.8}
                className="text-xs uppercase tracking-[0.32em] text-red-400/80 mb-4"
              >
                Five decisive phases
              </TextScramble>
              <h2 className="text-3xl sm:text-5xl font-black tracking-tight">
                Not a timeline. A pressure chamber.
              </h2>
            </div>
          </div>

          <div className="space-y-8">
            {PHASES.map((phase, index) => (
              <motion.div
                key={phase.number}
                initial={{ opacity: 0, y: 28 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-120px" }}
                transition={{ duration: 0.6, delay: index * 0.05 }}
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
                The ending was not anti-LLM.
                <span className="block text-white/55">It was pro-evidence.</span>
              </h2>
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
              <GlowCard glowColor="emerald" className="border-white/8 bg-emerald-500/[0.06]">
                <div className="text-xs uppercase tracking-[0.28em] text-emerald-300/75 mb-4">Production winner</div>
                <h3 className="text-3xl font-black text-white mb-4">4-Level Cascade SVM</h3>
                <div className="text-5xl font-black text-white mb-1">88.90%</div>
                <div className="text-sm text-emerald-400 font-semibold mb-5">Task 1 · +13.90 pp over rubric threshold</div>
                <p className="text-white/58 leading-8">
                  Sector → Group → MSTAR → Sub-Industry. Reads the Morningstar taxonomy hierarchy
                  instead of flattening it. 40× faster than DeBERTa on CPU, +24.90 pp better on Macro F1.
                  Task 2 reaches 55.41% across 428 sub-industry classes.
                </p>
              </GlowCard>

              <GlowCard glowColor="purple" className="border-white/8 bg-white/[0.03]">
                <div className="text-xs uppercase tracking-[0.28em] text-purple-300/75 mb-4">Ambitious contender</div>
                <h3 className="text-3xl font-black text-white mb-4">DeBERTa-v3 Small</h3>
                <div className="text-5xl font-black text-white mb-5">64.00%</div>
                <p className="text-white/58 leading-8">
                  Valuable as an experiment, useful for learning, and proof that the team could stand up a harder stack.
                  But it did not beat the classical pipeline on the metric that actually mattered.
                </p>
              </GlowCard>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
