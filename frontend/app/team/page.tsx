"use client";
import dynamic from "next/dynamic";
import Navigation from "@/components/Navigation";

const Team = dynamic(() => import("@/components/Team"), { ssr: false });

export default function TeamPage() {
  return (
    <main className="min-h-screen bg-black pt-20">
      <Navigation />
      <Team />
    </main>
  );
}
