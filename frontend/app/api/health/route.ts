import { NextResponse } from "next/server";

const RAILWAY_URL = process.env.SVM_API_URL ?? process.env.NEXT_PUBLIC_SVM_API_URL ?? "";
const HF_SPACE_URL = process.env.HF_SPACE_URL ?? "";

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
  const [railway, hf] = await Promise.all([
    RAILWAY_URL ? ping(`${RAILWAY_URL}/`) : Promise.resolve({ ok: false, latency: 0 }),
    HF_SPACE_URL ? ping(`${HF_SPACE_URL}/`) : Promise.resolve({ ok: false, latency: 0 }),
  ]);

  return NextResponse.json({
    timestamp: new Date().toISOString(),
    services: {
      vercel:  { ok: true,       latency: 0,              label: "Next.js / Vercel" },
      railway: { ok: railway.ok, latency: railway.latency, label: "Flask SVM / Railway" },
      hf:      { ok: hf.ok,      latency: hf.latency,      label: "DeBERTa / HF Space" },
    },
  });
}
