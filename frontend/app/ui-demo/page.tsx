"use client";

import {
  AreaChart,
  Area,
  Grid,
  XAxis,
  YAxis,
  ChartTooltip,
} from "@/components/ui/area-chart";
import { Accordion, AccordionContent, AccordionItem } from "@/components/ui/accordion";
import * as AccordionPrimitive from "@radix-ui/react-accordion";
import { BadgeDelta } from "@/components/ui/badge-delta";
import { Button } from "@/components/ui/button";
import Switch from "@/components/ui/switch";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import { Plus, Bolt, ChevronDown, CopyPlus, Files, Layers2, Trash } from "lucide-react";

// Chart Data: Simulating the Capstone Project's Model Performance (F1 Score) over 30 days
const performanceData = Array.from({ length: 30 }, (_, i) => {
  // Start at honest baseline 59.65% and grow to locked 75.0%
  const base = 59.65 + (i * 0.52);
  const noise = Math.sin(i) * 1.5;
  const f1 = Math.min(75.0, Math.max(0, base + noise));
  return {
    date: new Date(2024, 4, i + 1), // May 2024
    f1_score: parseFloat(f1.toFixed(2)),
  };
});

const faqItems = [
  {
    id: "1",
    title: "What is the locked ensemble result?",
    content:
      "A calibrated greedy ensemble of two ModernBERT-large variants reached 75.0% Macro F1 (91.4% top-3 accuracy) on the company-disjoint test set — after 14 model versions and catching a 97.2% leakage in the original 88.90% result.",
  },
  {
    id: "2",
    title: "How is the data visualized?",
    content:
      "We use an interactive PyVis network graph and customized React area charts to track confidence scores, segment mappings, and overall performance trends across the pipeline.",
  },
  {
    id: "3",
    title: "Is the GECS-Sage API production ready?",
    content:
      "Yes, the Flask API (server_legendary.py) handles real-time inference via the /api/predict_legendary endpoint, smoothly proxied by our Next.js frontend.",
  },
];

