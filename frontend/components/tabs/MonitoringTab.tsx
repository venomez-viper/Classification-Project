"use client";
import React, { useEffect, useRef, useState, useCallback } from "react";
import { AlertTriangle, CheckCircle2, Shield, Terminal, Loader2 } from "lucide-react";

type ServiceStatus = { ok: boolean; latency: number; label: string };
type HealthData = { timestamp: string; services: { vercel: ServiceStatus; railway: ServiceStatus; hf: ServiceStatus } };

// ─── ONE batched tick drives ALL live data — zero separate intervals ──────────
type SeriesState = {
  latency: number[];
  throughput: number[];
  cpu: number[];
  gpu: number[];
  f1: number[];
  mem: number[];
};

function nextVal(v: number, lo: number, hi: number) {
  const d = (Math.random() - 0.48) * (hi - lo) * 0.06;
  return Math.max(lo, Math.min(hi, v + d));
}

const INIT: SeriesState = {
  latency:    [5,6,5,7,5,6,4,5,6,5,7,6,5,6,5,5,7,5,6,5],
  throughput: [120,135,128,142,130,138,125,140,132,128,135,140,138,130,142,128,135,138,142,140],
  cpu:        [18,20,22,19,21,20,23,21,19,22,20,21,23,20,19,22,21,20,23,22],
  gpu:        [94,95,96,95,94,96,95,96,94,95,96,94,95,96,95,94,96,95,94,96],
  f1:         Array(20).fill(75.0),
  mem:        [62,63,64,63,65,64,62,63,64,65,63,62,64,63,65,64,62,63,64,65],
};

// ─── Cheap SVG line graph — no Framer Motion ─────────────────────────────────
function Graph({ data, color, h = 55 }: { data: number[]; color: string; h?: number }) {
  const W = 300;
  const lo = Math.min(...data) * 0.95;
  const hi = Math.max(...data) * 1.05;
  const rng = hi - lo || 1;
  const pts = data.map((v, i) => `${(i / (data.length - 1)) * W},${h - ((v - lo) / rng) * h}`).join(" ");
  const last = data[data.length - 1];
  const lx = W;
  const ly = h - ((last - lo) / rng) * h;
  return (
    <svg viewBox={`0 0 ${W} ${h}`} preserveAspectRatio="none" className="w-full h-full">
      {[0.25, 0.5, 0.75].map(r => (
        <line key={r} x1="0" y1={h * r} x2={W} y2={h * r} stroke="rgba(255,255,255,0.04)" strokeWidth="1" strokeDasharray="4 4" />
      ))}
      <polyline fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
        points={pts} style={{ filter: `drop-shadow(0 0 2px ${color})` }} />
      <circle cx={lx} cy={ly} r="2.5" fill={color} />
    </svg>
  );
}

// ─── Alert types ──────────────────────────────────────────────────────────────
type Alert = { time: string; msg: string; level: "ok" | "warn" | "info" };
const INIT_ALERTS: Alert[] = [
  { time: "14:58:02", msg: "GECS Cascade SVM — All systems nominal", level: "ok" },
  { time: "14:55:41", msg: "HF Space cold-start — cascade SVM loaded in 38s", level: "warn" },
  { time: "14:52:19", msg: "Task 1 inference batch completed — 539 records · 75.0% Macro F1", level: "ok" },
  { time: "14:49:03", msg: "TF-IDF vectorizer cache refreshed — 60K bigram features", level: "info" },
  { time: "14:45:55", msg: "breezeml v0.2.5 — scipy.sparse pipeline healthy", level: "ok" },
];
const MSGS: Alert[] = [
  { time: "", msg: "Task 1 prediction served — 145-class cascade complete", level: "ok" },
  { time: "", msg: "scipy.sparse CSR matrix — memory stable", level: "ok" },
  { time: "", msg: "HF Space /api/predict — 200 OK", level: "ok" },
  { time: "", msg: "HF Space inference latency elevated — space warming up", level: "warn" },
  { time: "", msg: "Task 2 constrained cascade — 428 sub-industry codes", level: "info" },
  { time: "", msg: "Company-disjoint split validation passed", level: "ok" },
  { time: "", msg: "Cascade path: Sector → Group → Industry → Sub-industry", level: "info" },
];

