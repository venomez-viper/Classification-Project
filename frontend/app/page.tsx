"use client";

import Link from "next/link";
import { motion } from "framer-motion";

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-black flex flex-col items-center justify-center relative overflow-hidden">
      {/* Ambient glow */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-red-600/10 blur-[120px]" />
      </div>

      {/* Content */}
      <motion.div
        className="relative z-10 flex flex-col items-center text-center px-6 max-w-2xl"
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, ease: "easeOut" }}
      >
        {/* Badge */}
        <span className="mb-6 inline-flex items-center gap-2 rounded-full border border-red-500/30 bg-red-500/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-widest text-red-400">
          MGT 599 · Group 4 · DePaul University
        </span>

        {/* Logo / name */}
        <h1 className="text-6xl sm:text-7xl font-black text-white tracking-tight leading-none mb-4">
          TAVSS
        </h1>

        {/* Full form */}
        <p className="text-sm text-white/30 uppercase tracking-[0.25em] mb-6">
          Text-Augmented Value & Sector System
        </p>

        {/* Description */}
        <p className="text-base text-white/55 leading-relaxed mb-10">
          An end-to-end MLOps platform for Morningstar GECS industry
          classification. Powered by fine-tuned DeBERTa-v3 and Linear SVM
          models trained on 35,000+ corporate descriptions.
        </p>

        {/* CTA */}
        <Link
          href="/login"
          className="group relative inline-flex items-center gap-3 rounded-full bg-red-600 hover:bg-red-500 px-8 py-3.5 text-sm font-bold text-white transition-all duration-200 shadow-lg shadow-red-900/40 hover:shadow-red-700/50"
        >
          Enter System
          <span className="transition-transform duration-200 group-hover:translate-x-1">
            →
          </span>
        </Link>

        {/* Subtle metrics */}
        <div className="mt-16 flex gap-10 text-center">
          {[
            { value: "86.82%", label: "Task 1 Macro F1" },
            { value: "78.10%", label: "DeBERTa F1" },
            { value: "35k+", label: "Training Samples" },
          ].map((m) => (
            <div key={m.label}>
              <p className="text-2xl font-black text-white">{m.value}</p>
              <p className="text-xs text-white/30 mt-1">{m.label}</p>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Footer */}
      <p className="absolute bottom-6 text-xs text-white/15">
        Spring 2026 · Capstone Project
      </p>
    </main>
  );
}
