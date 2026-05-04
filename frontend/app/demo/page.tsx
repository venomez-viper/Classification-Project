import Navigation from "@/components/Navigation";
import LiveDemo from "@/components/LiveDemo";
import HowItWorks from "@/components/HowItWorks";

export default function DemoPage() {
  return (
    <main className="min-h-screen bg-black pt-20">
      <Navigation />
      <LiveDemo />
      <div className="border-t border-white/6">
        <HowItWorks compact />
      </div>
    </main>
  );
}
