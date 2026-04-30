import React from "react";
import { motion } from "framer-motion";
import { TrendingUp, Package, Code, ArrowUpRight } from "lucide-react";
import { GlowCard } from "@/components/ui/spotlight-card";
import { TextScramble } from "@/components/ui/text-scramble";

export default function TrainingTab() {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }} 
      animate={{ opacity: 1, y: 0 }} 
      exit={{ opacity: 0 }} 
      transition={{ duration: 0.4 }} 
      className="max-w-[1400px] mx-auto pb-12 space-y-8"
    >
      <div className="flex justify-between items-end mb-8 border-b border-red-500/20 pb-4 relative">
        <div className="absolute bottom-0 left-0 w-1/3 h-[1px] bg-gradient-to-r from-red-500 to-transparent" />
        <div>
          <TextScramble as="h2" speed={0.02} duration={0.8} className="text-3xl font-black text-white tracking-widest uppercase text-shadow-red">
            Training & Engineering
          </TextScramble>
          <p className="text-sm text-red-500/50 mt-1 font-mono tracking-widest uppercase">breezeml Library Development & Hyperparameter Tuning</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
        
        {/* breezeml library */}
        <GlowCard glowColor="blue" className="p-8 border-white/10 bg-[#060606]/80 backdrop-blur-xl relative overflow-hidden flex flex-col">
          <div className="absolute -top-20 -left-20 w-[300px] h-[300px] bg-white/5 blur-[80px] rounded-full pointer-events-none" />
          
          <div className="flex items-center gap-5 mb-8 relative z-10 border-b border-white/5 pb-6">
            <div className="w-16 h-16 rounded-xl bg-white/5 flex items-center justify-center border border-white/10 shadow-[0_0_20px_rgba(255,255,255,0.05)]">
              <Package className="w-8 h-8 text-white/80" />
            </div>
            <div>
              <div className="text-xs font-bold text-white/40 tracking-[0.3em] uppercase mb-1">Open Source Package</div>
              <h3 className="text-3xl font-black text-white tracking-tight">breezeml v0.2.5</h3>
            </div>
          </div>
          
          <p className="text-sm text-white/60 leading-relaxed mb-8 relative z-10">
            To handle the extreme computational constraints of tracking 145 financial sectors across 50,000 dimensions, we built and published our own Python library. By abstracting the heavy lifting to C-level <code>scipy.sparse</code> operations, we bypassed the Waitress 503 deployment bottlenecks entirely.
          </p>
          
          <div className="bg-black/80 border border-white/10 rounded-xl p-5 shadow-[inset_0_0_20px_rgba(255,255,255,0.02)] relative z-10 flex-1">
            <div className="text-[10px] text-white/30 uppercase tracking-widest font-mono mb-3">Release History</div>
            <div className="space-y-3">
              {[
                { v: "v0.1.0", desc: "Initial dense matrix pipeline. (Failed at scale)" },
                { v: "v0.2.1", desc: "joblib parallelization patch. (Improved CPU util)" },
                { v: "v0.2.5", desc: "Native scipy.sparse CSR support. (Memory optimized)" }
              ].map((log, i) => (
                <div key={i} className="text-xs font-mono text-white/50 border border-white/5 p-3 rounded-lg flex items-start gap-3 bg-white/[0.02] hover:bg-white/[0.05] transition-colors cursor-default">
                  <Code className={`w-4 h-4 mt-0.5 flex-shrink-0 ${i === 2 ? 'text-emerald-500' : 'text-white/30'}`} />
                  <div>
                    <span className={`font-bold ${i === 2 ? 'text-emerald-400' : 'text-white/70'}`}>{log.v}</span> - {log.desc}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </GlowCard>

        {/* F1 Breakthrough */}
        <GlowCard glowColor="emerald" className="p-8 border-emerald-500/20 bg-[#060606]/80 backdrop-blur-xl relative overflow-hidden flex flex-col">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[400px] bg-emerald-500/10 blur-[100px] rounded-full pointer-events-none" />
          
          <div className="flex items-center gap-5 mb-8 relative z-10 border-b border-emerald-500/10 pb-6">
            <div className="w-16 h-16 rounded-xl bg-emerald-500/10 flex items-center justify-center border border-emerald-500/30 shadow-[0_0_20px_rgba(16,185,129,0.2)]">
              <TrendingUp className="w-8 h-8 text-emerald-500" />
            </div>
            <div>
              <div className="text-xs font-bold text-emerald-500 tracking-[0.3em] uppercase mb-1">Hyperparameter Breakthrough</div>
              <h3 className="text-3xl font-black text-white tracking-tight">Class Balancing</h3>
            </div>
          </div>

          <div className="flex items-center gap-6 mb-8 relative z-10">
            <div className="bg-black/60 border border-red-500/20 p-6 rounded-xl flex-1 text-center shadow-[inset_0_0_20px_rgba(239,68,68,0.05)]">
              <div className="text-xs text-red-400/50 uppercase tracking-widest font-mono mb-2">Before (Unbalanced)</div>
              <div className="text-4xl font-mono font-bold text-red-500 drop-shadow-[0_0_10px_rgba(239,68,68,0.5)]">43.0%</div>
            </div>
            <ArrowUpRight className="w-10 h-10 text-emerald-500 flex-shrink-0 animate-pulse" />
            <div className="bg-emerald-950/30 border border-emerald-500/40 p-6 rounded-xl flex-1 text-center shadow-[inset_0_0_30px_rgba(16,185,129,0.15)] relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-emerald-500/10 to-transparent animate-[shimmer_2s_infinite]" />
              <div className="text-xs text-emerald-400/70 uppercase tracking-widest font-mono mb-2 relative z-10">After (Balanced)</div>
              <div className="text-4xl font-mono font-bold text-emerald-400 drop-shadow-[0_0_15px_rgba(16,185,129,0.8)] relative z-10">86.8%</div>
            </div>
          </div>

          <div className="bg-black/80 border border-emerald-500/10 rounded-xl p-5 shadow-[inset_0_0_20px_rgba(0,0,0,0.5)] relative z-10 flex-1">
            <p className="text-sm text-emerald-100/60 leading-relaxed font-mono">
              <span className="text-emerald-500 font-bold">LOG:</span> The dataset's severe long-tail distribution completely crippled standard accuracy metrics. By implementing <code>class_weight='balanced'</code> in the LinearSVC engine, the algorithm dynamically penalized major sectors. This forced it to learn the minority sub-industries, immediately doubling the true Macro F1 score.
            </p>
          </div>
        </GlowCard>
      </div>
    </motion.div>
  );
}
