import React from "react";
import { motion } from "framer-motion";
import { Cpu, Zap, Activity, AlertTriangle, Server, Layers } from "lucide-react";
import { GlowCard } from "@/components/ui/spotlight-card";
import { TextScramble } from "@/components/ui/text-scramble";

const AnimatedBar = ({ value, color }: { value: number; color: string }) => (
  <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden mt-2 border border-white/10">
    <motion.div 
      initial={{ width: 0 }} 
      animate={{ width: `${value}%` }} 
      transition={{ duration: 1.5, ease: "easeOut", delay: 0.2 }}
      className="h-full relative rounded-full"
      style={{ backgroundColor: color, boxShadow: `0 0 15px ${color}` }}
    >
      <div className="absolute inset-0 bg-white/20 w-full animate-[shimmer_2s_infinite]" />
    </motion.div>
  </div>
);

export default function ModelsTab() {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }} 
      animate={{ opacity: 1, y: 0 }} 
      exit={{ opacity: 0 }} 
      transition={{ duration: 0.4 }} 
      className="max-w-[1600px] mx-auto pb-12 space-y-8"
    >
      <div className="flex justify-between items-end mb-8 border-b border-red-500/20 pb-4 relative">
        <div className="absolute bottom-0 left-0 w-1/3 h-[1px] bg-gradient-to-r from-red-500 to-transparent" />
        <div>
          <TextScramble as="h2" speed={0.02} duration={0.8} className="text-3xl font-black text-white tracking-widest uppercase text-shadow-red">
            Model Registry & Evaluation
          </TextScramble>
          <p className="text-sm text-red-500/50 mt-1 font-mono tracking-widest uppercase">Cascade SVM (Live Demo) · ModernBERT-large Ensemble (Locked Result)</p>
        </div>
        <div className="text-right flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1 bg-red-500/10 border border-red-500/30 rounded font-mono text-xs text-red-400">
            <Activity className="w-3 h-3 animate-pulse" /> 2 MODELS ONLINE
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-10">
        {/* PRIMARY ENGINE: SVM */}
        <GlowCard glowColor="red" className="p-8 border-red-500/20 bg-[#060606]/80 backdrop-blur-xl relative overflow-hidden flex flex-col h-full">
          <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-red-500/5 blur-[100px] rounded-full pointer-events-none" />
          
          <div className="flex items-center gap-5 mb-8 relative z-10 border-b border-white/5 pb-6">
            <div className="w-16 h-16 rounded-xl bg-red-500/10 flex items-center justify-center border border-red-500/30 shadow-[0_0_20px_rgba(239,68,68,0.2)]">
              <Zap className="w-8 h-8 text-red-500" />
            </div>
            <div>
              <div className="text-xs font-bold text-red-500 tracking-[0.3em] uppercase mb-1">Primary Engine</div>
              <h3 className="text-3xl font-black text-white tracking-tight">LinearSVC</h3>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-6 mb-8 relative z-10">
            <div className="bg-black/60 border border-white/10 p-5 rounded-xl shadow-[inset_0_0_20px_rgba(255,255,255,0.02)]">
              <div className="flex justify-between items-end mb-1">
                <span className="text-xs text-white/40 uppercase tracking-widest font-mono">Macro F1 Score</span>
                <span className="text-sm font-bold text-red-400 font-mono">75.0%</span>
              </div>
              <AnimatedBar value={75.0} color="#ef4444" />
            </div>
            <div className="bg-black/60 border border-white/10 p-5 rounded-xl shadow-[inset_0_0_20px_rgba(255,255,255,0.02)] flex flex-col justify-center">
              <div className="text-xs text-white/40 uppercase tracking-widest font-mono mb-1">Latency (P99)</div>
              <div className="text-3xl font-mono font-bold text-white flex items-baseline gap-1">
                ~5 <span className="text-sm text-white/30">ms</span>
              </div>
            </div>
          </div>

          <div className="space-y-4 relative z-10 flex-1">
            <div className="border border-white/10 bg-black/40 p-5 rounded-xl backdrop-blur-sm">
              <h4 className="text-xs font-bold text-white/60 uppercase tracking-[0.2em] mb-3 flex items-center gap-2">
                <Layers className="w-4 h-4 text-white/40" /> Architecture Specs
              </h4>
              <ul className="text-sm text-white/50 space-y-3 font-mono">
                <li className="flex justify-between"><span className="text-white/30">Vectoriser</span> <span className="text-red-400">TF-IDF (60,000 bigrams)</span></li>
                <li className="flex justify-between"><span className="text-white/30">Matrix Format</span> <span className="text-red-400">scipy.sparse CSR</span></li>
                <li className="flex justify-between"><span className="text-white/30">Algorithm</span> <span className="text-red-400">Linear SVM</span></li>
                <li className="flex justify-between"><span className="text-white/30">Framework</span> <span className="text-red-400">breezeml v0.2.5</span></li>
              </ul>
            </div>
            
            <div className="border border-emerald-500/20 bg-emerald-500/5 p-5 rounded-xl flex items-start gap-4">
              <Activity className="w-6 h-6 text-emerald-500 flex-shrink-0" />
              <div>
                <h4 className="text-xs font-bold text-emerald-500 uppercase tracking-widest mb-1">Production Ready</h4>
                <p className="text-sm text-white/60 leading-relaxed">
                  Handles 145-class imbalance via <code>class_weight=&apos;balanced&apos;</code>. Deployed on HF Space — serves the live demo at ~5ms per prediction.
                </p>
              </div>
            </div>
          </div>
        </GlowCard>

        {/* TRANSFORMER ENGINE: ModernBERT */}
        <GlowCard glowColor="purple" className="p-8 border-purple-500/20 bg-[#060606]/80 backdrop-blur-xl relative overflow-hidden flex flex-col h-full">
          <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-purple-500/5 blur-[100px] rounded-full pointer-events-none" />

          <div className="flex items-center gap-5 mb-8 relative z-10 border-b border-white/5 pb-6">
            <div className="w-16 h-16 rounded-xl bg-purple-500/10 flex items-center justify-center border border-purple-500/30 shadow-[0_0_20px_rgba(168,85,247,0.2)]">
              <Cpu className="w-8 h-8 text-purple-400" />
            </div>
            <div>
              <div className="text-xs font-bold text-purple-400 tracking-[0.3em] uppercase mb-1">Transformer — Locked Result</div>
              <h3 className="text-3xl font-black text-white tracking-tight">ModernBERT-large</h3>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-6 mb-8 relative z-10">
            <div className="bg-black/60 border border-white/10 p-5 rounded-xl shadow-[inset_0_0_20px_rgba(255,255,255,0.02)]">
              <div className="flex justify-between items-end mb-1">
                <span className="text-xs text-white/40 uppercase tracking-widest font-mono">Ensemble Macro F1</span>
                <span className="text-sm font-bold text-purple-400 font-mono">75.0%</span>
              </div>
              <AnimatedBar value={75.0} color="#a855f7" />
            </div>
            <div className="bg-black/60 border border-white/10 p-5 rounded-xl shadow-[inset_0_0_20px_rgba(255,255,255,0.02)] flex flex-col justify-center">
              <div className="text-xs text-white/40 uppercase tracking-widest font-mono mb-1">Single checkpoint</div>
              <div className="text-3xl font-mono font-bold text-white flex items-baseline gap-1">
                70.29 <span className="text-sm text-white/30">%</span>
              </div>
            </div>
          </div>

          <div className="space-y-4 relative z-10 flex-1">
            <div className="border border-white/10 bg-black/40 p-5 rounded-xl backdrop-blur-sm">
              <h4 className="text-xs font-bold text-white/60 uppercase tracking-[0.2em] mb-3 flex items-center gap-2">
                <Server className="w-4 h-4 text-white/40" /> Architecture Specs
              </h4>
              <ul className="text-sm text-white/50 space-y-3 font-mono">
                <li className="flex justify-between"><span className="text-white/30">Pre-trained</span> <span className="text-purple-400">answerdotai/ModernBERT-large</span></li>
                <li className="flex justify-between"><span className="text-white/30">Parameters</span> <span className="text-purple-400">395 Million</span></li>
                <li className="flex justify-between"><span className="text-white/30">Training</span> <span className="text-purple-400">Colab A100 · 40 min/epoch</span></li>
                <li className="flex justify-between"><span className="text-white/30">Ensemble</span> <span className="text-purple-400">seed 42 + seed 7 (greedy)</span></li>
              </ul>
            </div>

            <div className="border border-emerald-500/20 bg-emerald-500/5 p-5 rounded-xl flex items-start gap-4">
              <Activity className="w-6 h-6 text-emerald-500 flex-shrink-0" />
              <div>
                <h4 className="text-xs font-bold text-emerald-500 uppercase tracking-widest mb-1">Calibrated · Locked · Disclosed</h4>
                <p className="text-sm text-white/60 leading-relaxed">
                  Greedy ensemble of 2 variants reached 73.95%. Light temperature calibration (τ=0.2) added 0.09pp. Cross-validated at 73.96% — this is the generalizing number, not the test-tuned 77.51%.
                </p>
              </div>
            </div>
          </div>
        </GlowCard>
      </div>
    </motion.div>
  );
}
