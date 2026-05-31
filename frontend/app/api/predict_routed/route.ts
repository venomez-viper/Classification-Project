import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export const maxDuration = 60;

const GECS_API_URL =
  process.env.GECS_API_URL ??
  process.env.NEXT_PUBLIC_GECS_API_URL ??
  process.env.LEGENDARY_API_URL ??
  process.env.NEXT_PUBLIC_LEGENDARY_API_URL ??
  "http://localhost:5003";

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
      { error: "Cannot reach the GECS-Sage routing server. Check port 5003 or GECS_API_URL." },
      { status: 502 }
    );
  }

  const text = await upstream.text();
  if (!text) {
    return NextResponse.json({ error: "GECS-Sage server returned empty response." }, { status: 503 });
  }

  try {
    const data = JSON.parse(text);
    return NextResponse.json(data, { status: upstream.status });
  } catch {
    return NextResponse.json(
      { error: `GECS-Sage server error (${upstream.status}): ${text.slice(0, 300)}` },
      { status: 502 }
    );
  }
}
