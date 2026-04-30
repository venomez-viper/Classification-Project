import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const HF_SPACE_URL = process.env.HF_SPACE_URL ?? "http://localhost:7860";
const HF_API_SECRET = process.env.HF_API_SECRET ?? "";

export async function POST(req: NextRequest) {
  const body = await req.json();

  let upstream: Response;
  try {
    upstream = await fetch(`${HF_SPACE_URL}/api/predict_llm`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(HF_API_SECRET ? { "X-API-Secret": HF_API_SECRET } : {}),
      },
      body: JSON.stringify(body),
    });
  } catch {
    return NextResponse.json(
      { error: "Cannot reach DeBERTa server. HF Space may be cold-starting." },
      { status: 502 }
    );
  }

  const text = await upstream.text();
  if (!text) {
    return NextResponse.json({ error: "HF Space returned empty response. It may still be loading." }, { status: 503 });
  }
  try {
    const data = JSON.parse(text);
    return NextResponse.json(data, { status: upstream.status });
  } catch {
    return NextResponse.json({ error: `HF Space returned invalid JSON: ${text.slice(0, 200)}` }, { status: 502 });
  }
}
