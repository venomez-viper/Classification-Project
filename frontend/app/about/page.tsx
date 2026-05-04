import Navigation from "@/components/Navigation";
import HowItWorks from "@/components/HowItWorks";
import Link from "next/link";
import {
  ArrowRight, CheckCircle2, GitBranch, Rocket, Scale,
  Database, BrainCircuit, LayoutDashboard,
} from "lucide-react";

const STACK = [
  { label: "Text vectorization",  value: "TF-IDF · 60,000 bigram features · scipy.sparse CSR" },
  { label: "Cascade classifier",  value: "LinearSVC (scikit-learn) · class_weight='balanced'" },
  { label: "LLM track",           value: "DeBERTa-v3-small fine-tuned on RTX 3050" },
  { label: "ML library",          value: "breezeml (our open-source wrapper)" },
  { label: "SVM API server",      value: "Flask + Waitress → Railway (Docker)" },
  { label: "LLM API server",      value: "Flask + PyTorch → Hugging Face Spaces" },
  { label: "Frontend",            value: "Next.js 15 + Tailwind CSS → Vercel" },
  { label: "Taxonomy data",       value: "Morningstar GECS + GICS / NAICS / SIC crosswalk" },
];

const TEAM = [
  { name: "Akash Anipakalu Giridhar",   role: "ML engineering, cascade architecture, deployment" },
  { name: "Subasree Segar",             role: "Model evaluation, benchmarking, per-class diagnostics" },
  { name: "Vishal Shaileshkumar Rathod",role: "Feature engineering, TF-IDF pipeline" },
  { name: "Srilaxmi Ganjipalli",        role: "Data preprocessing, exploration, cleaning" },
  { name: "Tserennadmid Batkhuu",       role: "Documentation, reporting, project coordination" },
];

const ARCHITECTURE = [
  { icon: Database,       title: "Data → features", desc: "Raw Morningstar descriptions cleaned and converted to 60K-dimensional sparse TF-IDF vectors. No dense matrices — scipy CSR throughout." },
  { icon: BrainCircuit,   title: "Cascade inference", desc: "4-level LinearSVC chain reads the taxonomy hierarchy. Each level only competes within its parent's slice — not against all 145 codes at once." },
  { icon: LayoutDashboard, title: "Production surface", desc: "Flask API on Railway serves predictions in under 10 ms. Next.js frontend on Vercel. DeBERTa comparison on Hugging Face Spaces." },
];

