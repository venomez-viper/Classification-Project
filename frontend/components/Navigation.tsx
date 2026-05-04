"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Menu, X } from "lucide-react";
import { TextScramble } from "@/components/ui/text-scramble";

const NAV = [
  { label: "Home",      href: "/" },
  { label: "Journey",   href: "/journey" },
  { label: "Team",      href: "/team" },
];

function NavLink({ label, href, active }: { label: string; href: string; active: boolean }) {
  const [trigger, setTrigger] = useState(false);

  return (
    <Link
      href={href}
      className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
        active
          ? "bg-red-600/20 text-red-400 border border-red-600/30"
          : "text-white/50 hover:text-white hover:bg-white/8"
      }`}
      onMouseEnter={() => setTrigger(true)}
    >
      <TextScramble
        as="span"
        speed={0.02}
        duration={0.5}
        trigger={trigger}
        onScrambleComplete={() => setTrigger(false)}
        className="font-mono"
      >
        {label}
      </TextScramble>
    </Link>
  );
}

export default function Navigation() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-black/70 backdrop-blur-xl border-b border-white/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-8 h-20 flex items-center justify-between">
        <Link href="/" className="flex items-baseline gap-1.5 hover:opacity-80 transition-opacity">
          <TextScramble
            as="span"
            speed={0.03}
            duration={0.8}
            characterSet="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            className="text-xl font-black tracking-widest text-white"
            style={{ fontFamily: "var(--font-geist-sans), 'Inter', sans-serif", letterSpacing: "0.18em" }}
          >
            TAVSS
          </TextScramble>
          <span className="text-[10px] font-mono text-red-500/70 tracking-widest">v1.0</span>
        </Link>

        <div className="hidden md:flex items-center gap-2">
          {NAV.map((item) => (
            <NavLink key={item.href} label={item.label} href={item.href} active={pathname === item.href} />
          ))}
        </div>

        <div className="hidden md:block">
          <Link
            href="/login"
            className="text-sm px-5 py-2.5 rounded-lg bg-red-600 hover:bg-red-500 text-white font-semibold transition-all hover:shadow-[0_0_20px_rgba(220,38,38,0.4)]"
          >
            Login to App {"->"}
          </Link>
        </div>

        <button
          type="button"
          onClick={() => setMobileOpen((open) => !open)}
          className="md:hidden inline-flex items-center justify-center w-11 h-11 rounded-xl border border-white/10 bg-white/5 text-white/80 hover:text-white hover:bg-white/10 transition-colors"
          aria-label={mobileOpen ? "Close navigation menu" : "Open navigation menu"}
          aria-expanded={mobileOpen}
        >
          {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {mobileOpen && (
        <div className="md:hidden border-t border-white/8 bg-black/95 backdrop-blur-2xl">
          <div className="px-4 py-4 flex flex-col gap-2">
            {NAV.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileOpen(false)}
                className={`rounded-xl px-4 py-3 text-sm font-medium transition-all ${
                  pathname === item.href
                    ? "bg-red-600/20 text-red-400 border border-red-600/30"
                    : "text-white/70 hover:text-white hover:bg-white/8 border border-transparent"
                }`}
              >
                {item.label}
              </Link>
            ))}

            <Link
              href="/login"
              onClick={() => setMobileOpen(false)}
              className="mt-2 inline-flex items-center justify-center rounded-xl bg-red-600 px-4 py-3 text-sm font-semibold text-white hover:bg-red-500 transition-colors"
            >
              Login to App {"->"}
            </Link>
          </div>
        </div>
      )}
    </nav>
  );
}
