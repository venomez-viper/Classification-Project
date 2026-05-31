import { NextResponse } from "next/server";

const GECS_API_URL =
  process.env.GECS_API_URL ??
  process.env.NEXT_PUBLIC_GECS_API_URL ??
  process.env.LEGENDARY_API_URL ??
  process.env.NEXT_PUBLIC_LEGENDARY_API_URL ??
  process.env.SVM_API_URL ??
  process.env.NEXT_PUBLIC_SVM_API_URL ??
  "http://localhost:5003";
const HF_SPACE_URL = process.env.HF_SPACE_URL ?? process.env.NEXT_PUBLIC_LLM_API_URL ?? "";

async function ping(url: string, timeoutMs = 5000): Promise<{ ok: boolean; latency: number }> {
  const start = Date.now();
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    const res = await fetch(url, { method: "GET", signal: controller.signal });
    clearTimeout(timer);
    return { ok: res.ok || res.status < 500, latency: Date.now() - start };
  } catch {
    return { ok: false, latency: Date.now() - start };
  }
}

export async function GET() {
  const [gecs, hf] = await Promise.all([
    GECS_API_URL ? ping(`${GECS_API_URL}/health`) : Promise.resolve({ ok: false, latency: 0 }),
    HF_SPACE_URL ? ping(`${HF_SPACE_URL}/`) : Promise.resolve({ ok: false, latency: 0 }),
  ]);

  return NextResponse.json({
    timestamp: new Date().toISOString(),
    services: {
      vercel: { ok: true, latency: 0, label: "Next.js app" },
      railway: { ok: gecs.ok, latency: gecs.latency, label: "GECS-Sage Flask API" },
      hf: { ok: hf.ok, latency: hf.latency, label: "HF Space demo" },
    },
  });
}
