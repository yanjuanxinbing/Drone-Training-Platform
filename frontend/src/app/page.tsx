import { HeroCarousel } from "@/components/hero/HeroCarousel";
import { ScenarioGrid } from "@/components/sections/ScenarioGrid";
import { Manifesto } from "@/components/sections/Manifesto";
import { TelemetryStrip } from "@/components/sections/TelemetryStrip";

export default function Home() {
  return (
    <>
      <HeroCarousel />
      <ScenarioGrid />
      <Manifesto />
      <TelemetryStrip />
    </>
  );
}