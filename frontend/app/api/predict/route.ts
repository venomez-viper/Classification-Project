import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const RAILWAY_URL =
  process.env.SVM_API_URL ??
  process.env.NEXT_PUBLIC_SVM_API_URL ??
  "http://localhost:5000";

export async function POST(req: NextRequest) {
  const body = await req.json();

  let upstream: Response;
  try {
    upstream = await fetch(`${RAILWAY_URL}/api/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    return NextResponse.json(
      { error: "Cannot reach classification server. Railway may be offline." },
      { status: 502 }
    );
  }

  const data = await upstream.json();
  return NextResponse.json(data, { status: upstream.status });
}
