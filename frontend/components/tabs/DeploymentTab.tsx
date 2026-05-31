"use client";
import React from "react";
import { motion } from "framer-motion";
import Dashboard from "@/components/Dashboard";

export default function DeploymentTab() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.4 }}
      className="pb-12"
    >
      <div className="flex justify-between items-end border-b border-red-500/20 pb-4 mb-6 relative">
        <div className="absolute bottom-0 left-0 w-1/3 h-[1px] bg-gradient-to-r from-red-500 to-transparent" />
        <div>
          <h2 className="text-3xl font-black text-white tracking-widest uppercase">
            Live Inference · SVM Primary Engine
          </h2>
          <p className="text-sm text-red-500/50 mt-1 font-mono tracking-widest uppercase">Port 5000 · breezeml v0.2.5 · ConfidenceGauge + Alternatives + Feature Tags</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/30 rounded font-mono text-xs text-emerald-400">
          <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_#10b981] animate-pulse" />
          PORT 5000 ACTIVE
        </div>
      </div>

      {/* 
        Dashboard already contains: ConfidenceGauge, ResultPanel, AlternativesList,
        FeatureTags, PerfBar, AchievementStats, CodeChip - all fully wired to /api/predict.
        We override its min-h-screen root div with a scoped wrapper.
      */}
      <div className="[&>div]:min-h-0 [&>div]:pt-0 [&>div]:bg-transparent">
        <Dashboard />
      </div>

      {/* Knowledge Graph */}
      <div className="mt-10 border border-white/10 rounded-2xl overflow-hidden" style={{ height: "80vh" }}>
        <div className="px-6 py-4 border-b border-white/10 flex items-center gap-3 bg-black/40">
          <span className="w-2 h-2 rounded-full bg-purple-500 animate-pulse" />
          <span className="text-xs font-mono text-white/40 uppercase tracking-widest">Interactive GECS Knowledge Graph - 1,000 Sampled Nodes</span>
        </div>
        <iframe
          src="/graph/classification_graph.html"
          className="w-full h-full"
          title="GECS Classification Knowledge Graph"
        />
      </div>
    </motion.div>
  );
}
