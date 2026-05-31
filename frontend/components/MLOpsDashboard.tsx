"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Activity, LayoutDashboard, Box, Database, TrendingUp, Cpu, ActivitySquare,
  Bell, FileText, Shield, Settings, Search, User, ChevronDown, CheckCircle2,
  AlertTriangle, Info, Play, Layers, GitBranch, Terminal, HardDrive,
  Cpu as CpuIcon, Loader2, BarChart3, LogOut
} from "lucide-react";
import Link from "next/link";
import ModelsTab from "./tabs/ModelsTab";
import TrainingTab from "./tabs/TrainingTab";
import DataPipelinesTab from "./tabs/DataPipelinesTab";
import DeploymentTab from "./tabs/DeploymentTab";
import LLMTestingTab from "./tabs/LLMTestingTab";
import DocumentationTab from "./tabs/DocumentationTab";
import GraphTab from "./tabs/GraphTab";
import CodeTab from "./tabs/CodeTab";
import MonitoringTab from "./tabs/MonitoringTab";
import ReportsTab from "./tabs/ReportsTab";
import AlertsTab from "./tabs/AlertsTab";
import SettingsTab from "./tabs/SettingsTab";
import GovernanceTab from "./tabs/GovernanceTab";

// --- Mock Data ---
const SIDEBAR_ITEMS = [
  { icon: LayoutDashboard, label: "Overview" },
  { icon: Box, label: "Models" },
  { icon: Database, label: "Data Pipelines" },
  { icon: TrendingUp, label: "Training" },
  { icon: ActivitySquare, label: "Deployment (SVM)" },
  { icon: CpuIcon, label: "LLM Testing" },
  { icon: GitBranch, label: "Knowledge Graph" },
  { icon: Terminal, label: "Code Showcase" },
  { icon: Activity, label: "Monitoring" },
  { icon: BarChart3, label: "Reports" },
  { icon: Bell, label: "Alerts" },
  { icon: FileText, label: "Documentation" },
  { icon: Shield, label: "Governance" },
  { icon: Settings, label: "Settings" },
];

const MISSION_STATS = [
  { icon: Box, label: "MODELS", value: "145", sub: "+5 (3.4%)", color: "text-red-500" },
  { icon: ActivitySquare, label: "DEPLOYED", value: "2", sub: "+0 (0.0%)", color: "text-red-400" },
  { icon: TrendingUp, label: "TRAINING", value: "3", sub: "+1 (33%)", color: "text-amber-500" },
  { icon: Database, label: "DATASETS", value: "48", sub: "+2 (4.1%)", color: "text-white/50" },
  { icon: AlertTriangle, label: "ALERTS", value: "12", sub: "View all", color: "text-red-500" },
];

const PIPELINE_STEPS = [
  { label: "Data Ingestion", value: "53K rows", metric: "Company-disjoint split", active: false },
  { label: "Data Validation", value: "98.3%", metric: "CompanyId recovered", active: false },
  { label: "Feature Engineering", value: "123K+", metric: "Feature dimensions", active: false },
  { label: "Model Training", value: "14 runs", metric: "Versions documented", active: true },
  { label: "Evaluation", value: "75.0%", metric: "Locked Macro F1", active: false },
  { label: "Deployment", value: "HF Space", metric: "Live on Vercel", active: false },
  { label: "Monitoring", value: "Healthy", metric: "", active: false },
];

const DEPLOYED_MODELS = [
  { name: "Task 1 Ensemble (Industry)", version: "v7.0.0", status: "Healthy", acc: "75.0%", lat: "28 ms", req: "1.2M", drift: "0.01" },
  { name: "Task 2 (Sub-industry)", version: "v5.0.0", status: "Healthy", acc: "55.44%", lat: "35 ms", req: "890K", drift: "0.03" },
  { name: "ModernBERT-large (HF Space)", version: "v3.0.0", status: "Healthy", acc: "70.29%", lat: "320 ms", req: "12K", drift: "0.04" },
  { name: "TF-IDF Vectoriser", version: "v2.0.0", status: "Healthy", acc: "N/A", lat: "5 ms", req: "2.1M", drift: "0.00" },
];

