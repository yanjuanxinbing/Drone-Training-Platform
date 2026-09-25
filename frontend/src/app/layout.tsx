import type { Metadata } from "next";
import "./globals.css";
import { Header } from "@/components/chrome/Header";
import { Footer } from "@/components/chrome/Footer";
import { SmoothScroll } from "@/components/chrome/SmoothScroll";

export const metadata: Metadata = {
  title: "Drone Training Platform — Multi-Scenario Pilot Training",
  description:
    "A Swiss-grid, Bauhaus-minimal training ground for civil and commercial drone pilots. Six canonical scenarios with per-user progress tracking and an optional AirSim live-stream bridge.",
  metadataBase: new URL("http://localhost:3000"),
  openGraph: {
    title: "Drone Training Platform",
    description: "Multi-scenario pilot training. Engineered with restraint.",
    type: "website",
  },
};

export const viewport = {
  themeColor: "#FFFFFF",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <SmoothScroll />
        <Header />
        <main>{children}</main>
        <Footer />
      </body>
    </html>
  );
}