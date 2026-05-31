import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const GECS_API_URL =
  process.env.GECS_API_URL ??
  process.env.NEXT_PUBLIC_GECS_API_URL ??
  process.env.LEGENDARY_API_URL ??
  process.env.NEXT_PUBLIC_LEGENDARY_API_URL ??
  process.env.SVM_API_URL ??
  process.env.NEXT_PUBLIC_SVM_API_URL ??
  "http://localhost:5003";

export async function POST(req: NextRequest) {
  const body = await req.json();

  let upstream: Response;
  try {
    upstream = await fetch(`${GECS_API_URL}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    return NextResponse.json(
      { error: "Cannot reach the GECS-Sage feedback endpoint." },
      { status: 502 }
    );
  }

  const text = await upstream.text();
  if (!text) {
    return NextResponse.json({ error: "GECS-Sage feedback returned an empty response." }, { status: 503 });
  }
  try {
    return NextResponse.json(JSON.parse(text), { status: upstream.status });
  } catch {
    return NextResponse.json({ error: `GECS-Sage feedback error (${upstream.status}): ${text.slice(0, 300)}` }, { status: 502 });
  }
}
