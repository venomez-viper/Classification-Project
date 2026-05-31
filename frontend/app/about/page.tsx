import Navigation from "@/components/Navigation";
import HowItWorks from "@/components/HowItWorks";
import Link from "next/link";
import {
  ArrowRight,
  CheckCircle2,
  Database,
  LayoutDashboard,
  Rocket,
  Scale,
  ShieldCheck,
} from "lucide-react";

const STACK = [
  { label: "Serving API", value: "Hugging Face Space (cascade SVM) + Next.js proxy on Vercel" },
  { label: "Frontend", value: "Next.js 15 + Tailwind CSS, proxying to the GECS-Sage HF Space" },
  { label: "Task 1 locked", value: "Calibrated ModernBERT-large ensemble at 75.0% Macro F1 / 91.4% top-3" },
  { label: "Task 2 cascade", value: "Constrained 428-class sub-industry classifier at 55.44% Macro F1" },
  { label: "Taxonomy data", value: "Morningstar GECS definitions with GICS, NAICS, and SIC crosswalk support" },
  { label: "Experiment track", value: "ModernBERT and Qwen notebooks run in Colab Pro+ without becoming unsupported claims" },
];

const TEAM = [
  { name: "Akash Anipakalu Giridhar", role: "ML engineering, cascade architecture, deployment" },
  { name: "Subasree Segar", role: "Model evaluation, benchmarking, per-class diagnostics" },
  { name: "Vishal Shaileshkumar Rathod", role: "Feature engineering, TF-IDF pipeline" },
  { name: "Srilaxmi Ganjipalli", role: "Data preprocessing, exploration, cleaning" },
  { name: "Tserennadmid Batkhuu", role: "Documentation, reporting, project coordination" },
];

const ARCHITECTURE = [
  { icon: Database, title: "Data to features", desc: "Company and segment text flows into sparse model features and GECS taxonomy lookups." },
  { icon: ShieldCheck, title: "Audited inference", desc: "The app does not hide the leakage correction. It separates audit history from deployable performance." },
  { icon: LayoutDashboard, title: "Product surface", desc: "The frontend shows predictions, alternatives, model version, confidence, and review-oriented traces." },
];

