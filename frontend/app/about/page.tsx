import Link from "next/link";
import {
  ArrowRight,
  BrainCircuit,
  Database,
  GitBranch,
  LayoutDashboard,
  Rocket,
  Scale,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import Navigation from "@/components/Navigation";

const STACK = [
  { label: "Dataset frame", value: "Morningstar company and segment descriptions" },
  { label: "Vectorization", value: "TF-IDF with 50K sparse features" },
  { label: "Primary model", value: "Linear SVM with balanced class weighting" },
  { label: "LLM track", value: "DeBERTa-v3-small fine-tuning experiments" },
  { label: "SVM host", value: "Flask on Railway" },
  { label: "LLM host", value: "Hugging Face Spaces" },
  { label: "Frontend", value: "Next.js 15 on Vercel" },
  { label: "Reusable library", value: "breezeml" },
];

const ARCHITECTURE = [
  {
    icon: Database,
    title: "Data to features",
    desc: "Raw Morningstar text is cleaned, normalized, and transformed into sparse numerical features that the production model can score efficiently.",
  },
  {
    icon: BrainCircuit,
    title: "Models under pressure",
    desc: "Classical ML and transformer-based experiments were both tested against real imbalance, deployment cost, and interpretability needs.",
  },
  {
    icon: LayoutDashboard,
    title: "Product surface",
    desc: "The frontend is not only a report. It acts like a control room for the system narrative, prediction flow, and deployment story.",
  },
];

const TEAM = [
  { name: "Akash Anipakalu Giridhar", role: "ML engineering and library architecture" },
  { name: "Subasree Segar", role: "Data science and model evaluation" },
  { name: "Vishal Shaileshkumar Rathod", role: "Feature engineering" },
  { name: "Srilaxmi Ganjipalli", role: "Data exploration and preprocessing" },
  { name: "Tserennadmid Batkhuu", role: "Reporting and documentation" },
];

export default function AboutPage() {
  return (
    <main className="min-h-screen bg-black text-white">
      <Navigation />

      <section className="relative overflow-hidden px-6 pt-36 pb-20">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-8 left-[10%] h-72 w-72 rounded-full bg-red-600/14 blur-[120px]" />
          <div className="absolute top-40 right-[8%] h-80 w-80 rounded-full bg-cyan-500/10 blur-[140px]" />
          <div className="absolute inset-0 opacity-25" style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px)",
            backgroundSize: "68px 68px",
          }} />
        </div>

        <div className="relative mx-auto max-w-7xl">
          <div className="grid gap-10 lg:grid-cols-[1.1fr_0.9fr] lg:items-end">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-red-500/20 bg-red-500/10 px-4 py-2 text-xs uppercase tracking-[0.3em] text-red-300">
                <Sparkles className="h-3.5 w-3.5" />
                Project Page
              </div>
              <h1 className="mt-6 text-5xl sm:text-6xl lg:text-7xl font-black tracking-tight">
                This capstone became a
                <span className="block text-white/55">production-minded classification system.</span>
              </h1>
              <p className="mt-6 max-w-3xl text-lg sm:text-xl leading-relaxed text-white/55">
                TAVSS is the full story: raw financial text, feature engineering, model experiments,
                deployment tradeoffs, and the evidence that a classical sparse pipeline beat the louder deep-learning route.
              </p>
              <div className="mt-10 flex flex-wrap gap-3">
                <Link
                  href="/journey"
                  className="inline-flex items-center gap-2 rounded-2xl bg-white px-5 py-3 text-sm font-semibold text-black hover:bg-red-50 transition-colors"
                >
                  Read the journey
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

            <div className="rounded-[32px] border border-white/10 bg-white/[0.04] backdrop-blur-xl overflow-hidden">
              <div className="border-b border-white/8 px-6 py-5">
                <div className="text-xs uppercase tracking-[0.28em] text-cyan-300/80 mb-2">Executive snapshot</div>
                <h2 className="text-2xl font-bold text-white">Why this project matters</h2>
              </div>
              <div className="grid grid-cols-2 gap-px bg-white/8">
                <div className="bg-black/65 px-6 py-6">
                  <div className="text-xs uppercase tracking-[0.24em] text-white/35">Industry classes</div>
                  <div className="mt-2 text-3xl font-black text-white">145</div>
                </div>
                <div className="bg-black/65 px-6 py-6">
                  <div className="text-xs uppercase tracking-[0.24em] text-white/35">Subindustries</div>
                  <div className="mt-2 text-3xl font-black text-white">450+</div>
                </div>
                <div className="bg-black/65 px-6 py-6">
                  <div className="text-xs uppercase tracking-[0.24em] text-white/35">Winning metric</div>
                  <div className="mt-2 text-3xl font-black text-white">86.82%</div>
                </div>
                <div className="bg-black/65 px-6 py-6">
                  <div className="text-xs uppercase tracking-[0.24em] text-white/35">Operating thesis</div>
                  <div className="mt-2 text-base font-semibold text-white">Simple, fast, explainable</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="px-6 py-20 border-t border-white/6">
        <div className="mx-auto max-w-7xl">
          <div className="mb-12">
            <div className="text-xs uppercase tracking-[0.3em] text-red-300/80 mb-4">System architecture</div>
            <h2 className="text-3xl sm:text-5xl font-black tracking-tight">Built like a serious pipeline, not a class demo.</h2>
          </div>
          <div className="grid gap-5 md:grid-cols-3">
            {ARCHITECTURE.map((item) => (
              <div key={item.title} className="rounded-[28px] border border-white/10 bg-white/[0.03] p-6">
                <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-2xl border border-white/10 bg-white/5">
                  <item.icon className="h-5 w-5 text-white/80" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">{item.title}</h3>
                <p className="text-white/55 leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="px-6 py-20 border-t border-white/6">
        <div className="mx-auto max-w-7xl">
          <div className="mb-12">
            <div className="text-xs uppercase tracking-[0.3em] text-cyan-300/80 mb-4">Stack map</div>
            <h2 className="text-3xl sm:text-5xl font-black tracking-tight">Every layer has a job.</h2>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {STACK.map((item) => (
              <div key={item.label} className="rounded-2xl border border-white/10 bg-black/35 px-5 py-5">
                <div className="text-xs uppercase tracking-[0.24em] text-white/35 mb-2">{item.label}</div>
                <div className="text-sm leading-relaxed text-white">{item.value}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="px-6 py-20 border-t border-white/6">
        <div className="mx-auto max-w-7xl">
          <div className="mb-12">
            <div className="text-xs uppercase tracking-[0.3em] text-emerald-300/80 mb-4">Model decision wall</div>
            <h2 className="text-3xl sm:text-5xl font-black tracking-tight">
              The final choice was not about trendiness.
              <span className="block text-white/55">It was about operational proof.</span>
            </h2>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <div className="rounded-[32px] border border-emerald-500/20 bg-emerald-500/[0.06] p-8">
              <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs uppercase tracking-[0.24em] text-emerald-300">
                <ShieldCheck className="h-3.5 w-3.5" />
                Production winner
              </div>
              <h3 className="text-3xl font-black text-white mb-3">TF-IDF + Linear SVM</h3>
              <div className="text-5xl font-black text-white mb-6">86.82%</div>
              <p className="text-white/58 leading-8 mb-6">
                It delivered better macro performance, lower serving friction, easier reasoning, and a cleaner path to real deployment.
                The winning system was not the one with the most attention layers. It was the one that solved the task better.
              </p>
              <div className="flex items-center gap-2 text-sm text-emerald-300/90">
                <Rocket className="h-4 w-4" />
                Faster to host, easier to trust, better aligned with the problem.
              </div>
            </div>

            <div className="rounded-[32px] border border-purple-500/20 bg-white/[0.03] p-8">
              <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-purple-500/20 bg-purple-500/10 px-3 py-1 text-xs uppercase tracking-[0.24em] text-purple-300">
                <Scale className="h-3.5 w-3.5" />
                Valuable challenger
              </div>
              <h3 className="text-3xl font-black text-white mb-3">DeBERTa-v3 Small</h3>
              <div className="text-5xl font-black text-white mb-6">64.00%</div>
              <p className="text-white/58 leading-8 mb-6">
                The transformer track still mattered. It taught the team how to handle compute ceilings, class imbalance,
                augmentation strategy, and model-hosting pressure. But in the final ledger, it did not outperform the sparse baseline.
              </p>
              <div className="flex items-center gap-2 text-sm text-purple-300/90">
                <GitBranch className="h-4 w-4" />
                Important experiment, but not the final production answer.
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="px-6 py-20 border-t border-white/6">
        <div className="mx-auto max-w-7xl">
          <div className="mb-12">
            <div className="text-xs uppercase tracking-[0.3em] text-rose-300/80 mb-4">Who built it</div>
            <h2 className="text-3xl sm:text-5xl font-black tracking-tight">A five-person systems team.</h2>
          </div>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {TEAM.map((member) => (
              <div key={member.name} className="rounded-[28px] border border-white/10 bg-white/[0.03] p-6">
                <div className="text-lg font-semibold text-white mb-2">{member.name}</div>
                <div className="text-sm uppercase tracking-[0.24em] text-white/35 mb-3">{member.role}</div>
                <div className="text-sm text-white/55">
                  The project only works because each role fed into the same end-to-end system.
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="px-6 py-20 border-t border-white/6">
        <div className="mx-auto max-w-6xl text-center">
          <div className="text-sm text-white/40 mb-6">Want the full narrative or the people behind it?</div>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <Link
              href="/journey"
              className="inline-flex items-center gap-2 rounded-2xl bg-red-600 px-6 py-3.5 text-sm font-bold text-white hover:bg-red-500 transition-colors"
            >
              Open journey page
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/team"
              className="inline-flex items-center gap-2 rounded-2xl border border-white/15 px-6 py-3.5 text-sm font-bold text-white/80 hover:text-white hover:border-white/25 transition-colors"
            >
              Open team page
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