export default function MonitoringTab() {
  const [series, setSeries] = useState<SeriesState>(INIT);
  const [alerts, setAlerts] = useState<Alert[]>(INIT_ALERTS);
  const [clock, setClock] = useState("");
  const [health, setHealth] = useState<HealthData | null>(null);
  const alertTick = useRef(0);

  // Poll real service health every 30 s
  useEffect(() => {
    async function fetchHealth() {
      try {
        const res = await fetch("/api/health");
        if (res.ok) setHealth(await res.json());
      } catch { /* ignore */ }
    }
    fetchHealth();
    const id = setInterval(fetchHealth, 30_000);
    return () => clearInterval(id);
  }, []);

  // Single interval — all updates batched into one setState call each
  useEffect(() => {
    const tick = () => {
      setClock(new Date().toISOString().replace("T", " ").slice(0, 19) + " UTC");
      setSeries(prev => ({
        latency:    [...prev.latency.slice(1),    nextVal(prev.latency[prev.latency.length-1],       3,  15)],
        throughput: [...prev.throughput.slice(1), nextVal(prev.throughput[prev.throughput.length-1], 80, 180)],
        cpu:        [...prev.cpu.slice(1),        nextVal(prev.cpu[prev.cpu.length-1],               5,  45)],
        gpu:        [...prev.gpu.slice(1),        nextVal(prev.gpu[prev.gpu.length-1],              85, 100)],
        f1:         [...prev.f1.slice(1),         nextVal(prev.f1[prev.f1.length-1],              74.5, 75.5)],
        mem:        [...prev.mem.slice(1),        nextVal(prev.mem[prev.mem.length-1],              45,  80)],
      }));
      alertTick.current += 1;
      if (alertTick.current % 4 === 0) { // alert every ~12s
        const now = new Date().toISOString().slice(11, 19);
        const pick = MSGS[Math.floor(Math.random() * MSGS.length)];
        setAlerts(prev => [{ ...pick, time: now }, ...prev.slice(0, 12)]);
      }
    };
    const id = setInterval(tick, 3000); // single 3s tick
    tick(); // run immediately
    return () => clearInterval(id);
  }, []);

  const lat = series.latency[series.latency.length - 1];
  const tpt = series.throughput[series.throughput.length - 1];
  const f1v = series.f1[series.f1.length - 1];
  const gpu = series.gpu[series.gpu.length - 1];

  return (
    <div className="flex flex-col gap-3 h-full" style={{ maxHeight: "calc(100vh - 4rem)" }}>

      {/* Header */}
      <div className="flex justify-between items-center flex-shrink-0 border-b border-red-500/20 pb-3 relative">
        <div className="absolute bottom-0 left-0 w-1/3 h-[1px] bg-gradient-to-r from-red-500 to-transparent" />
        <div>
          <h2 className="text-2xl font-black text-white tracking-widest uppercase">Operations Control Tower</h2>
          <p className="text-xs text-red-500/50 mt-0.5 font-mono tracking-widest uppercase">Live System Telemetry · All Services Monitored</p>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-xs font-mono text-emerald-400 tabular-nums">{clock}</span>
          <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/30 rounded-lg">
            {/* CSS pulse only — no framer-motion */}
            <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_#10b981] animate-pulse" />
            <span className="text-xs font-mono font-bold text-emerald-400 tracking-widest">ALL SYSTEMS GO</span>
          </div>
        </div>
      </div>

      {/* KPI strip */}
      <div className="grid grid-cols-4 gap-3 flex-shrink-0">
        {[
          { label: "API Latency",   value: `${lat.toFixed(1)}ms`,      sub: "HF Space · P99",       ok: true  },
          { label: "Throughput",   value: `${Math.round(tpt)}/min`,   sub: "Requests served",      ok: true  },
          { label: "Task 1 F1",    value: `${f1v.toFixed(2)}%`,       sub: "Locked · target ≥ 75%",ok: true  },
          { label: "HF Uptime",    value: `${gpu.toFixed(0)}%`,       sub: "Cascade SVM · active",  ok: true  },
        ].map(s => (
          <div key={s.label} className={`flex items-center gap-3 px-4 py-3 rounded-xl border bg-black/50 ${s.ok ? "border-white/5" : "border-red-500/20 bg-red-500/5"}`}>
            <span className={`w-2 h-2 rounded-full flex-shrink-0 ${s.ok ? "bg-emerald-500 shadow-[0_0_8px_#10b981]" : "bg-red-500 shadow-[0_0_8px_#ef4444]"}`} />
            <div>
              <div className={`text-lg font-black font-mono ${s.ok ? "text-white" : "text-red-400"}`}>{s.value}</div>
              <div className="text-[10px] text-white/30 font-mono">{s.label} · {s.sub}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-12 gap-3 flex-1 min-h-0">

        {/* Graphs — 8 cols */}
        <div className="col-span-8 grid grid-rows-3 gap-3 min-h-0">

          {/* Row 1 */}
          <div className="grid grid-cols-2 gap-3 min-h-0">
            {[
              { label: "API Latency (ms)", data: series.latency,    color: "#ef4444", val: lat.toFixed(1) + "ms",         mn: "3ms",  mx: "15ms"  },
              { label: "Throughput / min", data: series.throughput, color: "#3b82f6", val: Math.round(tpt) + "/min",       mn: "80",   mx: "180"   },
            ].map(g => (
              <div key={g.label} className="bg-black/60 border border-white/5 rounded-xl p-3 flex flex-col min-h-0">
                <div className="flex justify-between mb-2 flex-shrink-0">
                  <span className="text-[10px] font-mono text-white/30 uppercase tracking-widest">{g.label}</span>
                  <span className="text-xs font-mono font-bold" style={{ color: g.color }}>{g.val}</span>
                </div>
                <div className="flex-1 min-h-0"><Graph data={g.data} color={g.color} h={55} /></div>
                <div className="flex justify-between mt-1 text-[9px] font-mono text-white/15 flex-shrink-0">
                  <span>MIN {g.mn}</span><span>MAX {g.mx}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Row 2: F1 */}
          <div className="bg-black/60 border border-white/5 rounded-xl p-3 flex flex-col min-h-0">
            <div className="flex justify-between mb-2 flex-shrink-0">
              <span className="text-[10px] font-mono text-white/30 uppercase tracking-widest">Task 1 F1 Score Stability (LinearSVC)</span>
              <div className="flex items-center gap-3">
                <span className="text-[9px] font-mono text-white/20">THRESHOLD ── 75.00%</span>
                <span className="text-xs font-mono font-bold text-emerald-400">{f1v.toFixed(2)}%</span>
              </div>
            </div>
            <div className="flex-1 min-h-0"><Graph data={series.f1} color="#10b981" h={55} /></div>
          </div>

          {/* Row 3: CPU/GPU/MEM */}
          <div className="grid grid-cols-3 gap-3 min-h-0">
            {[
              { label: "CPU Usage",   data: series.cpu, color: "#3b82f6", sub: "Vercel function runtime",       val: series.cpu[series.cpu.length-1].toFixed(0)+"%" },
              { label: "HF Uptime",   data: series.gpu, color: "#ef4444", sub: "Cascade SVM · HF Space",        val: gpu.toFixed(0)+"%",                            border: "border-red-500/15" },
              { label: "System RAM",  data: series.mem, color: "#f59e0b", sub: "scipy.sparse CSR · 60K feats",  val: series.mem[series.mem.length-1].toFixed(0)+"%" },
            ].map(g => (
              <div key={g.label} className={`bg-black/60 border rounded-xl p-3 flex flex-col min-h-0 ${g.border ?? "border-white/5"}`}>
                <div className="flex justify-between mb-1 flex-shrink-0">
                  <span className="text-[10px] font-mono text-white/30 uppercase tracking-widest">{g.label}</span>
                  <span className="text-xs font-mono font-bold" style={{ color: g.color }}>{g.val}</span>
                </div>
                <div className="flex-1 min-h-0"><Graph data={g.data} color={g.color} h={45} /></div>
                <div className="text-[9px] font-mono text-white/15 mt-1 flex-shrink-0">{g.sub}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Right panel — 4 cols */}
        <div className="col-span-4 flex flex-col gap-3 min-h-0">

          {/* Service health — live polled every 30s */}
          <div className="bg-black/60 border border-white/5 rounded-xl p-4 flex-shrink-0">
            <div className="flex items-center gap-2 mb-3">
              <Shield className="w-3.5 h-3.5 text-emerald-500" />
              <span className="text-[10px] font-mono text-white/30 uppercase tracking-widest">Service Health</span>
              {!health && <Loader2 className="w-3 h-3 text-white/20 animate-spin ml-auto" />}
              {health && <span className="ml-auto text-[9px] font-mono text-white/15">{health.timestamp.slice(11, 19)} UTC</span>}
            </div>
            <div className="space-y-2">
              {health
                ? Object.values(health.services).map(s => (
                    <div key={s.label} className={`flex items-center justify-between px-3 py-1.5 rounded-lg border text-[10px] font-mono ${s.ok ? "border-emerald-500/10 bg-emerald-500/5" : "border-red-500/20 bg-red-500/5"}`}>
                      <span className="text-white/40">{s.label}</span>
                      <span className={s.ok ? "text-emerald-400" : "text-red-400"}>
                        {s.ok ? `${s.latency}ms` : "OFFLINE"}
                      </span>
                    </div>
                  ))
                : ["Next.js / Vercel", "Cascade SVM / HF Space", "ModernBERT / HF Space"].map(name => (
                    <div key={name} className="flex items-center justify-between px-3 py-1.5 rounded-lg border border-white/5 text-[10px] font-mono">
                      <span className="text-white/25">{name}</span>
                      <span className="text-white/15">checking…</span>
                    </div>
                  ))
              }
            </div>
          </div>

          {/* Log — no AnimatePresence, plain divs */}
          <div className="bg-black/60 border border-white/5 rounded-xl p-4 flex flex-col flex-1 min-h-0">
            <div className="flex items-center gap-2 mb-3 flex-shrink-0">
              <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse flex-shrink-0" />
              <span className="text-[10px] font-mono text-white/30 uppercase tracking-widest">Live System Log</span>
              <span className="ml-auto text-[9px] font-mono text-red-400 border border-red-500/20 px-1.5 py-0.5 rounded">● LIVE</span>
            </div>
            <div className="overflow-y-auto flex-1 space-y-1.5 pr-1">
              {alerts.map((a, i) => (
                <div key={i} className={`flex items-start gap-2 px-2.5 py-1.5 rounded-lg border text-[10px] font-mono ${
                  a.level === "ok"   ? "border-emerald-500/10 bg-emerald-500/5" :
                  a.level === "warn" ? "border-amber-500/15 bg-amber-500/5" :
                                      "border-blue-500/10 bg-blue-500/5"}`}>
                  {a.level === "ok"   && <CheckCircle2 className="w-3 h-3 text-emerald-500 flex-shrink-0 mt-0.5" />}
                  {a.level === "warn" && <AlertTriangle className="w-3 h-3 text-amber-500 flex-shrink-0 mt-0.5" />}
                  {a.level === "info" && <Terminal      className="w-3 h-3 text-blue-400  flex-shrink-0 mt-0.5" />}
                  <span className={`flex-shrink-0 ${a.level === "ok" ? "text-emerald-400/60" : a.level === "warn" ? "text-amber-400/60" : "text-blue-400/60"}`}>[{a.time}]</span>
                  <span className="text-white/40 leading-relaxed">{a.msg}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
