import Navigation from "@/components/Navigation";
import ModelDevelopment from "@/components/ModelDevelopment";
import Evaluation from "@/components/Evaluation";

export default function ModelPage() {
  return (
    <main className="min-h-screen bg-black pt-20">
      <Navigation />
      <ModelDevelopment />
      <Evaluation />
    </main>
  );
}
