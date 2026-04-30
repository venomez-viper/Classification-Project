import Navigation from "@/components/Navigation";
import Hero from "@/components/Hero";
import Link from "next/link";
import {
  ArrowRight,
  BrainCircuit,
  DatabaseZap,
  GitBranch,
  PlayCircle,
  Radar,
  ShieldCheck,
  Users,
} from "lucide-react";

const PAGES = [
  {
    href: "/ml",
    title: "TAVSS Control Center",
    desc: "A real-time MLOps dashboard monitoring pipeline health, metrics, and model behavior.",
    color: "red",
    badge: "MLOps",
  },
  {
    href: "/features",
    title: "Feature Engineering",
    desc: "How raw company text became a 50,000-dimensional sparse representation using TF-IDF.",
    color: "red",
    badge: "NLP",
  },
  {
    href: "/breezeml",
    title: "breezeml Library",
    desc: "The PyPI package we built, patched, and used to support the production inference flow.",
    color: "blue",
    badge: "v0.2.5",
  },
  {
    href: "/model",
    title: "Model and Results",
    desc: "Two Linear SVM models trained on sparse vectors, with Task 1 reaching 86.82% Macro F1.",
    color: "cyan",
    badge: "86.82%",
  },
  {
    href: "/graph",
    title: "Knowledge Graph",
    desc: "An interactive graph connecting companies, segments, subindustries, and keywords.",
    color: "emerald",
    badge: "Interactive",
  },
  {
    href: "/demo",
    title: "Live Demo",
    desc: "Paste a company description and watch the classifier assign a Morningstar GECS code in real time.",
    color: "amber",
    badge: "Live",
  },
  {
    href: "/team",
    title: "The Team",
    desc: "Five MGT 599 students who turned a difficult capstone into a working product.",
    color: "rose",
    badge: "Group 4",
  },
];

const JOURNEY_STOPS = [
  {
    step: "01",
    title: "Frame the business problem",
    desc: "Morningstar descriptions, real class imbalance, and an industry taxonomy too broad for shortcuts.",
    href: "/about",
  },
  {
    step: "02",
    title: "Engineer the text pipeline",
    desc: "Sparse TF-IDF features, vocabulary tuning, and a training path built around control and speed.",
    href: "/features",
  },
  {
    step: "03",
    title: "Compare SVM and LLM tracks",
    desc: "A serious model decision shaped by Macro F1, cost, and deployment practicality.",
    href: "/model",
  },
  {
    step: "04",
    title: "Deploy and demonstrate",
    desc: "A product flow that can still lean on local services when remote deployments fail.",
    href: "/demo",
  },
];

const TEAM_HIGHLIGHTS = [
  {
    name: "Akash",
    role: "ML engineering",
    desc: "Inference stack, breezeml architecture, and deployment plumbing.",
  },
  {
    name: "Subasree",
    role: "Evaluation",
    desc: "Per-class diagnostics, metrics analysis, and results synthesis.",
  },
  {
    name: "Vishal",
    role: "Feature engineering",
    desc: "TF-IDF design, sparse vector experiments, and pipeline validation.",
  },
  {
    name: "Srilaxmi",
    role: "Preprocessing",
    desc: "Data structure review, cleaning rules, and imbalance constraints.",
  },
  {
    name: "Tserennadmid",
    role: "Documentation",
    desc: "Reports, repo coordination, and project continuity across weeks.",
  },
];

const PILLARS = [
  {
    icon: DatabaseZap,
    title: "Structured Data Work",
    desc: "The project treats messy company descriptions like a production input stream, not a classroom toy dataset.",
  },
  {
    icon: BrainCircuit,
    title: "Model Choices With Consequences",
    desc: "Classical ML and LLM approaches were both tested, but only one earned the production role.",
  },
  {
    icon: ShieldCheck,
    title: "Failure-Aware Deployment",
    desc: "The app is now easier to keep useful even when Railway or Hugging Face are unavailable.",
  },
];

