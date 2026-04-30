"use client";

import { FallingPattern } from "@/components/ui/falling-pattern";
import { RevealText } from "@/components/ui/reveal-text";
import { GlowCard } from "@/components/ui/spotlight-card";
import { TextScramble } from "@/components/ui/text-scramble";
import { motion } from "framer-motion";
import { ExternalLink } from "lucide-react";

const TEAM = [
  {
    name: "AKASH",
    fullName: "Akash Anipakalu Giridhar",
    role: "ML Engineering and Library Architecture",
    detail:
      "Built and patched the breezeml PyPI library across 5 versions. Designed the sparse matrix pipeline, fixed the SVM deadlock that was causing 20-minute training times, and deployed the Flask inference server.",
    glowColor: "red" as const,
  },
  {
    name: "SUBASREE",
    fullName: "Subasree Segar",
    role: "Data Science and Model Evaluation",
    detail:
      "Ran evaluation across both tasks, analyzed per-class F1 scores, identified which industries the model struggled on, and compiled the performance diagnostics for the final report.",
    glowColor: "blue" as const,
  },
  {
    name: "VISHAL",
    fullName: "Vishal Shaileshkumar Rathod",
    role: "Feature Engineering",
    detail:
      "Developed the TF-IDF feature sets for both tasks, tested different vocabulary sizes and ngram configurations, and validated the full sparse vector pipeline end to end.",
    glowColor: "orange" as const,
  },
  {
    name: "SRILAXMI",
    fullName: "Srilaxmi Ganjipalli",
    role: "Data Exploration and Preprocessing",
    detail:
      "Analyzed the raw dataset structure, identified class imbalance patterns, applied the cleaning logic for rare classes and missing values, and documented all data constraints.",
    glowColor: "green" as const,
  },
  {
    name: "TSERENNADMID",
    fullName: "Tserennadmid Batkhuu",
    role: "Reporting and Documentation",
    detail:
      "Maintained the GitHub repository, wrote the weekly progress reports, and kept all project documentation up to date across all three weeks of the capstone.",
    glowColor: "purple" as const,
  },
];

export default function Team() {
  return (
    <section id="team" className="relative min-h-screen overflow-hidden bg-black">
      {/* Full page Matrix green FallingPattern */}
      <div className="fixed inset-0 z-0 opacity-60 pointer-events-none">
        <FallingPattern
          color="#00ff41"
          backgroundColor="#000000"
          duration={80}
          blurIntensity="0.2rem"
          density={1}
        />
      </div>

      <div className="relative z-10 max-w-5xl mx-auto px-6 py-20">
        {/* Page title */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-20"
        >
          <TextScramble as="p" speed={0.02} duration={0.8} characterSet="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" className="text-red-500 text-sm font-semibold uppercase tracking-widest mb-4">
            DePaul University Chicago
          </TextScramble>
          <h1 className="text-6xl sm:text-8xl font-black text-white tracking-tight mb-3">
            Group 4
          </h1>
          <p className="text-white/40 text-lg">
            The five people who stayed up debugging memory crashes so you would not have to.
          </p>
        </motion.div>

        <div className="space-y-20">
          {TEAM.map((member, i) => (
            <motion.div
              key={member.name}
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.1 }}
            >
              {/* Giant name - left aligned */}
              <div className="flex items-center mb-6">
                <RevealText
                  text={member.name}
                  textColor="text-white"
                  overlayColor="text-red-500"
                  fontSize="text-[64px] sm:text-[90px] lg:text-[112px]"
                  letterDelay={0.06}
                  overlayDelay={0.04}
                  letterImages={[
                    "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&q=80",
                    "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&q=80",
                    "https://images.unsplash.com/photo-1666875753105-c63a6f3bdc86?w=800&q=80",
                    "https://images.unsplash.com/photo-1639762681485-074b7f938ba0?w=800&q=80",
                    "https://images.unsplash.com/photo-1504868584819-f8e8b4b6d7e3?w=800&q=80",
                    "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&q=80",
                    "https://images.unsplash.com/photo-1526628953301-3cd0b8b9d3e5?w=800&q=80",
                    "https://images.unsplash.com/photo-1543286386-713bdd548da4?w=800&q=80",
                    "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=800&q=80",
                    "https://images.unsplash.com/photo-1605792657660-596af9009e82?w=800&q=80",
                    "https://images.unsplash.com/photo-1614064641938-3bbee52942c7?w=800&q=80",
                    "https://images.unsplash.com/photo-1611532736597-de2d4265fba3?w=800&q=80",
                  ]}
                />
              </div>

              {/* Detail card sits under the name, same left edge */}
              <GlowCard glowColor={member.glowColor} className="w-full">
                <div className="flex flex-col sm:flex-row sm:items-start gap-4">
                  <div className="flex-1">
                    <p className="text-xs font-bold uppercase tracking-widest text-white/40 mb-1">
                      {member.fullName}
                    </p>
                    <TextScramble as="p" speed={0.015} duration={0.5} className="text-base font-semibold text-white mb-2">
                      {member.role}
                    </TextScramble>
                    <p className="text-sm text-white/55 leading-relaxed">{member.detail}</p>
                  </div>
                </div>
              </GlowCard>
            </motion.div>
          ))}
        </div>

        {/* Footer links */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="mt-24 pt-12 border-t border-white/8 flex flex-wrap items-center justify-center gap-4"
        >
          <a
            href="https://github.com/venomez-viper/Classification-Project"
            target="_blank"
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 text-white/50 hover:text-white text-sm transition-all"
          >
            <ExternalLink className="w-4 h-4" />
            GitHub Repository
          </a>
          <a
            href="https://pypi.org/project/breezeml/"
            target="_blank"
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg border border-red-600/20 bg-red-600/8 hover:bg-red-600/15 text-red-400 hover:text-red-300 text-sm transition-all"
          >
            breezeml on PyPI
          </a>
        </motion.div>
      </div>
    </section>
  );
}
