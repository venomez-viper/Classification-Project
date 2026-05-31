import dynamic from "next/dynamic";
import Navigation from "@/components/Navigation";

const Journey = dynamic(() => import("@/components/Journey"), { ssr: false });

export default function JourneyPage() {
  return (
    <main className="min-h-screen bg-black pt-20">
      <Navigation />
      <Journey />
    </main>
  );
}
