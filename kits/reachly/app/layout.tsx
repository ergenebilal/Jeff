import type { Metadata } from "next";
// ── FONTS ─────────────────────────────────────────────────────────────────
// Reachly pairs Onest (UI + display) with JetBrains Mono (numbers/metrics).
// The setup can swap these for per-brand variety. Keep the CSS variable names
// (--font-sans-app / --font-display-app / --font-mono-app) so globals.css picks
// them up. Pick any pairing from next/font/google.
import { Onest, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";
import { LanguageProvider } from "@/components/i18n/language-provider";
import appConfig from "@/app.config";
import { DEFAULT_LANG } from "@/lib/i18n/config";

const sans = Onest({
  variable: "--font-sans-app",
  subsets: ["latin"],
  display: "swap",
  weight: ["400", "500", "600", "700", "800"],
});

// Onest also drives the display headings — clean and geometric, not editorial.
const display = Onest({
  variable: "--font-display-app",
  subsets: ["latin"],
  display: "swap",
  weight: ["500", "600", "700", "800"],
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
      suppressHydrationWarning
      className={`${sans.variable} ${display.variable} ${mono.variable} h-full`}
    >
      <body className="min-h-full bg-background text-foreground antialiased font-sans">
        <ThemeProvider attribute="class" defaultTheme="light" enableSystem={false}>
          <LanguageProvider>{children}</LanguageProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
