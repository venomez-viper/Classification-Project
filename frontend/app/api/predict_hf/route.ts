import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export const maxDuration = 60;

const HF_SPACE_URL =
  process.env.HF_SPACE_URL ??
  process.env.GECS_API_URL ??
  process.env.NEXT_PUBLIC_GECS_API_URL ??
  "https://akash-ag-gecs-classifier-space.hf.space";

export async function POST(req: NextRequest) {
  const body = await req.json();
  const text = String(body.text ?? body.company_text ?? "").trim();

  if (!text) {
    return NextResponse.json({ error: "text is required" }, { status: 400 });
  }

  let upstream: Response;
  try {
    upstream = await fetch(`${HF_SPACE_URL}/api/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, company_text: text }),
    });
  } catch {
    return NextResponse.json(
      { error: "Cannot reach the Hugging Face Space. It may be waking up — wait 30 seconds and try again." },
      { status: 502 }
    );
  }

  const raw = await upstream.text();
  if (!raw) {
    return NextResponse.json({ error: "Empty response from HF Space." }, { status: 503 });
  }

  try {
    const data = JSON.parse(raw);
    return NextResponse.json(data, { status: upstream.status });
  } catch {
    return NextResponse.json(
      { error: `HF Space error (${upstream.status}): ${raw.slice(0, 300)}` },
      { status: 502 }
    );
  }
}
