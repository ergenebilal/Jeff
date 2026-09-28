import type { Metadata } from "next";
// ── FONTS ─────────────────────────────────────────────────────────────────
// The setup can swap these for per-brand variety. Keep the CSS variable names
// (--font-sans-app / --font-display-app / --font-mono-app) so globals.css picks
// them up. Pick any pairing from next/font/google.
import { Plus_Jakarta_Sans, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { LanguageProvider } from "@/components/i18n/language-provider";
import appConfig from "@/app.config";
import { DEFAULT_LANG } from "@/lib/i18n/config";

// Pipely pairs Plus Jakarta Sans (UI + display) with JetBrains Mono (deal
// values, labels). The display variable reuses the Jakarta family at heavier
// weights — no serif. Keep the CSS variable names so globals.css picks them up.
const sans = Plus_Jakarta_Sans({
  variable: "--font-sans-app",
  subsets: ["latin"],
  display: "swap",
  weight: ["400", "500", "600", "700", "800"],
});

const display = Plus_Jakarta_Sans({
  variable: "--font-display-app",
  subsets: ["latin"],
  display: "swap",
  weight: ["600", "700", "800"],
});

const mono = JetBrains_Mono({
  variable: "--font-mono-app",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: `${appConfig.name} — ${appConfig.tagline[DEFAULT_LANG]}`,
  description: appConfig.description[DEFAULT_LANG],
  applicationName: appConfig.name,
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang={DEFAULT_LANG}
      className={`${sans.variable} ${display.variable} ${mono.variable} h-full`}
    >
      <body className="min-h-full bg-background text-foreground antialiased font-sans">
        <LanguageProvider>{children}</LanguageProvider>
      </body>
    </html>
  );
}
