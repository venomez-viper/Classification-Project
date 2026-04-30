import Navigation from "@/components/Navigation";
import Link from "next/link";

const TEAM = [
  { name: "Akash Gupta", role: "ML Engineering & Backend" },
  { name: "Group 4 Member 2", role: "Data Pipeline & Feature Engineering" },
  { name: "Group 4 Member 3", role: "Model Training & Evaluation" },
  { name: "Group 4 Member 4", role: "Frontend & Visualization" },
  { name: "Group 4 Member 5", role: "Research & Documentation" },
];

const TECH = [
  { label: "Model", value: "DeBERTa-v3-small + Linear SVM" },
  { label: "Task 1 Macro F1", value: "86.82%" },
  { label: "DeBERTa F1", value: "78.10%" },
  { label: "Training Samples", value: "35,000+" },
  { label: "Industries Covered", value: "145 GECS classes" },
  { label: "Subindustries", value: "450+" },
  { label: "Vectorization", value: "TF-IDF (50k dims)" },
  { label: "Backend", value: "Flask · Railway" },
  { label: "LLM Host", value: "Hugging Face Spaces" },
  { label: "Frontend", value: "Next.js 15 · Vercel" },
];

export default function AboutPage() {
  return (
    <main className="min-h-screen bg-black text-white">
      <Navigation />

      {/* Header */}
      <section className="pt-40 pb-20 px-6 text-center">
        <span className="inline-block mb-4 rounded-full border border-red-500/30 bg-red-500/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-widest text-red-400">
          MGT 599 · Group 4 · DePaul University
        </span>
        <h1 className="text-5xl sm:text-6xl font-black tracking-tight mb-6">
          About the Project
        </h1>
        <p className="text-white/50 text-lg max-w-2xl mx-auto leading-relaxed">
          TAVSS — Text-Augmented Value &amp; Sector System — is an end-to-end MLOps platform
          that classifies companies into Morningstar GECS industries using fine-tuned
          transformer models and traditional ML pipelines.
        </p>
      </section>

      {/* What we built */}
      <section className="py-16 px-6 border-t border-white/6">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold mb-6 text-white/90">What We Built</h2>
          <div className="space-y-4 text-white/55 leading-relaxed">
            <p>
              Starting from raw Morningstar GECS company descriptions, we built a complete
              classification pipeline: text cleaning, TF-IDF vectorization at 50,000 dimensions,
              Linear SVM training across 145 industry categories, and a fine-tuned
              DeBERTa-v3-small model for 29 well-represented classes.
            </p>
            <p>
              We packaged the core ML logic into <span className="text-red-400 font-semibold">breezeml</span>,
              a public PyPI library. The TAVSS dashboard (this app) is the production-grade
              interface — connecting the Railway SVM backend, Hugging Face DeBERTa Space, and
              a Next.js frontend on Vercel into one unified MLOps control center.
            </p>
          </div>
        </div>
      </section>

      {/* Tech stats grid */}
      <section className="py-16 px-6 border-t border-white/6">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold mb-8 text-white/90">Technical Specs</h2>
          <div className="grid sm:grid-cols-2 gap-3">
            {TECH.map((t) => (
              <div
                key={t.label}
                className="flex items-center justify-between rounded-xl border border-white/8 bg-white/3 px-5 py-4"
              >
                <span className="text-sm text-white/40 uppercase tracking-wider">{t.label}</span>
                <span className="text-sm font-bold text-white">{t.value}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Team */}
      <section className="py-16 px-6 border-t border-white/6">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold mb-8 text-white/90">The Team</h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {TEAM.map((m) => (
              <div
                key={m.name}
                className="rounded-xl border border-white/8 bg-white/3 px-5 py-5"
              >
                <p className="font-bold text-white mb-1">{m.name}</p>
                <p className="text-sm text-white/40">{m.role}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-6 border-t border-white/6 text-center">
        <p className="text-white/40 mb-6 text-sm">Ready to try the classifier?</p>
        <Link
          href="/login"
          className="inline-flex items-center gap-2 rounded-full bg-red-600 hover:bg-red-500 px-8 py-3.5 text-sm font-bold text-white transition-all hover:-translate-y-0.5 shadow-lg shadow-red-900/40"
        >
          Login to TAVSS App →
        </Link>
      </section>

      <footer className="border-t border-white/6 py-8 text-center text-xs text-white/20">
        © 2026 TAVSS · MGT 599 Capstone · Group 4 · DePaul University Chicago
      </footer>
    </main>
  );
}
