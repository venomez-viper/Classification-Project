"use client";
import React, { useState } from "react";
import { motion } from "framer-motion";
import { Share2, ZoomIn, ZoomOut, Move, Info, Filter } from "lucide-react";
import { TextScramble } from "@/components/ui/text-scramble";

const LEGEND = [
  { color: "#9b59b6", label: "Industry (Task 1)" },
  { color: "#e74c3c", label: "Subindustry (Task 2)" },
  { color: "#2ecc71", label: "Company" },
  { color: "#3498db", label: "Segment" },
  { color: "#f1c40f", label: "Keyword Feature" },
];

const STATS = [
  { label: "Total Nodes", value: "1,000" },
  { label: "Edge Connections", value: "4,200+" },
  { label: "Industry Classes", value: "145" },
  { label: "Subindustry Classes", value: "407" },
];

export default function GraphTab() {
  const [fullscreen, setFullscreen] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.4 }}
      className="max-w-[1600px] mx-auto pb-12 space-y-6"
    >
      {/* Header */}
      <div className="flex justify-between items-end border-b border-red-500/20 pb-4 relative">
        <div className="absolute bottom-0 left-0 w-1/3 h-[1px] bg-gradient-to-r from-red-500 to-transparent" />
        <div>
          <TextScramble as="h2" speed={0.02} duration={0.8} className="text-3xl font-black text-white tracking-widest uppercase">
            GECS Knowledge Graph
          </TextScramble>
          <p className="text-sm text-red-500/50 mt-1 font-mono tracking-widest uppercase">
            Interactive taxonomy map · 1,000 sampled company nodes · PyVis + NetworkX
          </p>
        </div>
        <button
          onClick={() => setFullscreen(!fullscreen)}
          className="flex items-center gap-2 px-4 py-2 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-xs font-mono hover:bg-red-500/20 transition-colors"
        >
          <ZoomIn className="w-4 h-4" />
          {fullscreen ? "Exit Fullscreen" : "Fullscreen"}
        </button>
      </div>

      {/* Stats strip */}
      <div className="grid grid-cols-4 gap-4">
        {STATS.map((s) => (
          <div key={s.label} className="bg-black/60 border border-white/5 rounded-xl p-4 text-center backdrop-blur-sm">
            <div className="text-2xl font-black font-mono text-red-400 drop-shadow-[0_0_10px_rgba(239,68,68,0.4)]">{s.value}</div>
            <div className="text-xs text-white/30 mt-1 font-mono uppercase tracking-wider">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 items-center">
        <div className="flex items-center gap-2 text-xs text-white/30 font-mono mr-2">
          <Filter className="w-3 h-3" /> NODE TYPES:
        </div>
        {LEGEND.map((item) => (
          <div key={item.label} className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 hover:bg-white/10 transition-colors cursor-default">
            <span className="w-2.5 h-2.5 rounded-full flex-shrink-0 shadow-lg" style={{ backgroundColor: item.color, boxShadow: `0 0 8px ${item.color}` }} />
            <span className="text-xs text-white/50 font-mono">{item.label}</span>
          </div>
        ))}
        <div className="ml-auto flex items-center gap-2 text-xs text-white/25 font-mono">
          <Move className="w-3 h-3" /> Drag nodes · Scroll to zoom · Click to highlight
        </div>
      </div>

      {/* Graph Frame */}
      <div
        className={`relative rounded-2xl overflow-hidden border border-white/10 bg-black transition-all duration-500 ${fullscreen ? "fixed inset-4 z-50 rounded-2xl" : ""}`}
        style={{ height: fullscreen ? "auto" : "78vh", minHeight: 600 }}
      >
        {/* Glow corners */}
        <div className="absolute top-0 left-0 w-32 h-32 bg-red-500/10 blur-3xl rounded-full pointer-events-none z-10" />
        <div className="absolute bottom-0 right-0 w-32 h-32 bg-purple-500/10 blur-3xl rounded-full pointer-events-none z-10" />

        {/* Top bar */}
        <div className="absolute top-0 left-0 right-0 z-20 flex items-center justify-between px-5 py-3 bg-black/80 backdrop-blur-sm border-b border-white/10">
          <div className="flex items-center gap-3">
            <span className="w-2 h-2 rounded-full bg-red-500 shadow-[0_0_8px_#ef4444] animate-pulse" />
            <span className="text-xs font-mono text-white/40 uppercase tracking-widest">GECS Taxonomy Classification Graph - LIVE</span>
          </div>
          <div className="flex items-center gap-2 text-xs font-mono text-white/25">
            <Info className="w-3 h-3" />
            <span>Generated with PyVis & NetworkX from Task 1 + Task 2 datasets</span>
          </div>
        </div>

        {/* iframe */}
        <iframe
          src="/graph/classification_graph.html"
          className="w-full h-full pt-11"
          title="GECS Classification Knowledge Graph"
          style={{ border: "none", background: "transparent" }}
        />

        {/* Bottom info bar */}
        <div className="absolute bottom-0 left-0 right-0 z-20 flex items-center justify-between px-5 py-2.5 bg-black/80 backdrop-blur-sm border-t border-white/10">
          <span className="text-[10px] font-mono text-white/20">1,000 company segments sampled from 53,585 training records for browser performance</span>
          <div className="flex gap-4 text-[10px] font-mono">
            <span className="text-red-400/60">■ Task 1: 145 classes</span>
            <span className="text-blue-400/60">■ Task 2: 407 classes</span>
          </div>
        </div>
      </div>

      {/* Fullscreen overlay close */}
      {fullscreen && (
        <button
          onClick={() => setFullscreen(false)}
          className="fixed top-6 right-6 z-[60] px-4 py-2 bg-red-600 text-white text-xs font-mono rounded-lg hover:bg-red-500 transition-colors shadow-[0_0_20px_rgba(239,68,68,0.5)]"
        >
          ✕ Close Fullscreen
        </button>
      )}
    </motion.div>
  );
}