export default function AboutPage() {
  return (
    <main className="min-h-screen bg-black text-white">
      <Navigation />

      <section className="relative overflow-hidden px-6 pt-36 pb-16">
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
                GECS-Sage is built<br />
                <span className="text-white/50">around the audit.</span>
              </h1>
              <p className="mt-6 max-w-2xl text-lg sm:text-xl leading-relaxed text-white/55">
                We started with a flashy cascade result, found leakage, and rebuilt the product around reproducible baselines, Morningstar taxonomy grounding, and analyst review. That honesty is the point.
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

            <div className="grid grid-cols-2 gap-3">
              {[
                { v: "75.0%",  l: "Locked Task 1 F1",   s: "Calibrated ensemble · cross-validated", c: "text-red-400",    b: "border-red-500/20 bg-red-500/5" },
                { v: "55.44%", l: "Task 2 Macro F1",    s: "428 constrained classes",               c: "text-blue-400",   b: "border-blue-500/20 bg-blue-500/5" },
                { v: "88.90%", l: "Audit finding",       s: "leakage, not shipped",                  c: "text-amber-400",  b: "border-amber-500/20 bg-amber-500/5" },
                { v: "91.4%",  l: "Top-3 Accuracy",      s: "Company-disjoint test set",             c: "text-emerald-400",b: "border-emerald-500/20 bg-emerald-500/5" },
                { v: "14",     l: "Model versions",       s: "V2 honest baseline → locked ensemble", c: "text-violet-400", b: "border-violet-500/20 bg-violet-500/5" },
                { v: "97.2%",  l: "Leakage caught",       s: "Test rows memorized in V1",            c: "text-cyan-400",   b: "border-cyan-500/20 bg-cyan-500/5" },
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

      <div className="border-t border-white/6">
        <HowItWorks />
      </div>

      <section className="px-6 py-20 border-t border-white/6">
        <div className="mx-auto max-w-7xl">
          <div className="mb-10">
            <div className="text-xs uppercase tracking-[0.3em] text-red-300/80 mb-4">System architecture</div>
            <h2 className="text-3xl sm:text-4xl font-black tracking-tight">
              Built like a reviewable production pipeline.
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

      <section className="px-6 py-20 border-t border-white/6">
        <div className="mx-auto max-w-7xl">
          <div className="mb-10">
            <div className="text-xs uppercase tracking-[0.3em] text-emerald-300/80 mb-4">Model decision</div>
            <h2 className="text-3xl sm:text-4xl font-black tracking-tight">
              The cascade is useful because it is inspectable.
            </h2>
          </div>
          <div className="grid gap-6 lg:grid-cols-2">
            <div className="rounded-[32px] border border-emerald-500/20 bg-emerald-500/[0.05] p-8">
              <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs uppercase tracking-[0.24em] text-emerald-300">
                <CheckCircle2 className="h-3.5 w-3.5" /> Deployable baseline
              </div>
              <h3 className="text-3xl font-black text-white mb-2">Calibrated Ensemble</h3>
              <div className="text-5xl font-black text-white mb-1">75.0%</div>
              <div className="text-sm text-emerald-400 font-semibold mb-5">Macro F1 · 91.4% top-3 · cross-validated</div>
              <p className="text-white/55 leading-8 mb-5 text-sm">
                Greedy ensemble of two ModernBERT-large variants with temperature calibration. Trained on company-disjoint splits. The test-tuned upper bound (77.51%) is disclosed but excluded from the headline after 5-fold CV showed it generalizes to 73.96%.
              </p>
              <div className="flex items-center gap-2 text-sm text-emerald-300/90">
                <Rocket className="h-4 w-4" /> Honest, deployable, and cross-validated.
              </div>
            </div>
            <div className="rounded-[32px] border border-amber-500/20 bg-white/[0.03] p-8">
              <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-amber-500/20 bg-amber-500/10 px-3 py-1 text-xs uppercase tracking-[0.24em] text-amber-300">
                <Scale className="h-3.5 w-3.5" /> Audit artifact
              </div>
              <h3 className="text-3xl font-black text-white mb-2">Leaked Week 3 Run</h3>
              <div className="text-5xl font-black text-white mb-1">88.90%</div>
              <div className="text-sm text-amber-400 font-semibold mb-5">Documented, not shipped</div>
              <p className="text-white/55 leading-8 mb-5 text-sm">
                This number stays in the project because it proves we audited ourselves. It should never be presented as current model performance.
              </p>
              <div className="flex items-center gap-2 text-sm text-amber-300/90">
                <ShieldCheck className="h-4 w-4" /> Methodology credibility.
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="px-6 py-20 border-t border-white/6">
        <div className="mx-auto max-w-7xl">
          <div className="mb-10">
            <div className="text-xs uppercase tracking-[0.3em] text-cyan-300/80 mb-4">Tech stack</div>
            <h2 className="text-3xl sm:text-4xl font-black tracking-tight">Every layer has a job.</h2>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
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

      <section className="px-6 py-16 border-t border-white/6">
        <div className="mx-auto max-w-4xl text-center">
          <h2 className="text-2xl font-black text-white mb-6">Ready to see it in action?</h2>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <Link href="/demo"
              className="inline-flex items-center gap-2 rounded-2xl bg-red-600 px-6 py-3.5 text-sm font-bold text-white hover:bg-red-500 transition-colors">
              Run a live classification <ArrowRight className="h-4 w-4" />
            </Link>
            <Link href="/model"
              className="inline-flex items-center gap-2 rounded-2xl border border-white/15 px-6 py-3.5 text-sm font-bold text-white/80 hover:text-white hover:border-white/25 transition-colors">
              Review model evidence <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>

      <footer className="border-t border-white/6 py-8 text-center text-xs text-white/20">
        2026 TAVSS · MGT 599 Capstone · Group 4 · DePaul University Chicago
      </footer>
    </main>
  );
}
