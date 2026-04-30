import Navigation from "@/components/Navigation";
import Hero from "@/components/Hero";
import Link from "next/link";

const PAGES = [
  {
    href: "/ml",
    title: "TAVSS Control Center",
    desc: "A massive, real-time MLOps dashboard monitoring our pipeline health, metrics, and models.",
    color: "red",
    badge: "MLOps",
  },
  {
    href: "/features",
    title: "Feature Engineering",
    desc: "How we turned raw company text into 50,000-dimensional sparse vectors using TF-IDF.",
    color: "red",
    badge: "NLP",
  },
  {
    href: "/breezeml",
    title: "breezeml Library",
    desc: "The PyPI library we built, broke, and patched 5 times trying to get the Macro F1 above 75%.",
    color: "blue",
    badge: "v0.2.5",
  },
  {
    href: "/model",
    title: "Model and Results",
    desc: "Two Linear SVM models trained on sparse TF-IDF matrices. Task 1 hit 86.82% Macro F1.",
    color: "cyan",
    badge: "86.82%",
  },
  {
    href: "/graph",
    title: "Knowledge Graph",
    desc: "An interactive physics graph connecting companies, segments, subindustries, and keywords.",
    color: "emerald",
    badge: "Interactive",
  },
  {
    href: "/demo",
    title: "Live Demo",
    desc: "Paste any company description and watch the classifier assign a Morningstar GECS code in real time.",
    color: "amber",
    badge: "Live",
  },
  {
    href: "/team",
    title: "The Team",
    desc: "Five MGT 599 students who spent too many nights debugging memory crashes.",
    color: "rose",
    badge: "Group 4",
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

      <section className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <p className="text-center text-white/35 text-sm uppercase tracking-widest mb-12">
            Explore the project
          </p>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {PAGES.map((page) => (
              <Link
                key={page.href}
                href={page.href}
                className={`group rounded-2xl border p-6 transition-all duration-200 ${cardBorder[page.color]}`}
              >
                <div className="flex items-center justify-between mb-4">
                  <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${badgeColor[page.color]}`}>
                    {page.badge}
                  </span>
                  <span className="text-white/20 group-hover:text-white/50 transition-colors text-lg">
                    &rarr;
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
        © 2026 TAVSS · MGT 599 Capstone · Group 4 · DePaul University Chicago
      </footer>
    </main>
  );
}
