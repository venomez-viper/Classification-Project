"use client";
import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Eye, EyeOff, Lock, User, AlertCircle, Loader2 } from "lucide-react";

function LoginInner() {
  const router       = useRouter();
  const searchParams = useSearchParams();
  const from         = searchParams.get("from") ?? "/ml";

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPw,   setShowPw]   = useState(false);
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState("");
  const [mounted,  setMounted]  = useState(false);

  useEffect(() => setMounted(true), []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!username || !password) return;
    setLoading(true);
    setError("");

    try {
      const res  = await fetch("/api/auth", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();

      if (data.ok) {
        router.push(from);
        router.refresh();
      } else {
        setError("Access denied. Invalid credentials.");
      }
    } catch {
      setError("Connection failed. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-black flex items-center justify-center relative overflow-hidden px-4">

      {/* Background grid */}
      <div className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage: "linear-gradient(rgba(239,68,68,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(239,68,68,0.04) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
        }} />

      {/* Glow orbs */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-red-900/20 blur-[120px] rounded-full pointer-events-none" />
      <div className="absolute bottom-1/4 left-1/4 w-[300px] h-[300px] bg-red-800/10 blur-[100px] rounded-full pointer-events-none" />

      {/* Animated scan line */}
      <motion.div
        className="absolute left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-red-500/30 to-transparent pointer-events-none"
        animate={{ top: ["0%", "100%", "0%"] }}
        transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
      />

      <AnimatePresence>
        {mounted && (
          <motion.div
            initial={{ opacity: 0, y: 24, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
            className="relative w-full max-w-md"
          >
            {/* Card */}
            <div className="relative bg-white/[0.03] backdrop-blur-2xl border border-white/10 rounded-3xl p-8 shadow-[0_0_80px_rgba(239,68,68,0.08)]">

              {/* Corner accents */}
              <div className="absolute top-0 left-0 w-12 h-12 border-t border-l border-red-500/40 rounded-tl-3xl" />
              <div className="absolute bottom-0 right-0 w-12 h-12 border-b border-r border-red-500/40 rounded-br-3xl" />

              {/* Brand */}
              <div className="text-center mb-8">
                <div className="inline-flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-xl bg-red-500/10 border border-red-500/30 flex items-center justify-center">
                    <Lock className="w-5 h-5 text-red-400" />
                  </div>
                </div>
                <h1 className="text-4xl font-black text-white tracking-[0.15em] uppercase">TAVSS</h1>
                <p className="text-xs font-mono text-red-500/50 mt-2 tracking-[0.3em] uppercase">
                  Restricted Access · Authorize to Continue
                </p>
                <div className="mt-3 flex items-center justify-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-[10px] font-mono text-emerald-400/60">System Online</span>
                </div>
              </div>

              {/* Form */}
              <form onSubmit={handleSubmit} className="space-y-4">

                {/* Username */}
                <div className="space-y-1.5">
                  <label className="text-[10px] font-mono text-white/30 uppercase tracking-widest">Username</label>
                  <div className="relative">
                    <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20" />
                    <input
                      type="text"
                      value={username}
                      onChange={e => setUsername(e.target.value)}
                      autoComplete="username"
                      spellCheck={false}
                      placeholder="Enter username"
                      className="w-full pl-10 pr-4 py-3.5 bg-black/40 border border-white/8 rounded-xl text-white text-sm font-mono placeholder:text-white/15 focus:outline-none focus:border-red-500/40 focus:bg-black/60 transition-all"
                      style={{ borderColor: error ? "rgba(239,68,68,0.3)" : undefined }}
                    />
                  </div>
                </div>

                {/* Password */}
                <div className="space-y-1.5">
                  <label className="text-[10px] font-mono text-white/30 uppercase tracking-widest">Access Code</label>
                  <div className="relative">
                    <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20" />
                    <input
                      type={showPw ? "text" : "password"}
                      value={password}
                      onChange={e => setPassword(e.target.value)}
                      autoComplete="current-password"
                      placeholder="••••••••"
                      className="w-full pl-10 pr-12 py-3.5 bg-black/40 border border-white/8 rounded-xl text-white text-sm font-mono placeholder:text-white/15 focus:outline-none focus:border-red-500/40 focus:bg-black/60 transition-all"
                      style={{ borderColor: error ? "rgba(239,68,68,0.3)" : undefined }}
                    />
                    <button type="button" onClick={() => setShowPw(p => !p)}
                      className="absolute inset-y-0 right-0 flex items-center px-3.5 text-white/20 hover:text-white/50 transition-colors">
                      {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {/* Error */}
                <AnimatePresence>
                  {error && (
                    <motion.div
                      initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                      className="flex items-center gap-2 px-3 py-2.5 bg-red-500/8 border border-red-500/20 rounded-lg"
                    >
                      <AlertCircle className="w-3.5 h-3.5 text-red-400 flex-shrink-0" />
                      <span className="text-xs font-mono text-red-400">{error}</span>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Submit */}
                <button
                  type="submit"
                  disabled={loading || !username || !password}
                  className="w-full py-4 mt-2 rounded-xl font-mono font-bold text-sm tracking-[0.2em] uppercase transition-all flex items-center justify-center gap-3 disabled:opacity-30 disabled:cursor-not-allowed relative overflow-hidden group"
                  style={{
                    background: "linear-gradient(135deg, rgba(239,68,68,0.15), rgba(185,28,28,0.1))",
                    border: "1px solid rgba(239,68,68,0.35)",
                    color: "#f87171",
                    boxShadow: "0 0 40px rgba(239,68,68,0.1)",
                  }}
                >
                  {/* Shimmer on hover */}
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700" />
                  {loading
                    ? <><Loader2 className="w-4 h-4 animate-spin" /> Authenticating...</>
                    : <>Authorize Access →</>}
                </button>
              </form>

              {/* Footer */}
              <div className="mt-6 pt-5 border-t border-white/5 text-center">
                <p className="text-[9px] font-mono text-white/15 uppercase tracking-widest">
                  TAVSS · MGT 599 Capstone · DePaul University Chicago
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-black flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-red-500 animate-spin" />
      </div>
    }>
      <LoginInner />
    </Suspense>
  );
}
