import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // 1. Allow public paths (login page and auth API)
  if (pathname.startsWith("/login") || pathname.startsWith("/api/auth")) {
    return NextResponse.next();
  }

  // 2. Allow static assets and internal next calls
  if (
    pathname.startsWith("/_next") ||
    pathname.includes("favicon.ico") ||
    pathname.includes(".png") ||
    pathname.includes(".svg")
  ) {
    return NextResponse.next();
  }

  // 3. Check for auth cookie
  const auth = request.cookies.get("tavss_auth");
  
  if (!auth || auth.value !== "granted") {
    // Redirect to login, but keep the original path in 'from'
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.searchParams.set("from", pathname);
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

// Next.js 16 might complain about middleware.ts, but let's try the stable way first.
// If the build fails again because of the 'middleware' name, we will rename the EXPORT to 'proxy'.
