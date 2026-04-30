"use client";

import { motion } from "framer-motion";
import { ExternalLink, GitBranch, Library, LineChart, ScanSearch, ServerCog } from "lucide-react";
import { FallingPattern } from "@/components/ui/falling-pattern";
import { GlowCard } from "@/components/ui/spotlight-card";
import { RevealText } from "@/components/ui/reveal-text";
import { TextScramble } from "@/components/ui/text-scramble";

const TEAM = [
  {
    name: "AKASH",
    fullName: "Akash Anipakalu Giridhar",
    role: "ML Engineering and Library Architecture",
    detail:
      "Built and patched the breezeml package, shaped the sparse inference pipeline, and deployed the Flask serving layer used by the app.",
    glowColor: "red" as const,
    icon: Library,
  },
  {
    name: "SUBASREE",
    fullName: "Subasree Segar",
    role: "Data Science and Model Evaluation",
    detail:
      "Ran evaluation across both tasks, read the failure patterns at the class level, and translated model behavior into report-grade findings.",
    glowColor: "blue" as const,
    icon: LineChart,
  },
  {
    name: "VISHAL",
    fullName: "Vishal Shaileshkumar Rathod",
    role: "Feature Engineering",
    detail:
      "Designed and validated the TF-IDF feature space, tested vocabulary and n-gram settings, and kept the sparse pipeline effective.",
    glowColor: "orange" as const,
    icon: ServerCog,
  },
  {
    name: "SRILAXMI",
    fullName: "Srilaxmi Ganjipalli",
    role: "Data Exploration and Preprocessing",
    detail:
      "Mapped the raw dataset structure, identified imbalance and cleaning issues, and clarified the data constraints the models had to survive.",
    glowColor: "green" as const,
    icon: ScanSearch,
  },
  {
    name: "TSERENNADMID",
    fullName: "Tserennadmid Batkhuu",
    role: "Reporting and Documentation",
    detail:
      "Maintained repository continuity, documented the weekly project state, and kept the team narrative coherent as the system evolved.",
    glowColor: "purple" as const,
    icon: GitBranch,
  },
];

const STRIP = [
  { label: "People", value: "5" },
  { label: "Core workstreams", value: "5" },
  { label: "Shared outcome", value: "1 shipped system" },
  { label: "Operating mode", value: "Cross-functional" },
];

export default function Team() {
  return (
    <section id="team" className="relative min-h-screen overflow-hidden bg-black text-white">
      <div className="fixed inset-0 z-0 opacity-45 pointer-events-none">
        <FallingPattern
          color="#00ff41"
          backgroundColor="#000000"
          duration={80}
          blurIntensity="0.2rem"
          density={1}
        />
      </div>

      <div className="relative z-10 px-6 py-20">
        <div className="mx-auto max-w-7xl">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.65 }}
            className="grid gap-10 lg:grid-cols-[1.12fr_0.88fr] lg:items-end"
          >
            <div>
              <TextScramble
                as="p"
                speed={0.02}
                duration={0.8}
                characterSet="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
                className="text-red-400 text-sm font-semibold uppercase tracking-[0.3em] mb-5"
              >
                Systems Team
              </TextScramble>

              <div className="mb-6">
                <RevealText
                  text="GROUP4"
                  textColor="text-white"
                  overlayColor="text-red-500"
                  fontSize="text-[56px] sm:text-[92px] lg:text-[124px]"
                  letterDelay={0.06}
                  overlayDelay={0.035}
                />
              </div>

              <h1 className="max-w-4xl text-3xl sm:text-5xl lg:text-6xl font-black tracking-tight leading-[0.96]">
                Five people, five specialties,
                <span className="block text-white/55">one end-to-end product story.</span>
              </h1>

              <p className="mt-6 max-w-3xl text-lg sm:text-xl leading-relaxed text-white/55">
                This capstone worked because the team split responsibility clearly, then pulled the work back together
                into a single system across modeling, documentation, deployment, and presentation.
              </p>
            </div>

            <div className="rounded-[32px] border border-white/10 bg-white/[0.04] backdrop-blur-xl overflow-hidden">
              <div className="border-b border-white/8 px-6 py-5">
                <div className="text-xs uppercase tracking-[0.28em] text-emerald-300/80 mb-2">Operating snapshot</div>
                <h2 className="text-2xl font-bold text-white">The build crew behind TAVSS</h2>
              </div>
              <div className="grid grid-cols-2 gap-px bg-white/8">
                {STRIP.map((item) => (
                  <div key={item.label} className="bg-black/65 px-6 py-6">
                    <div className="text-xs uppercase tracking-[0.24em] text-white/35">{item.label}</div>
                    <div className="mt-2 text-2xl font-black text-white">{item.value}</div>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>

          <div className="mt-16 grid gap-5 md:grid-cols-2 xl:grid-cols-5">
            {TEAM.map((member, index) => (
              <motion.div
                key={member.name}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-120px" }}
                transition={{ duration: 0.55, delay: index * 0.05 }}
              >
                <GlowCard glowColor={member.glowColor} className="h-full border-white/8 bg-white/[0.03] p-6">
                  <div className="mb-5 flex items-center justify-between">
                    <member.icon className="h-5 w-5 text-white/75" />
                    <span className="text-xs uppercase tracking-[0.24em] text-white/28">Core role</span>
                  </div>
                  <div className="text-2xl font-black text-white mb-2">{member.name}</div>
                  <div className="text-sm text-white/45 mb-4 min-h-[44px]">{member.fullName}</div>
                  <div className="text-xs uppercase tracking-[0.24em] text-red-300/80 mb-3">{member.role}</div>
                  <p className="text-sm leading-7 text-white/58">{member.detail}</p>
                </GlowCard>
              </motion.div>
            ))}
          </div>

          <div className="mt-16 grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
            <div className="rounded-[32px] border border-white/10 bg-black/35 p-8">
              <div className="text-xs uppercase tracking-[0.28em] text-cyan-300/80 mb-4">Team doctrine</div>
              <h2 className="text-3xl font-black text-white mb-4">No isolated heroics. Shared system ownership.</h2>
              <p className="text-white/55 leading-8">
                The strongest part of the team was not that every member did the same kind of work. It was that each
                workstream connected cleanly to the next one. Data work informed modeling. Modeling informed deployment.
                Deployment shaped the product story. Documentation made the whole thing legible.
              </p>
            </div>

            <div className="rounded-[32px] border border-white/10 bg-white/[0.03] p-8">
              <div className="text-xs uppercase tracking-[0.28em] text-rose-300/80 mb-5">Contribution lanes</div>
              <div className="space-y-4">
                {TEAM.map((member) => (
                  <div key={member.fullName} className="rounded-2xl border border-white/8 bg-black/30 px-5 py-4">
                    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                      <div>
                        <div className="font-semibold text-white">{member.fullName}</div>
                        <div className="text-sm text-white/45">{member.role}</div>
                      </div>
                      <div className="text-xs uppercase tracking-[0.24em] text-white/28">Group 4</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="mt-20 pt-12 border-t border-white/8 flex flex-wrap items-center justify-center gap-4"
          >
            <a
              href="https://github.com/venomez-viper/Classification-Project"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 text-white/50 hover:text-white text-sm transition-all"
            >
              <ExternalLink className="w-4 h-4" />
              GitHub Repository
            </a>
            <a
              href="https://pypi.org/project/breezeml/"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg border border-red-600/20 bg-red-600/8 hover:bg-red-600/15 text-red-400 hover:text-red-300 text-sm transition-all"
            >
              breezeml on PyPI
            </a>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
