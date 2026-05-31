"use client";
import { SparklesCore } from "@/components/ui/sparkles";
import { FallingPattern } from "@/components/ui/falling-pattern";
import { TextScramble } from "@/components/ui/text-scramble";
import { motion } from "framer-motion";
import { ChevronDown } from "lucide-react";
import { useEffect, useState } from "react";

const STATS = [
  { label: "GECS Industries", value: 145, suffix: "" },
  { label: "Sub-Industries", value: 428, suffix: "" },
  { label: "Training Segments", value: 53587, suffix: "+" },
  { label: "Locked Task 1 F1", value: 75.0, suffix: "%", decimal: true },
];

function AnimatedCounter({ target, suffix, decimal = false }: { target: number; suffix: string; decimal?: boolean }) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    const duration = 2000;
    const steps = 60;
    const increment = target / steps;
    let current = 0;
    const timer = setInterval(() => {
      current = Math.min(current + increment, target);
      setVal(current);
      if (current >= target) clearInterval(timer);
    }, duration / steps);
    return () => clearInterval(timer);
  }, [target]);
  return <>{decimal ? val.toFixed(2) : Math.round(val).toLocaleString()}{suffix}</>;
}

export default function Hero() {
  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden">
      <div className="absolute inset-0 z-0">
        <FallingPattern 
          color="rgba(220, 38, 38, 0.4)" 
          backgroundColor="rgba(0, 0, 0, 0)" 
          blurIntensity="0.5px" 
          duration={80} 
          className="absolute inset-0 opacity-50"
        />
        <SparklesCore
          id="hero-sparkles"
          background="transparent"
          minSize={0.4}
          maxSize={1.4}
          particleDensity={120}
          className="absolute inset-0 w-full h-full"
          particleColor="#dc2626"
          speed={0.6}
        />
        <div className="absolute inset-0 [mask-image:radial-gradient(ellipse_80%_50%_at_50%_0%,black,transparent)] bg-black/40" />
      </div>

      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[700px] h-[400px] bg-red-700/20 blur-[120px] rounded-full pointer-events-none" />

      <div className="relative z-10 text-center px-6 max-w-5xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-red-600/30 bg-red-600/10 text-red-400 text-sm font-medium mb-8"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
          <TextScramble as="span" speed={0.025} duration={1} characterSet="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .">
            MGT 599 Capstone . Morningstar RED Team . Group 4
          </TextScramble>
        </motion.div>

        {/* TAVSS acronym breakdown */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.28 }}
          className="mb-6"
        >
          <div className="inline-flex items-end gap-0 font-black tracking-[-0.02em] text-6xl sm:text-8xl lg:text-9xl select-none">
            {[
              { letter: "T", word: "Taxonomy",     color: "from-red-400 to-red-500" },
              { letter: "A", word: "Aware",         color: "from-orange-400 to-red-400" },
              { letter: "V", word: "Venture",       color: "from-amber-300 to-orange-400" },
              { letter: "S", word: "Segmentation",  color: "from-cyan-400 to-blue-400" },
              { letter: "S", word: "System",        color: "from-blue-400 to-violet-500" },
            ].map(({ letter, color }, i) => (
              <motion.span
                key={i}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.32 + i * 0.07 }}
                className={`bg-gradient-to-b ${color} bg-clip-text text-transparent`}
              >
                {letter}
              </motion.span>
            ))}
          </div>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.75 }}
            className="mt-3 flex items-center justify-center gap-2 flex-wrap"
          >
            {["Taxonomy", "Aware", "Venture", "Segmentation", "System"].map((word, i) => (
              <span key={word} className="flex items-center gap-2">
                <span className="text-xs sm:text-sm font-semibold tracking-[0.18em] uppercase text-white/50">{word}</span>
                {i < 4 && <span className="text-white/20 text-xs">·</span>}
              </span>
            ))}
          </motion.div>
        </motion.div>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="text-lg sm:text-xl text-white/50 max-w-2xl mx-auto mb-12"
        >
          An audited GECS-Sage cascade built on{" "}
          <span className="text-red-500 font-semibold">breezeml</span>{" "}
          and Morningstar taxonomy grounding. Ships a locked{" "}
          <span className="text-white/80">ModernBERT ensemble (75.0% F1)</span>, a{" "}
          <span className="text-white/80">constrained Task 2 cascade</span>, ensuring highly trustworthy results.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.65 }}
          className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-12"
        >
          {STATS.map((stat) => (
            <div
              key={stat.label}
              className="bg-white/5 border border-white/10 rounded-2xl px-5 py-5 backdrop-blur-sm"
            >
              <div className="text-3xl font-bold text-white font-mono mb-1">
                <AnimatedCounter target={stat.value} suffix={stat.suffix} decimal={stat.decimal} />
              </div>
              <div className="text-xs text-white/40 uppercase tracking-wider">
                <TextScramble as="span" speed={0.015} duration={0.6}>{stat.label}</TextScramble>
              </div>
            </div>
          ))}
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="flex flex-wrap items-center justify-center gap-3"
        >
          <a
            href="/login"
            className="px-7 py-3.5 rounded-xl bg-red-700 hover:bg-red-600 text-white font-semibold text-sm transition-all hover:-translate-y-0.5 hover:shadow-[0_0_30px_rgba(220,38,38,0.4)]"
          >
            <TextScramble as="span" speed={0.02} duration={0.5}>Launch TAVSS App</TextScramble>
          </a>
          <a
            href="/about"
            className="px-7 py-3.5 rounded-xl border border-white/15 hover:border-white/30 text-white/70 hover:text-white font-semibold text-sm transition-all"
          >
            About the Project
          </a>
        </motion.div>
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.2 }}
        className="absolute bottom-8 left-1/2 -translate-x-1/2 text-white/30 animate-bounce"
      >
        <ChevronDown className="w-6 h-6" />
      </motion.div>
    </section>
  );
}
