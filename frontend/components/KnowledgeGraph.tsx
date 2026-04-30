"use client";
import { motion } from "framer-motion";
import { Info } from "lucide-react";

export default function KnowledgeGraph() {
  return (
    <section id="graph" className="py-32 px-6 section-glow">
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-10"
        >
          <p className="text-red-400 text-sm font-semibold uppercase tracking-widest mb-3">Data Explorer</p>
          <h2 className="text-4xl sm:text-5xl font-bold text-white mb-5">
            Interactive Knowledge Graph
          </h2>
          <p className="text-white/50 text-lg max-w-2xl mx-auto">
            This graph connects 1,000 sampled company segments across all five levels of the
            GECS hierarchy. You can pan, zoom, click any node, and filter by group.
          </p>
        </motion.div>

        {/* Legend */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="flex flex-wrap justify-center gap-4 mb-6"
        >
          {[
            { color: "#9b59b6", label: "Industry (Task 1)" },
            { color: "#e74c3c", label: "Subindustry (Task 2)" },
            { color: "#2ecc71", label: "Company" },
            { color: "#3498db", label: "Segment" },
            { color: "#f1c40f", label: "Keyword Feature" },
          ].map((item) => (
            <div key={item.label} className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10">
              <span className="w-2.5 h-2.5 rounded-full" style={{ background: item.color }} />
              <span className="text-xs text-white/60">{item.label}</span>
            </div>
          ))}
        </motion.div>

        {/* Tip */}
        <div className="flex items-center gap-2 text-xs text-white/35 justify-center mb-4">
          <Info className="w-3.5 h-3.5" />
          <span>Drag nodes to rearrange. Click any node to highlight its connections. Use the filters at the top of the graph.</span>
        </div>

        {/* Graph iframe */}
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="rounded-2xl border border-white/10 overflow-hidden"
          style={{ height: "88vh", minHeight: "700px" }}
        >
          <iframe
            src="/graph/classification_graph.html"
            className="w-full h-full"
            title="GECS Classification Knowledge Graph"
          />
        </motion.div>

        <p className="text-center text-xs text-white/25 mt-4">
          Generated with PyVis and NetworkX from the Task 1 and Task 2 datasets. 1,000 segments sampled for browser performance.
        </p>
      </div>
    </section>
  );
}
