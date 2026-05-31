import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const GECS_API_URL =
  process.env.GECS_API_URL ??
  process.env.NEXT_PUBLIC_GECS_API_URL ??
  process.env.LEGENDARY_API_URL ??
  process.env.NEXT_PUBLIC_LEGENDARY_API_URL ??
  process.env.LLM_API_URL ??
  process.env.NEXT_PUBLIC_LLM_API_URL ??
  "http://localhost:5003";

type JsonObject = Record<string, unknown>;

function asObject(value: unknown): JsonObject {
  return typeof value === "object" && value !== null ? (value as JsonObject) : {};
}

function asNumber(value: unknown, fallback = 0): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function legacyLlmShape(data: JsonObject): JsonObject {
  const task1 = asObject(data.task1);
  const task2 = asObject(data.task2);
  const alternatives = Array.isArray(data.alternatives) ? data.alternatives : data.alternatives_t1;
  return {
    ...data,
    engine: data.engine ?? data.model_version ?? "GECS-Sage",
    mstar_code: data.mstar_code ?? task1.code,
    mstar_label: data.mstar_label ?? task1.industry_name ?? task1.label,
    confidence: data.confidence ?? data.confidence_t1 ?? task1.confidence_percent ?? asNumber(task1.confidence) * 100,
    confidence_t1: data.confidence_t1 ?? task1.confidence_percent ?? asNumber(task1.confidence) * 100,
    alternatives: data.alternatives ?? alternatives ?? [],
    alternatives_t1: data.alternatives_t1 ?? alternatives ?? [],
    task2_ready: Boolean(task2.code ?? data.sub_code),
    sub_code: data.sub_code ?? task2.code,
    sub_label: data.sub_label ?? task2.subindustry_name ?? task2.label,
    sub_confidence: data.sub_confidence ?? data.confidence_t2 ?? task2.confidence_percent ?? asNumber(task2.confidence) * 100,
    sub_alternatives: data.sub_alternatives ?? task2.alternatives ?? data.alternatives_t2 ?? [],
  };
}

export async function POST(req: NextRequest) {
  const body = await req.json();

  let upstream: Response;
  try {
    upstream = await fetch(`${GECS_API_URL}/api/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...body,
        company_text: body.company_text ?? body.text,
        segment_text: body.segment_text ?? body.text,
        include_reasoning: body.include_reasoning ?? true,
      }),
    });
  } catch {
    return NextResponse.json(
      { error: "Cannot reach GECS-Sage. Make sure server_legendary.py is running on port 5003." },
      { status: 502 }
    );
  }

  const text = await upstream.text();
  if (!text) {
    return NextResponse.json({ error: "GECS-Sage returned an empty response." }, { status: 503 });
  }

  try {
    const data = JSON.parse(text);
    return NextResponse.json(legacyLlmShape(asObject(data)), { status: upstream.status });
  } catch {
    return NextResponse.json(
      { error: `GECS-Sage error (${upstream.status}): ${text.slice(0, 300)}` },
      { status: 502 }
    );
  }
}