export default function AboutPage() {
  return (
    <main className="min-h-screen bg-black text-white">
      <Navigation />

      {/* ── Hero ── */}
      <section className="relative overflow-hidden px-6 pt-36 pb-12">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-8 left-[10%] h-72 w-72 rounded-full bg-red-600/12 blur-[120px]" />
          <div className="absolute top-40 right-[8%] h-80 w-80 rounded-full bg-violet-500/10 blur-[140px]" />
          <div className="absolute inset-0 opacity-20" style={{
            backgroundImage: "linear-gradient(rgba(255,255,255,0.05) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.05) 1px,transparent 1px)",
            backgroundSize: "68px 68px",
          }} />
        </div>

        <div className="relative mx-auto max-w-7xl">
          <div className="grid gap-10 lg:grid-cols-[1.1fr_0.9fr] lg:items-start">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-red-500/20 bg-red-500/10 px-4 py-2 text-xs uppercase tracking-[0.3em] text-red-300 mb-6">
                MGT 599 Capstone · Group 4 · DePaul University
              </div>
              <h1 className="text-5xl sm:text-6xl lg:text-7xl font-black tracking-tight leading-[0.95]">
                We automated how<br />
                <span className="text-white/50">Morningstar classifies</span><br />
                the equity universe.
              </h1>
              <p className="mt-6 max-w-2xl text-lg sm:text-xl leading-relaxed text-white/55">
                TAVSS is a 4-level cascade classifier that reads a company description and
                assigns a Morningstar GECS industry code — beating a fine-tuned transformer
                by <span className="text-emerald-400 font-bold">+24.90 percentage points</span>, on CPU, with no GPU required.
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <Link href="/demo"
                  className="inline-flex items-center gap-2 rounded-2xl bg-white px-5 py-3 text-sm font-bold text-black hover:bg-red-50 transition-colors">
                  Try the live demo <ArrowRight className="h-4 w-4" />
                </Link>
                <Link href="/journey"
                  className="inline-flex items-center gap-2 rounded-2xl border border-white/15 px-5 py-3 text-sm font-semibold text-white/78 hover:text-white hover:border-white/25 transition-colors">
                  Read the journey <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            </div>

            {/* Key numbers */}
            <div className="grid grid-cols-2 gap-3">
              {[
                { v: "88.90%", l: "Task 1 Macro F1",    s: "145 GECS industry codes",     c: "text-red-400",     b: "border-red-500/20 bg-red-500/5" },
                { v: "55.41%", l: "Task 2 Macro F1",    s: "428 sub-industry codes",       c: "text-blue-400",    b: "border-blue-500/20 bg-blue-500/5" },
                { v: "+24.9pp",l: "vs DeBERTa",         s: "fine-tuned transformer",        c: "text-emerald-400", b: "border-emerald-500/20 bg-emerald-500/5" },
                { v: "40×",    l: "Faster than DeBERTa",s: "CPU · no GPU required",         c: "text-violet-400",  b: "border-violet-500/20 bg-violet-500/5" },
                { v: "53K+",   l: "Training segments",  s: "Morningstar company data",      c: "text-amber-400",   b: "border-amber-500/20 bg-amber-500/5" },
                { v: "60K",    l: "TF-IDF features",    s: "bigram sparse vectorization",   c: "text-cyan-400",    b: "border-cyan-500/20 bg-cyan-500/5" },
              ].map((s) => (
                <div key={s.l} className={`rounded-2xl border ${s.b} px-5 py-4`}>
                  <div className={`text-2xl font-black ${s.c} mb-1`}>{s.v}</div>
                  <div className="text-sm font-semibold text-white">{s.l}</div>
                  <div className="text-xs text-white/35 mt-0.5">{s.s}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── How it works (cascade explainer) ── */}
      <div className="border-t border-white/6">
        <HowItWorks />
      </div>

      {/* ── System architecture ── */}
      <section className="px-6 py-20 border-t border-white/6">
        <div className="mx-auto max-w-7xl">
          <div className="mb-10">
            <div className="text-xs uppercase tracking-[0.3em] text-red-300/80 mb-4">System architecture</div>
            <h2 className="text-3xl sm:text-4xl font-black tracking-tight">
              Built like a real production pipeline.
            </h2>
          </div>
          <div className="grid gap-5 md:grid-cols-3">
            {ARCHITECTURE.map((item) => (
              <div key={item.title} className="rounded-[28px] border border-white/10 bg-white/[0.03] p-6">
                <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-2xl border border-white/10 bg-white/5">
                  <item.icon className="h-5 w-5 text-white/80" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">{item.title}</h3>
                <p className="text-white/50 leading-relaxed text-sm">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Model decision ── */}
      <section className="px-6 py-20 border-t border-white/6">
        <div className="mx-auto max-w-7xl">
          <div className="mb-10">
            <div className="text-xs uppercase tracking-[0.3em] text-emerald-300/80 mb-4">Model decision</div>
            <h2 className="text-3xl sm:text-4xl font-black tracking-tight">
              The cascade SVM won. The evidence was clear.
            </h2>
          </div>
          <div className="grid gap-6 lg:grid-cols-2">
            <div className="rounded-[32px] border border-emerald-500/20 bg-emerald-500/[0.05] p-8">
              <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs uppercase tracking-[0.24em] text-emerald-300">
                <CheckCircle2 className="h-3.5 w-3.5" /> Production winner
              </div>
              <h3 className="text-3xl font-black text-white mb-2">4-Level Cascade SVM</h3>
              <div className="text-5xl font-black text-white mb-1">88.90%</div>
              <div className="text-sm text-emerald-400 font-semibold mb-5">+13.90 pp over rubric threshold of 75%</div>
              <p className="text-white/55 leading-8 mb-5 text-sm">
                Sector → Group → Industry → Sub-Industry. Each classifier trains only on its slice of the taxonomy.
                Runs on CPU, deploys in a Docker container, serves predictions in under 10 ms.
                Task 2 adds 428 sub-industry classes at 55.41% Macro F1.
              </p>
              <div className="flex items-center gap-2 text-sm text-emerald-300/90">
                <Rocket className="h-4 w-4" /> Fast, explainable, no GPU required.
              </div>
            </div>
            <div className="rounded-[32px] border border-purple-500/20 bg-white/[0.03] p-8">
              <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-purple-500/20 bg-purple-500/10 px-3 py-1 text-xs uppercase tracking-[0.24em] text-purple-300">
                <Scale className="h-3.5 w-3.5" /> Valuable challenger
              </div>
              <h3 className="text-3xl font-black text-white mb-2">DeBERTa-v3 Small</h3>
              <div className="text-5xl font-black text-white mb-1">64.00%</div>
              <div className="text-sm text-purple-400 font-semibold mb-5">−24.90 pp vs cascade · GPU required</div>
              <p className="text-white/55 leading-8 mb-5 text-sm">
                Fine-tuned on the same data with class-weighted loss. Proved the training approach
                was sound — but didn't outperform the classical pipeline on Macro F1.
                3+ hour training epochs on an RTX 3050 with 4 GB VRAM.
              </p>
              <div className="flex items-center gap-2 text-sm text-purple-300/90">
                <GitBranch className="h-4 w-4" /> Important experiment, not the production answer.
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Tech stack ── */}
      <section className="px-6 py-20 border-t border-white/6">
        <div className="mx-auto max-w-7xl">
          <div className="mb-10">
            <div className="text-xs uppercase tracking-[0.3em] text-cyan-300/80 mb-4">Tech stack</div>
            <h2 className="text-3xl sm:text-4xl font-black tracking-tight">Every layer has a job.</h2>
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

      {/* ── Team ── */}
      <section className="px-6 py-20 border-t border-white/6">
        <div className="mx-auto max-w-7xl">
          <div className="mb-10">
            <div className="text-xs uppercase tracking-[0.3em] text-rose-300/80 mb-4">The team</div>
            <h2 className="text-3xl sm:text-4xl font-black tracking-tight">Five people. One finished system.</h2>
          </div>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {TEAM.map((member) => (
              <div key={member.name} className="rounded-[28px] border border-white/10 bg-white/[0.03] p-6">
                <div className="text-lg font-semibold text-white mb-2">{member.name}</div>
                <div className="text-sm text-white/40 leading-relaxed">{member.role}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="px-6 py-16 border-t border-white/6">
        <div className="mx-auto max-w-4xl text-center">
          <h2 className="text-2xl font-black text-white mb-6">Ready to see it in action?</h2>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <Link href="/demo"
              className="inline-flex items-center gap-2 rounded-2xl bg-red-600 px-6 py-3.5 text-sm font-bold text-white hover:bg-red-500 transition-colors">
              Run a live classification <ArrowRight className="h-4 w-4" />
            </Link>
            <Link href="/llm"
              className="inline-flex items-center gap-2 rounded-2xl border border-white/15 px-6 py-3.5 text-sm font-bold text-white/80 hover:text-white hover:border-white/25 transition-colors">
              Compare with DeBERTa <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>

      <footer className="border-t border-white/6 py-8 text-center text-xs text-white/20">
        © 2026 TAVSS · MGT 599 Capstone · Group 4 · DePaul University Chicago
      </footer>
    </main>
  );
}