const EXPERIMENTS = [
  { id: "Exp - 3428", name: "Calibrated Greedy Ensemble ★", score: "75.0%", time: "Locked" },
  { id: "Exp - 3425", name: "Greedy Ensemble (2 variants)", score: "73.95%", time: "Post-pres." },
  { id: "Exp - 3422", name: "ModernBERT-large epoch 3", score: "70.29%", time: "Week 6" },
  { id: "Exp - 3418", name: "V8 Mega-Ensemble (classical)", score: "68.42%", time: "Week 5" },
  { id: "Exp - 3412", name: "V2 Honest Baseline (TF-IDF)", score: "59.65%", time: "Week 4" },
];

// --- SVG Chart Components ---
const MiniLineChart = ({ color, data }: { color: string; data: number[] }) => {
  const max = Math.max(...data);
  const min = Math.min(...data) - 5;
  const range = max - min;
  
  const points = data.map((d, i) => {
    const x = (i / (data.length - 1)) * 100;
    const y = 100 - (((d - min) / range) * 100);
    return `${x},${y}`;
  }).join(" ");

  return (
    <div className="h-16 w-full mt-2 relative">
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="w-full h-full overflow-visible">
        <polyline fill="none" stroke={color} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" points={points} style={{ filter: `drop-shadow(0 4px 6px ${color}40)` }} />
        {data.map((d, i) => (
          <circle key={i} cx={(i / (data.length - 1)) * 100} cy={100 - (((d - min) / range) * 100)} r="2" fill={color} />
        ))}
      </svg>
      <div className="absolute inset-0 flex flex-col justify-between pointer-events-none opacity-10">
        <div className="border-b border-white/50 w-full" />
        <div className="border-b border-white/50 w-full" />
        <div className="border-b border-white/50 w-full" />
      </div>
    </div>
  );
};

const RadialGauge = ({ label, value, color }: { label: string; value: number; color: string }) => {
  const radius = 40;
  const circ = 2 * Math.PI * radius;
  const strokeDasharray = circ;
  const strokeDashoffset = circ - (value / 100) * circ;

  return (
    <div className="flex flex-col items-center">
      <div className="text-xs font-mono text-white/40 mb-2 uppercase tracking-wider">{label}</div>
      <div className="relative w-24 h-24 flex items-center justify-center">
        <svg className="w-full h-full transform -rotate-90">
          <circle cx="48" cy="48" r={radius} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
          <motion.circle initial={{ strokeDashoffset: circ }} animate={{ strokeDashoffset }} transition={{ duration: 1.5, ease: "easeOut" }} cx="48" cy="48" r={radius} fill="none" stroke={color} strokeWidth="8" strokeLinecap="round" style={{ strokeDasharray, filter: `drop-shadow(0 0 8px ${color}60)` }} />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-xl font-bold font-mono text-white">{value}%</span>
        </div>
      </div>
    </div>
  );
};

// --- Dynamic ML Lifecycle Pipeline ---

