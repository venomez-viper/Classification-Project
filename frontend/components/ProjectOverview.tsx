"use client";
import { motion } from "framer-motion";
import { Database, Tags, FileText, Target, BarChart2, GitBranch } from "lucide-react";

const TASKS = [
  {
    number: "01",
    title: "Industry Classification",
    target: "MstarGlobal",
    classes: "145 classes",
    color: "violet",
    description:
      "Classify each company into one of 145 Morningstar GECS industry codes using LongProfile, SegmentName, and SegmentDescription as input features.",
    inputs: ["LongProfile", "SegmentName", "SegmentDescription", "Revenue data"],
  },
  {
    number: "02",
    title: "Subindustry Classification",
    target: "Subindustry",
    classes: "450 classes",
    color: "blue",
    description:
      "Classify each business segment into one of 450 granular Morningstar GECS subindustry activity codes using only segment-level text.",
    inputs: ["SegmentName", "SegmentDescription"],
  },
];

const CONSTRAINTS = [
  { icon: Database, label: "Point-In-Time", desc: "Latest record before Dec 31, 2024" },
  { icon: FileText, label: "Annual Filings Only", desc: "Full fiscal year disclosures" },
  { icon: Tags, label: "Anonymized IDs", desc: "Company names replaced with 'The Company'" },
  { icon: Target, label: "Complete Segments", desc: "All segments present for selected date" },
];

export default function ProjectOverview() {
  return (
    <section id="overview" className="py-32 px-6 section-glow">
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <p className="text-red-400 text-sm font-semibold uppercase tracking-widest mb-3">Project Overview</p>
          <h2 className="text-4xl sm:text-5xl font-bold text-white mb-5">
            What We Were Asked to Build
          </h2>
          <p className="text-white/50 text-lg max-w-2xl mx-auto">
            The Morningstar RED Team challenged us to build a production-ready automated
            GECS classification pipeline that could scale to the global equity universe.
            and extend to private markets via PitchBook.
          </p>
        </motion.div>

        {/* Task Cards */}
        <div className="grid md:grid-cols-2 gap-6 mb-16">
          {TASKS.map((task, i) => (
            <motion.div
              key={task.number}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.15 }}
              className={`relative rounded-2xl border p-8 overflow-hidden ${
                task.color === "violet"
                  ? "border-red-500/25 bg-red-500/5"
                  : "border-blue-500/25 bg-blue-500/5"
              }`}
            >
              <div className={`absolute top-0 right-0 text-8xl font-black opacity-5 leading-none pr-4 pt-2 ${
                task.color === "violet" ? "text-red-400" : "text-blue-400"
              }`}>{task.number}</div>

              <div className="flex items-center gap-3 mb-4">
                <span className={`text-xs font-bold uppercase tracking-widest px-3 py-1 rounded-full ${
                  task.color === "violet"
                    ? "bg-red-500/20 text-red-300"
                    : "bg-blue-500/20 text-blue-300"
                }`}>Task {task.number}</span>
                <span className="text-white/30 text-xs">{task.classes}</span>
              </div>

              <h3 className="text-2xl font-bold text-white mb-3">{task.title}</h3>
              <p className="text-white/50 mb-5 leading-relaxed">{task.description}</p>

              <div className="space-y-1.5">
                <p className="text-xs text-white/30 uppercase tracking-wider mb-2">Input Features</p>
                {task.inputs.map((inp) => (
                  <div key={inp} className="flex items-center gap-2 text-sm text-white/60">
                    <span className={`w-1 h-1 rounded-full ${task.color === "violet" ? "bg-red-400" : "bg-blue-400"}`} />
                    <code className="font-mono">{inp}</code>
                  </div>
                ))}
              </div>

              <div className={`mt-5 pt-5 border-t ${task.color === "violet" ? "border-red-500/15" : "border-blue-500/15"} flex items-center gap-2`}>
                <span className="text-xs text-white/30">Target Label:</span>
                <code className={`text-sm font-mono font-bold ${task.color === "violet" ? "text-red-300" : "text-blue-300"}`}>
                  {task.target}
                </code>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Dataset Constraints */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="grid grid-cols-2 md:grid-cols-4 gap-4"
        >
          {CONSTRAINTS.map((c) => (
            <div key={c.label} className="flex flex-col items-center text-center p-5 rounded-xl bg-white/4 border border-white/8">
              <c.icon className="w-5 h-5 text-red-400 mb-3" />
              <div className="text-sm font-semibold text-white mb-1">{c.label}</div>
              <div className="text-xs text-white/40">{c.desc}</div>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
