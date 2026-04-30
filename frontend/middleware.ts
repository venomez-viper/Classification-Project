import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_PATHS = ["/login", "/api/auth", "/_next", "/favicon.ico", "/public"];
const PUBLIC_PAGES = [
  "/",
  "/about",
  "/journey",
  "/team",
  "/demo",
  "/features",
  "/breezeml",
  "/model",
  "/graph",
];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Marketing and showcase pages are public
  if (PUBLIC_PAGES.includes(pathname)) {
    return NextResponse.next();
  }

  // Allow public paths through
  if (PUBLIC_PATHS.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  // Allow API routes except auth to pass (they do their own checks)
  if (pathname.startsWith("/api/")) {
    return NextResponse.next();
  }

  const auth = request.cookies.get("tavss_auth");
  if (auth?.value === "granted") {
    return NextResponse.next();
  }

  const loginUrl = request.nextUrl.clone();
  loginUrl.pathname = "/login";
  loginUrl.searchParams.set("from", pathname);
  return NextResponse.redirect(loginUrl);
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