const cardBorder: Record<string, string> = {
  red: "border-red-500/25 hover:border-red-500/50 bg-red-500/5",
  blue: "border-blue-500/25 hover:border-blue-500/50 bg-blue-500/5",
  cyan: "border-cyan-500/25 hover:border-cyan-500/50 bg-cyan-500/5",
  emerald: "border-emerald-500/25 hover:border-emerald-500/50 bg-emerald-500/5",
  amber: "border-amber-500/25 hover:border-amber-500/50 bg-amber-500/5",
  rose: "border-rose-500/25 hover:border-rose-500/50 bg-rose-500/5",
};

const badgeColor: Record<string, string> = {
  red: "bg-red-500/20 text-red-300",
  blue: "bg-blue-500/20 text-blue-300",
  cyan: "bg-cyan-500/20 text-cyan-300",
  emerald: "bg-emerald-500/20 text-emerald-300",
  amber: "bg-amber-500/20 text-amber-300",
  rose: "bg-rose-500/20 text-rose-300",
};

export default function Home() {
  return (
    <main className="min-h-screen bg-black">
      <Navigation />
      <Hero />

      <section className="relative px-6 pb-10">
        <div className="max-w-6xl mx-auto -mt-14 relative z-10">
          <div className="grid gap-4 md:grid-cols-3">
            {PILLARS.map((pillar) => (
              <div
                key={pillar.title}
                className="rounded-3xl border border-white/10 bg-white/[0.04] backdrop-blur-xl p-6 shadow-[0_25px_80px_rgba(0,0,0,0.28)]"
              >
                <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-red-500/20 to-cyan-400/10 border border-white/10 flex items-center justify-center mb-4">
                  <pillar.icon className="w-5 h-5 text-white/80" />
                </div>
                <h2 className="text-lg font-semibold text-white mb-2">{pillar.title}</h2>
                <p className="text-sm leading-relaxed text-white/55">{pillar.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="relative py-24 px-6 overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-10 right-[10%] h-64 w-64 rounded-full bg-red-600/10 blur-3xl" />
          <div className="absolute bottom-0 left-[8%] h-72 w-72 rounded-full bg-cyan-500/10 blur-3xl" />
        </div>

        <div className="max-w-6xl mx-auto relative z-10">
          <div className="flex flex-col gap-5 md:flex-row md:items-end md:justify-between mb-12">
            <div className="max-w-2xl">
              <p className="text-sm uppercase tracking-[0.32em] text-red-400/80 mb-4">Guided Journey</p>
              <h2 className="text-4xl sm:text-5xl font-bold text-white tracking-tight mb-4">
                A clearer path through the capstone
              </h2>
              <p className="text-white/55 text-lg leading-relaxed">
                Start with the business problem, move through the engineering tradeoffs, and finish at the live product.
                The team page is now pulled into that flow instead of sitting off to the side.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Link
                href="/journey"
                className="inline-flex items-center gap-2 rounded-2xl bg-white text-black px-5 py-3 text-sm font-semibold hover:bg-red-50 transition-colors"
              >
                Read full journey
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                href="/team"
                className="inline-flex items-center gap-2 rounded-2xl border border-white/15 px-5 py-3 text-sm font-semibold text-white/75 hover:text-white hover:border-white/25 transition-colors"
              >
                Meet the team
                <Users className="w-4 h-4" />
              </Link>
            </div>
          </div>

          <div className="grid gap-4 lg:grid-cols-4">
            {JOURNEY_STOPS.map((stop, index) => (
              <Link
                key={stop.step}
                href={stop.href}
                className={`group rounded-[28px] border p-6 transition-all duration-300 hover:-translate-y-1 ${
                  index === 0
                    ? "border-red-500/30 bg-red-500/8"
                    : index === 1
                      ? "border-blue-500/25 bg-blue-500/8"
                      : index === 2
                        ? "border-cyan-500/25 bg-cyan-500/8"
                        : "border-emerald-500/25 bg-emerald-500/8"
                }`}
              >
                <div className="flex items-center justify-between mb-8">
                  <span className="text-xs tracking-[0.3em] uppercase text-white/35">Stop {stop.step}</span>
                  <GitBranch className="w-4 h-4 text-white/25 group-hover:text-white/55 transition-colors" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3 leading-tight">{stop.title}</h3>
                <p className="text-sm text-white/55 leading-relaxed mb-8">{stop.desc}</p>
                <span className="inline-flex items-center gap-2 text-sm text-white/70 group-hover:text-white transition-colors">
                  Open section
                  <ArrowRight className="w-4 h-4" />
                </span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section className="px-6 pb-24">
        <div className="max-w-6xl mx-auto grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
          <div className="rounded-[32px] border border-white/10 bg-gradient-to-br from-white/[0.06] to-white/[0.02] p-8 md:p-10">
            <p className="text-sm uppercase tracking-[0.32em] text-rose-300/80 mb-4">Team Spotlight</p>
            <h2 className="text-3xl sm:text-4xl font-bold text-white tracking-tight mb-4">
              The people behind the pipeline now sit inside the story
            </h2>
            <p className="text-white/55 text-lg leading-relaxed mb-8">
              The dedicated team page already existed. This redesign makes it a core stop in the visitor journey so the
              project feels authored, not anonymous.
            </p>

            <div className="grid gap-3 sm:grid-cols-2">
              {TEAM_HIGHLIGHTS.map((member) => (
                <div key={member.name} className="rounded-2xl border border-white/10 bg-black/25 p-4">
                  <div className="text-xs uppercase tracking-[0.28em] text-white/35 mb-2">{member.role}</div>
                  <div className="text-lg font-semibold text-white mb-2">{member.name}</div>
                  <p className="text-sm text-white/55 leading-relaxed">{member.desc}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-[32px] border border-white/10 bg-black/35 p-8 md:p-10 flex flex-col justify-between overflow-hidden relative">
            <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(circle_at_top_right,rgba(244,63,94,0.18),transparent_30%),radial-gradient(circle_at_bottom_left,rgba(34,211,238,0.14),transparent_35%)]" />
            <div className="relative z-10">
              <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs uppercase tracking-[0.26em] text-white/55 mb-6">
                <Radar className="w-3.5 h-3.5" />
                Group 4
              </div>
              <h3 className="text-3xl font-bold text-white mb-4">Five roles. One finished system.</h3>
              <p className="text-white/55 leading-relaxed mb-8">
                From data constraints to documentation, the capstone moved because the work was distributed with intention
                and pulled back together into one deployable experience.
              </p>

              <div className="space-y-3 mb-8">
                {TEAM_HIGHLIGHTS.map((member) => (
                  <div key={member.name} className="flex items-start justify-between gap-4 border-b border-white/8 pb-3">
                    <div>
                      <div className="text-white font-medium">{member.name}</div>
                      <div className="text-sm text-white/45">{member.role}</div>
                    </div>
                    <span className="text-xs uppercase tracking-[0.25em] text-white/30">Core</span>
                  </div>
                ))}
              </div>
            </div>

            <Link
              href="/team"
              className="relative z-10 inline-flex items-center justify-center gap-2 rounded-2xl bg-red-600 px-5 py-3 text-sm font-semibold text-white hover:bg-red-500 transition-colors"
            >
              Open team page
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      <section className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between mb-12">
            <div>
              <p className="text-sm uppercase tracking-[0.32em] text-white/35 mb-4">
                Explore the platform
              </p>
              <h2 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">
                Dive into the modules that make the system real
              </h2>
            </div>
            <Link
              href="/demo"
              className="inline-flex items-center gap-2 text-sm font-semibold text-amber-300 hover:text-amber-200 transition-colors"
            >
              Try the live demo
              <PlayCircle className="w-4 h-4" />
            </Link>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {PAGES.map((page) => (
              <Link
                key={page.href}
                href={page.href}
                className={`group rounded-[28px] border p-6 transition-all duration-300 hover:-translate-y-1 ${cardBorder[page.color]}`}
              >
                <div className="flex items-center justify-between mb-4">
                  <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${badgeColor[page.color]}`}>
                    {page.badge}
                  </span>
                  <span className="text-white/20 group-hover:text-white/50 transition-colors text-lg">
                    {"->"}
                  </span>
                </div>
                <h3 className="text-base font-bold text-white mb-2">{page.title}</h3>
                <p className="text-sm text-white/45 leading-relaxed">{page.desc}</p>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <footer className="border-t border-white/6 py-8 text-center text-xs text-white/20">
        (c) 2026 TAVSS | MGT 599 Capstone | Group 4 | DePaul University Chicago
      </footer>
    </main>
  );
}
