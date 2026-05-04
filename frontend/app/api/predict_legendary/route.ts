import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const LEGENDARY_URL =
  process.env.LEGENDARY_API_URL ??
  process.env.NEXT_PUBLIC_LEGENDARY_API_URL ??
  "http://localhost:5003";

export async function POST(req: NextRequest) {
  const body = await req.json();

  let upstream: Response;
  try {
    upstream = await fetch(`${LEGENDARY_URL}/api/predict_legendary`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    return NextResponse.json(
      { error: "Cannot reach the legendary server. Check port 5003 or LEGENDARY_API_URL." },
      { status: 502 }
    );
  }

  const text = await upstream.text();
  if (!text) {
    return NextResponse.json({ error: "Legendary server returned empty response." }, { status: 503 });
  }

  try {
    const data = JSON.parse(text);
    return NextResponse.json(data, { status: upstream.status });
  } catch {
    return NextResponse.json(
      { error: `Legendary server error (${upstream.status}): ${text.slice(0, 300)}` },
      { status: 502 }
    );
  }
}
