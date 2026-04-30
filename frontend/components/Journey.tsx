"use client";
import { motion } from "framer-motion";
import { ServerCrash, Cpu, AlertTriangle, Wrench, CheckCircle2 } from "lucide-react";
import { GlowCard } from "@/components/ui/spotlight-card";
import { TextScramble } from "@/components/ui/text-scramble";

const PHASES = [
  {
    icon: ServerCrash,
    title: "Phase 1: The Infrastructure Hurdle",
    description: "Our initial attempt to fine-tune a 180-million parameter LLM (DeBERTa-v3-small) started on Google Colab. However, the sheer size of the dataset (42,000+ rows) caused training epochs to exceed 1 hour. Colab repeatedly terminated our instances due to timeout constraints, forcing a complete pivot in our engineering strategy.",
    glow: "red",
    delay: 0.1
  },
  {
    icon: Cpu,
    title: "Phase 2: Local GPU Optimization",
    description: "We transitioned the entire LLM pipeline to a local Windows environment with a single RTX 3050 (4GB VRAM). To prevent Out-Of-Memory (OOM) crashes, we rewrote the PyTorch training loop to implement Gradient Accumulation (simulating large batch sizes) and aggressive CUDA cache clearing.",
    glow: "blue",
    delay: 0.2
  },
  {
    icon: AlertTriangle,
    title: "Phase 3: The Data Problem",
    description: "Despite successful local training, the model's Macro F1 score flatlined around 63%. We discovered that the extreme 145-class imbalance caused the neural network to completely ignore rare industries. With some classes having thousands of examples and others having fewer than 5, the model was statistically incentivized to be 'lazy'.",
    glow: "amber",
    delay: 0.3
  },
  {
    icon: Wrench,
    title: "Phase 4: Programmatic Augmentation",
    description: "To combat the imbalance, we engineered a secondary data track. We deployed a local 'flan-t5-base' model to programmatically expand 421 short descriptions for minority classes into rich, 3-sentence profiles. We paired this augmented dataset with Custom PyTorch Class Weights in the CrossEntropyLoss function to mathematically force the model to penalize errors on rare classes.",
    glow: "purple",
    delay: 0.4
  },
  {
    icon: CheckCircle2,
    title: "Phase 5: The Final Verdict",
    description: "The final result: DeBERTa LLM reached 64.00% Macro F1. The classic TF-IDF + Linear SVM pipeline achieved 86.82%. In a real-world business context, this proves that complex Generative AI is not always the solution. We saved hypothetical compute thousands of dollars by proving a simpler, highly-efficient SVM is the superior production choice for highly-specific jargon classification.",
    glow: "emerald",
    delay: 0.5
  }
];

export default function Journey() {
  return (
    <section className="min-h-screen py-24 px-6 overflow-hidden relative">
      {/* Background accents */}
      <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-red-900/10 blur-[120px] rounded-full pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-blue-900/10 blur-[120px] rounded-full pointer-events-none" />

      <div className="max-w-4xl mx-auto relative z-10">
        
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-20 text-center"
        >
          <TextScramble
            as="p"
            speed={0.02}
            duration={0.8}
            className="text-red-500 text-sm font-semibold uppercase tracking-[0.3em] mb-4"
          >
            Case Study
          </TextScramble>
          <h1 className="text-5xl sm:text-6xl font-bold text-white mb-6 tracking-tight">
            The LLM <span className="text-transparent bg-clip-text bg-gradient-to-r from-red-500 to-rose-400">Journey</span>
          </h1>
          <p className="text-white/50 text-xl max-w-2xl mx-auto leading-relaxed">
            Documenting the engineering hurdles, the optimization strategies, and the hard truths of forcing Deep Learning onto extreme class imbalance.
          </p>
        </motion.div>

        {/* Timeline */}
        <div className="relative">
          {/* Vertical Line */}
          <div className="absolute left-[27px] top-4 bottom-4 w-0.5 bg-gradient-to-b from-red-500/50 via-white/10 to-emerald-500/50 hidden md:block" />

          <div className="flex flex-col gap-12">
            {PHASES.map((phase, i) => (
              <motion.div 
                key={i}
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, margin: "-100px" }}
                transition={{ duration: 0.6, delay: phase.delay }}
                className="relative flex flex-col md:flex-row gap-6 md:gap-12"
              >
                {/* Timeline Icon */}
                <div className="hidden md:flex flex-col items-center z-10">
                  <div className={`w-14 h-14 rounded-full bg-black border border-white/10 flex items-center justify-center shadow-[0_0_20px_rgba(255,255,255,0.05)]`}>
                    <phase.icon className={`w-6 h-6 text-white/70`} />
                  </div>
                </div>

                {/* Content Card */}
                <GlowCard glowColor={phase.glow as any} className="flex-1 p-8 md:p-10 border-white/5 bg-black/40 backdrop-blur-sm">
                  <div className="flex items-center gap-4 mb-4 md:hidden">
                    <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center border border-white/10">
                      <phase.icon className="w-5 h-5 text-white/70" />
                    </div>
                    <h3 className="text-xl font-bold text-white">{phase.title}</h3>
                  </div>
                  
                  <h3 className="hidden md:block text-2xl font-bold text-white mb-4">{phase.title}</h3>
                  <p className="text-white/60 text-lg leading-relaxed font-light">
                    {phase.description}
                  </p>
                </GlowCard>
              </motion.div>
            ))}
          </div>
        </div>

      </div>
    </section>
  );
}