export default function UIDashboardDemo() {
  return (
    <div className="min-h-screen bg-black text-white p-8 md:p-12 font-geist">
      <div className="max-w-6xl mx-auto space-y-12">
        
        {/* Header Section */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-end border-b border-white/10 pb-6">
          <div>
            <h1 className="text-4xl font-bold tracking-tight text-white">Project Analytics</h1>
            <p className="text-white/60 mt-2">Monitoring the GECS-Sage Capstone classification pipeline.</p>
          </div>
          
          <div className="mt-4 md:mt-0 flex gap-4 items-center">
            <BadgeDelta variant="solidOutline" deltaType="increase" iconStyle="line" value="75.0% F1 locked" />
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline">
                  Manage Model
                  <ChevronDown className="-me-1 ms-2 opacity-60" size={16} strokeWidth={2} />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuGroup>
                  <DropdownMenuItem>
                    <CopyPlus size={16} strokeWidth={2} className="opacity-60" /> Copy Report
                  </DropdownMenuItem>
                  <DropdownMenuItem>
                    <Bolt size={16} strokeWidth={2} className="opacity-60" /> Retrain
                  </DropdownMenuItem>
                </DropdownMenuGroup>
                <DropdownMenuSeparator />
                <DropdownMenuGroup>
                  <DropdownMenuItem>
                    <Files size={16} strokeWidth={2} className="opacity-60" /> Export Logs
                  </DropdownMenuItem>
                  <DropdownMenuItem className="text-red-500 focus:text-red-400 focus:bg-red-950/30">
                    <Trash size={16} strokeWidth={2} /> Terminate Run
                  </DropdownMenuItem>
                </DropdownMenuGroup>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* Chart Section */}
        <section className="bg-black border border-white/10 rounded-3xl p-6 shadow-2xl relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-b from-red-500/5 to-transparent pointer-events-none" />
          <div className="mb-6">
            <h2 className="text-xl font-semibold">Model Performance History</h2>
            <p className="text-sm text-white/50">Macro F1 Score progression over the development lifecycle.</p>
          </div>
          <div className="w-full h-[400px]">
            <AreaChart data={performanceData} margin={{ left: 40, top: 20, right: 20, bottom: 40 }}>
              <Grid horizontal strokeDasharray="4,4" strokeOpacity={0.2} stroke="currentColor" />
              <Area dataKey="f1_score" fillOpacity={0.15} strokeWidth={3} fill="oklch(0.48 0.22 15)" stroke="oklch(0.62 0.22 15)" />
              <YAxis numTicks={5} formatValue={(v) => `${v}%`} />
              <XAxis numTicks={6} />
              <ChartTooltip />
            </AreaChart>
          </div>
        </section>

        {/* Bottom Split Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          
          {/* Accordion FAQ */}
          <section className="bg-zinc-950 border border-white/10 rounded-3xl p-6">
            <h2 className="text-xl font-semibold mb-6">Pipeline Architecture FAQ</h2>
            <Accordion type="single" collapsible className="w-full" defaultValue="1">
              {faqItems.map((item) => (
                <AccordionItem value={item.id} key={item.id} className="py-2 border-white/10">
                  <AccordionPrimitive.Header className="flex">
                    <AccordionPrimitive.Trigger className="flex flex-1 items-center gap-3 py-2 text-left text-[15px] font-semibold leading-6 transition-all text-white hover:text-red-400 [&>svg>path:last-child]:origin-center [&>svg>path:last-child]:transition-all [&>svg>path:last-child]:duration-200 [&>svg]:-order-1 [&[data-state=open]>svg>path:last-child]:rotate-90 [&[data-state=open]>svg>path:last-child]:opacity-0 [&[data-state=open]>svg]:rotate-180">
                      {item.title}
                      <Plus
                        size={16}
                        strokeWidth={2}
                        className="shrink-0 opacity-60 transition-transform duration-200"
                        aria-hidden="true"
                      />
                    </AccordionPrimitive.Trigger>
                  </AccordionPrimitive.Header>
                  <AccordionContent className="pb-2 ps-7 text-white/60">
                    {item.content}
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </section>

          {/* Badges / Micro-stats */}
          <section className="bg-zinc-950 border border-white/10 rounded-3xl p-6 flex flex-col gap-6">
            <div>
              <h2 className="text-xl font-semibold">Live Training Deltas</h2>
              <p className="text-sm text-white/50 mb-6">Recent metric shifts observed in continuous evaluation.</p>
            </div>
            <div className="flex flex-col gap-4">
              <div className="flex justify-between items-center p-4 border border-white/10 rounded-xl bg-black/50">
                <span className="text-sm font-medium">Precision (Task 1)</span>
                <BadgeDelta variant="solid" deltaType="increase" iconStyle="line" value="+4.2%" />
              </div>
              <div className="flex justify-between items-center p-4 border border-white/10 rounded-xl bg-black/50">
                <span className="text-sm font-medium">Recall (Task 2)</span>
                <BadgeDelta variant="solid" deltaType="decrease" iconStyle="line" value="-1.1%" />
              </div>
              <div className="flex justify-between items-center p-4 border border-white/10 rounded-xl bg-black/50">
                <span className="text-sm font-medium">Inference Latency</span>
                <BadgeDelta variant="solid" deltaType="neutral" iconStyle="line" value="~120ms" />
              </div>
            </div>
            
            <div className="mt-2 flex items-center justify-between p-4 border border-white/10 rounded-xl bg-white/5">
              <div>
                <h3 className="text-sm font-medium">Live Metrics Stream</h3>
                <p className="text-xs text-white/50 mt-1">Continuously update charts with real-time inference data.</p>
              </div>
              <Switch checked={true} />
            </div>
          </section>

        </div>
      </div>
    </div>
  );
}