function DynamicPipeline() {
  const [active, setActive] = React.useState(3);
  React.useEffect(() => {
    const id = setInterval(() => setActive(prev => (prev + 1) % PIPELINE_STEPS.length), 5000);
    return () => clearInterval(id);
  }, []);
  return (
    <div className="border border-white/10 bg-[#0a0a0a] rounded-xl p-5">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xs font-bold text-white/60 tracking-widest uppercase">ML Lifecycle Pipeline</h2>
        <div className="flex items-center gap-2">
          <motion.span animate={{ opacity: [1, 0.2, 1] }} transition={{ duration: 1, repeat: Infinity }}
            className="w-1.5 h-1.5 rounded-full bg-red-500" />
          <span className="text-[10px] font-mono text-red-400">LIVE</span>
        </div>
      </div>
      <div className="flex items-start justify-between relative px-2">
        <div className="absolute top-5 left-8 right-8 h-[2px] bg-white/5 z-0" />
        <motion.div className="absolute top-[18px] h-[4px] z-0 rounded-full blur-sm bg-red-500"
          style={{ width: 36 }}
          animate={{ left: `${(active / (PIPELINE_STEPS.length - 1)) * 83 + 3}%` }}
          transition={{ duration: 1.4, ease: "easeInOut" }}
        />
        {PIPELINE_STEPS.map((step, i) => {
          const isActive = active === i;
          const isDone = i < active;
          return (
            <div key={i} className="relative z-10 flex flex-col items-center gap-2" style={{ width: `${100 / PIPELINE_STEPS.length}%` }}>
              <motion.div
                animate={{
                  borderColor: isActive ? "rgba(239,68,68,0.8)" : isDone ? "rgba(16,185,129,0.5)" : "rgba(255,255,255,0.1)",
                  backgroundColor: isActive ? "rgba(239,68,68,0.12)" : isDone ? "rgba(16,185,129,0.08)" : "rgba(10,10,10,1)",
                  boxShadow: isActive ? "0 0 20px rgba(239,68,68,0.5)" : isDone ? "0 0 10px rgba(16,185,129,0.25)" : "none",
                }}
                transition={{ duration: 0.9, ease: "easeInOut" }}
                className="w-10 h-10 rounded-xl border flex items-center justify-center"
              >
                {isActive ? <Loader2 className="w-5 h-5 text-red-400 animate-spin" /> :
                 isDone   ? <CheckCircle2 className="w-5 h-5 text-emerald-400" /> :
                            <Box className="w-4 h-4 text-white/20" />}
              </motion.div>
              <div className="text-center px-1">
                <motion.div animate={{ color: isActive ? "#f87171" : isDone ? "#34d399" : "rgba(255,255,255,0.35)" }}
                  transition={{ duration: 0.9, ease: "easeInOut" }}
                  className="text-[9px] font-bold font-mono uppercase tracking-wide leading-tight">
                  {step.label}
                </motion.div>
                <div className="text-[9px] text-white/25 font-mono mt-0.5 leading-tight">{step.value}</div>
                {step.metric && (
                  <motion.div animate={{ opacity: isActive ? 1 : 0.4 }}
                    transition={{ duration: 0.9 }}
                    className="text-[8px] font-mono mt-0.5" style={{ color: isActive ? "#10b981" : "#6b7280" }}>
                    {step.metric}
                  </motion.div>
                )}
              </div>
            </div>
          );
        })}
      </div>
      <div className="mt-5 pt-3 border-t border-white/5 flex items-center gap-3">
        <motion.div key={active} initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }} className="flex items-center gap-2">
          <span className="text-[10px] font-mono text-white/25 uppercase tracking-widest">Current Stage:</span>
          <span className="text-[10px] font-mono text-red-400 font-bold">{PIPELINE_STEPS[active]?.label}</span>
        </motion.div>
        <div className="ml-auto flex gap-1">
          {PIPELINE_STEPS.map((_, i) => (
            <div key={i} className="w-1.5 h-1.5 rounded-full transition-colors duration-300"
              style={{ backgroundColor: i === active ? "#ef4444" : i < active ? "#10b981" : "rgba(255,255,255,0.1)" }} />
          ))}
        </div>
      </div>
    </div>
  );
}

// --- Sub-Views ---

