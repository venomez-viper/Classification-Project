import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export const maxDuration = 300;

const GECS_API_URL =
  process.env.GECS_API_URL ??
  process.env.NEXT_PUBLIC_GECS_API_URL ??
  process.env.LEGENDARY_API_URL ??
  process.env.NEXT_PUBLIC_LEGENDARY_API_URL ??
  process.env.SVM_API_URL ??
  process.env.NEXT_PUBLIC_SVM_API_URL ??
  "http://localhost:5003";

type JsonObject = Record<string, unknown>;

function asObject(value: unknown): JsonObject {
  return typeof value === "object" && value !== null ? (value as JsonObject) : {};
}

function asNumber(value: unknown, fallback = 0): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function flattenResponse(data: JsonObject): JsonObject {
  const task1 = asObject(data.task1);
  const task2 = asObject(data.task2);
  const alternatives = Array.isArray(data.alternatives) ? data.alternatives : data.alternatives_t1;
  const task2Alternatives = Array.isArray(task2.alternatives) ? task2.alternatives : data.alternatives_t2;

  return {
    ...data,
    mstar_code: data.mstar_code ?? task1.code,
    mstar_label: data.mstar_label ?? task1.industry_name ?? task1.label,
    confidence_t1: data.confidence_t1 ?? task1.confidence_percent ?? asNumber(task1.confidence) * 100,
    alternatives_t1: data.alternatives_t1 ?? alternatives ?? [],
    features_t1: data.features_t1 ?? [],
    sub_code: data.sub_code ?? task2.code,
    sub_label: data.sub_label ?? task2.subindustry_name ?? task2.label,
    confidence_t2: data.confidence_t2 ?? task2.confidence_percent ?? asNumber(task2.confidence) * 100,
    alternatives_t2: data.alternatives_t2 ?? task2Alternatives ?? [],
    features_t2: data.features_t2 ?? [],
  };
}

export async function POST(req: NextRequest) {
  const body = await req.json();

  let upstream: Response;
  const payload = {
    ...body,
    company_text: body.company_text ?? body.text,
    segment_text: body.segment_text ?? body.text,
    include_reasoning: body.include_reasoning ?? true,
  };

  try {
    upstream = await fetch(`${GECS_API_URL}/api/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch {
    return NextResponse.json(
      { error: "Cannot reach the GECS-Sage Flask classifier." },
      { status: 502 }
    );
  }

  const text = await upstream.text();
  if (!text) {
    return NextResponse.json({ error: "GECS-Sage returned an empty response." }, { status: 503 });
  }
  try {
    const data = JSON.parse(text);
    return NextResponse.json(flattenResponse(asObject(data)), { status: upstream.status });
  } catch {
    return NextResponse.json({ error: `GECS-Sage error (${upstream.status}): ${text.slice(0, 300)}` }, { status: 502 });
  }
}
