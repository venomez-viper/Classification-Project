import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const USERNAME = process.env.ACCESS_USER     ?? "admin";
const PASSWORD = process.env.ACCESS_PASSWORD ?? "TAVSS2026";

export async function POST(req: NextRequest) {
  const { username, password } = await req.json();

  if (username === USERNAME && password === PASSWORD) {
    const res = NextResponse.json({ ok: true });
    res.cookies.set("tavss_auth", "granted", {
      httpOnly: true,
      sameSite: "lax",
      path: "/",
      maxAge: 60 * 60 * 8, // 8 hours
    });
    return res;
  }

  return NextResponse.json({ ok: false, error: "Invalid credentials" }, { status: 401 });
}

export async function DELETE() {
  const res = NextResponse.json({ ok: true });
  res.cookies.set("tavss_auth", "", { path: "/", maxAge: 0 });
  return res;
}