function OverviewTab() {
  return (
    <motion.div key="overview" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.3 }} className="grid grid-cols-12 gap-6 max-w-[1600px] mx-auto pb-12">
      {/* LEFT COLUMN (8 cols) */}
      <div className="col-span-12 xl:col-span-8 flex flex-col gap-6">
        
        {/* Mission Overview */}
        <div className="border border-white/10 bg-[#0a0a0a] rounded-xl p-5">
          <div className="flex justify-between items-center mb-5">
            <h2 className="text-xs font-bold text-white/60 tracking-widest uppercase">Mission Overview</h2>
            <span className="text-[10px] text-white/30">Live overview of key metrics</span>
          </div>
          <div className="grid grid-cols-5 gap-4">
            {MISSION_STATS.map((stat, i) => (
              <div key={i} className="bg-black border border-white/5 rounded-lg p-4 flex flex-col justify-center">
                <div className="flex items-center justify-between mb-2">
                  <stat.icon className={`w-4 h-4 ${stat.color}`} />
                  <span className="text-[10px] text-white/30">{stat.label}</span>
                </div>
                <div className="flex items-end gap-2">
                  <span className="text-2xl font-bold font-mono text-white leading-none">{stat.value}</span>
                </div>
                <span className={`text-[10px] mt-1 ${stat.color}`}>{stat.sub}</span>
              </div>
            ))}
          </div>
        </div>

        {/* ML Lifecycle Pipeline - DYNAMIC */}
        <DynamicPipeline />

        {/* Deployed Models & Data Pipeline Health */}
        <div className="grid grid-cols-2 gap-6">
          <div className="border border-white/10 bg-[#0a0a0a] rounded-xl p-5">
            <div className="flex justify-between items-center mb-5">
              <h2 className="text-xs font-bold text-white/60 tracking-widest uppercase">Deployed Models</h2>
              <button className="text-[10px] text-white/40">View All</button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-white/10">
                    <th className="pb-2 text-[10px] text-white/30 font-medium">MODEL NAME</th>
                    <th className="pb-2 text-[10px] text-white/30 font-medium">VER</th>
                    <th className="pb-2 text-[10px] text-white/30 font-medium">STATUS</th>
                    <th className="pb-2 text-[10px] text-white/30 font-medium">ACC</th>
                    <th className="pb-2 text-[10px] text-white/30 font-medium">LATENCY</th>
                  </tr>
                </thead>
                <tbody className="text-xs font-mono">
                  {DEPLOYED_MODELS.map((m, i) => (
                    <tr key={i} className="border-b border-white/5 last:border-0 hover:bg-white/5 transition-colors">
                      <td className="py-3 text-white/70">{m.name}</td>
                      <td className="py-3 text-white/40">{m.version}</td>
                      <td className="py-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] ${m.status === 'Healthy' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-amber-500/10 text-amber-500'}`}>{m.status}</span>
                      </td>
                      <td className="py-3 text-white/70">{m.acc}</td>
                      <td className="py-3 text-white/40">{m.lat}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="border border-white/10 bg-[#0a0a0a] rounded-xl p-5">
            <div className="flex justify-between items-center mb-5">
              <h2 className="text-xs font-bold text-white/60 tracking-widest uppercase">Data Pipeline Health</h2>
              <button className="text-[10px] text-white/40">View All</button>
            </div>
            <div className="space-y-4">
              {[
                { name: "Morningstar Ingestion", type: "Batch", rate: "4.2 GB/s", status: "Healthy" },
                { name: "HF Space Inference", type: "Streaming", rate: "250 MB/s", status: "Healthy" },
                { name: "TF-IDF Vectorization", type: "Streaming", rate: "1.8 GB/s", status: "Warning" },
              ].map((pipe, i) => (
                <div key={i} className="flex items-center justify-between p-3 rounded-lg border border-white/5 bg-black">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded bg-white/5 flex items-center justify-center">
                      <Database className="w-4 h-4 text-white/40" />
                    </div>
                    <div>
                      <div className="text-xs text-white/80">{pipe.name}</div>
                      <div className="text-[10px] font-mono text-white/40 mt-0.5">{pipe.type}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs font-mono text-white/80">{pipe.rate}</div>
                    <div className={`text-[10px] mt-0.5 flex items-center justify-end gap-1 ${pipe.status === 'Healthy' ? 'text-emerald-500' : 'text-amber-500'}`}>
                      <span className="w-1.5 h-1.5 rounded-full bg-current" /> {pipe.status}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* RIGHT COLUMN (4 cols) */}
      <div className="col-span-12 xl:col-span-4 flex flex-col gap-6">
        
        <div className="border border-white/10 bg-[#0a0a0a] rounded-xl p-5">
          <div className="flex justify-between items-center mb-5">
            <h2 className="text-xs font-bold text-white/60 tracking-widest uppercase">Model Performance</h2>
            <button className="text-[10px] border border-white/10 px-2 py-1 rounded text-white/40">Last 7 Days</button>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-black border border-white/5 p-3 rounded-lg">
              <div className="flex justify-between items-start mb-1">
                <span className="text-[10px] text-white/30 uppercase">Macro F1 (Avg)</span>
                <span className="text-[10px] text-emerald-500">+13.0%</span>
              </div>
              <div className="text-lg font-bold font-mono text-white">75.0%</div>
              <MiniLineChart color="#ef4444" data={[40, 59.65, 67.11, 68.42, 70.29, 73.95, 75.0]} />
            </div>
            <div className="bg-black border border-white/5 p-3 rounded-lg">
              <div className="flex justify-between items-start mb-1">
                <span className="text-[10px] text-white/30 uppercase">Precision (Avg)</span>
                <span className="text-[10px] text-emerald-500">+1.8%</span>
              </div>
              <div className="text-lg font-bold font-mono text-white">91.4%</div>
              <MiniLineChart color="#3b82f6" data={[72, 78, 82, 86, 88.5, 90.9, 91.4]} />
            </div>
          </div>
        </div>

        <div className="border border-white/10 bg-[#0a0a0a] rounded-xl p-5">
          <div className="flex justify-between items-center mb-5">
            <h2 className="text-xs font-bold text-white/60 tracking-widest uppercase">Resource Utilization</h2>
          </div>
          <div className="grid grid-cols-4 gap-2">
            <RadialGauge label="CPU" value={22} color="#3b82f6" />
            <RadialGauge label="GPU" value={98} color="#ef4444" />
            <RadialGauge label="MEM" value={64} color="#10b981" />
            <RadialGauge label="DISK" value={41} color="#f59e0b" />
          </div>
          <div className="mt-4 text-center text-[10px] text-white/30">
            GPU 0: Colab A100 (training) · HF Space CPU (inference) - VRAM 98% during training runs
          </div>
        </div>

        <div className="border border-white/10 bg-[#0a0a0a] rounded-xl p-5">
          <div className="flex justify-between items-center mb-5">
            <h2 className="text-xs font-bold text-white/60 tracking-widest uppercase">Experiments</h2>
          </div>
          <div className="space-y-3">
            {EXPERIMENTS.map((exp, i) => (
              <div key={i} className="flex items-center justify-between border-b border-white/5 pb-3 last:border-0 last:pb-0">
                <div>
                  <div className="text-[10px] font-mono text-white/40 mb-0.5">{exp.id}</div>
                  <div className="text-xs text-white/80">{exp.name}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-bold font-mono text-white">{exp.score}</div>
                  <div className="text-[10px] text-white/30">{exp.time}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </motion.div>
  );
}

// --- Main Layout ---

export default function MLOpsDashboard() {
  const [activeTab, setActiveTab] = useState("Overview");

  return (
    <div className="min-h-screen bg-[#020202] text-white flex overflow-hidden font-sans">
      {/* SIDEBAR */}
      <aside className="w-64 border-r border-white/10 bg-black flex flex-col flex-shrink-0 z-20">
        <div className="h-16 flex items-center px-6 border-b border-white/10">
          <Link href="/" className="flex items-center gap-2 group">
            <div className="w-8 h-8 bg-red-600 rounded flex items-center justify-center group-hover:bg-red-500 transition-colors shadow-[0_0_15px_rgba(220,38,38,0.5)]">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="text-sm font-black tracking-widest text-white leading-none">TAVSS</div>
              <div className="text-[10px] text-white/50 tracking-widest uppercase mt-1">ML Operations</div>
            </div>
          </Link>
        </div>

        <nav className="flex-1 py-6 px-3 space-y-1 overflow-y-auto">
          {SIDEBAR_ITEMS.map((item, i) => (
            <button key={i} onClick={() => setActiveTab(item.label)} className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
              activeTab === item.label 
                ? "bg-red-500/10 text-red-500 font-semibold border border-red-500/20" 
                : "text-white/40 hover:text-white hover:bg-white/5"
            }`}>
              <item.icon className={`w-4 h-4 ${activeTab === item.label ? "text-red-500" : "text-white/40"}`} />
              {item.label}
            </button>
          ))}
        </nav>

        <div className="p-4 border-t border-white/10">
          <div className="flex items-center justify-between px-2">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center">
                <User className="w-4 h-4 text-red-400" />
              </div>
              <div>
                <div className="text-xs font-bold text-white">admin</div>
                <div className="text-[10px] text-white/40">TAVSS Access</div>
              </div>
            </div>
            <button
              title="Sign out"
              onClick={async () => {
                await fetch("/api/auth", { method: "DELETE" });
                window.location.href = "/";
              }}
              className="text-white/20 hover:text-red-400 transition-colors p-1 rounded"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* MAIN CONTENT */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden relative">
        {/* TOPBAR */}
        <header className="h-16 border-b border-white/10 bg-[#060606] flex items-center justify-between px-6 flex-shrink-0 z-10">
          <div>
            <h1 className="text-sm font-bold text-white tracking-widest uppercase">AI/ML Control Center</h1>
            <div className="text-xs text-white/40 mt-0.5">Real-time monitoring, analytics & orchestration</div>
          </div>
          
          <div className="flex items-center gap-8">
            <div className="flex flex-col">
              <span className="text-[10px] text-white/40 uppercase tracking-widest">System Status</span>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_#10b981]" />
                <span className="text-xs font-bold text-emerald-500">OPERATIONAL</span>
              </div>
            </div>
            
            <div className="w-px h-8 bg-white/10" />
            
            <div className="flex flex-col">
              <span className="text-[10px] text-white/40 uppercase tracking-widest">Global Health</span>
              <div className="flex items-baseline gap-2 mt-0.5">
                <span className="text-lg font-bold font-mono leading-none">94.2</span>
                <span className="text-xs text-white/40">/100</span>
                <span className="text-[10px] text-emerald-500">+1.2%</span>
              </div>
            </div>

            <div className="w-px h-8 bg-white/10" />

            <div className="flex flex-col">
              <span className="text-[10px] text-white/40 uppercase tracking-widest">Active Models</span>
              <div className="flex items-baseline gap-2 mt-0.5">
                <span className="text-lg font-bold font-mono leading-none">3</span>
                <span className="text-[10px] text-emerald-500">+0</span>
              </div>
            </div>

            <div className="flex items-center gap-4 ml-6">
              <button className="text-white/40 hover:text-white"><Search className="w-4 h-4" /></button>
              <button onClick={() => setActiveTab("Alerts")} className="text-white/40 hover:text-white relative">
                <Bell className="w-4 h-4" />
                <span className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full" />
              </button>
              <button onClick={() => setActiveTab("Settings")} className="text-white/40 hover:text-white">
                <Settings className="w-4 h-4" />
              </button>
            </div>
          </div>
        </header>

        {/* DYNAMIC TAB RENDERING */}
        <div className="flex-1 overflow-y-auto p-6 bg-[#020202]">
          <AnimatePresence mode="wait">
            {activeTab === "Overview" && <OverviewTab key="Overview" />}
            {activeTab === "Models" && <ModelsTab key="Models" />}
            {activeTab === "Training" && <TrainingTab key="Training" />}
            {activeTab === "Data Pipelines" && <DataPipelinesTab key="DataPipelines" />}
            {activeTab === "Deployment (SVM)" && <DeploymentTab key="Deployment" />}
            {activeTab === "LLM Testing" && <LLMTestingTab key="LLMTesting" />}
            {activeTab === "Knowledge Graph" && <GraphTab key="Graph" />}
            {activeTab === "Code Showcase" && <CodeTab key="Code" />}
            {activeTab === "Monitoring" && <MonitoringTab key="Monitoring" />}
            {activeTab === "Reports" && <ReportsTab key="Reports" />}
            {activeTab === "Alerts" && <AlertsTab key="Alerts" />}
            {activeTab === "Documentation" && <DocumentationTab key="Documentation" />}
            {activeTab === "Governance" && <GovernanceTab key="Governance" />}
            {activeTab === "Settings" && <SettingsTab key="Settings" />}
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}
