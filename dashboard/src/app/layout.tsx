import "@fontsource/ibm-plex-mono/400.css";
import "@fontsource/ibm-plex-sans/400.css";
import "@fontsource/ibm-plex-sans/500.css";
import "@fontsource/ibm-plex-sans/600.css";
import "@fontsource/fraunces/500.css";
import "@fontsource/fraunces/600.css";
import type { Metadata } from "next";
import type { ReactNode } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { BundleProvider } from "@/lib/bundle";

import "./globals.css";

export const metadata: Metadata = {
  title: { default: "Immune Atlas", template: "%s | Immune Atlas" },
  description:
    "Immune cell populations and treatment-response analysis for a clinical trial dataset.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <BundleProvider>
          <AppShell>{children}</AppShell>
        </BundleProvider>
      </body>
    </html>
  );
}
