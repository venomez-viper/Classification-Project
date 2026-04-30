import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const configuredUrls = [
  process.env.HF_SPACE_URL,
  process.env.NEXT_PUBLIC_LLM_API_URL,
  "http://localhost:7860",
  "http://localhost:5001",
].filter(Boolean) as string[];

const LLM_BASE_URLS = [...new Set(configuredUrls.map((url) => url.replace(/\/$/, "")))];
const HF_API_SECRET = process.env.HF_API_SECRET ?? "";

async function requestUpstream(body: unknown) {
  const headers = {
    "Content-Type": "application/json",
    ...(HF_API_SECRET ? { "X-API-Secret": HF_API_SECRET } : {}),
  };

  let lastResponse: Response | null = null;

  for (const baseUrl of LLM_BASE_URLS) {
    for (const route of ["/run/predict_llm", "/api/predict_llm"]) {
      try {
        const response = await fetch(`${baseUrl}${route}`, {
          method: "POST",
          headers,
          body: JSON.stringify(body),
        });

        if (response.status !== 404) {
          return response;
        }

        lastResponse = response;
      } catch {
        continue;
      }
    }
  }

  return lastResponse;
}

export async function POST(req: NextRequest) {
  const body = await req.json();

  const upstream = await requestUpstream(body);
  if (!upstream) {
    return NextResponse.json(
      { error: "Cannot reach DeBERTa server. Check HF Space URL, local LLM URL, or cold-start status." },
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
