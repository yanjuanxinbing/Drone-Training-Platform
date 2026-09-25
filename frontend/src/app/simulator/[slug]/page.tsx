import { SCENARIOS, getScenario } from "@/lib/scenarios";
import { Simulator } from "@/components/three/Simulator";

type Params = { params: Promise<{ slug: string }> };

export async function generateStaticParams() {
  return SCENARIOS.map((s) => ({ slug: s.slug }));
}

export async function generateMetadata({ params }: Params) {
  const { slug } = await params;
  const s = getScenario(slug);
  if (!s) return {};
  return { title: `Simulator · ${s.name}` };
}

export default async function SimulatorPage({ params }: Params) {
  const { slug } = await params;
  const scenario = getScenario(slug);
  if (!scenario) return <div>Scenario not found.</div>;
  return <Simulator scenario={scenario} />;
}