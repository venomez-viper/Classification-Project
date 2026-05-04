import Navigation from "@/components/Navigation";
import Dashboard from "@/components/Dashboard";
import HowItWorks from "@/components/HowItWorks";

export default function DashboardPage() {
  return (
    <main className="min-h-screen bg-black">
      <Navigation />
      <Dashboard />
      <div className="border-t border-white/6">
        <HowItWorks compact />
      </div>
    </main>
  );
}
