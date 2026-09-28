import type { Metadata } from "next";
// ── FONTS ─────────────────────────────────────────────────────────────────
// Distinctive, NOT Inter/Roboto. Schibsted Grotesk drives the UI/display voice;
// JetBrains Mono powers labels, counts, citations and source paths. The setup
// can swap these — keep the CSS variable names (--font-sans-app /
// --font-display-app / --font-mono-app) so globals.css picks them up.
import { Schibsted_Grotesk, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";
import { LanguageProvider } from "@/components/i18n/language-provider";
import appConfig from "@/app.config";
import { DEFAULT_LANG } from "@/lib/i18n/config";

const sans = Schibsted_Grotesk({
  variable: "--font-sans-app",
  subsets: ["latin"],
  display: "swap",
  weight: ["400", "500", "600", "700", "800"],
});

// Schibsted Grotesk also serves as the display face — crisp, geometric, modern.
const display = Schibsted_Grotesk({
  variable: "--font-display-app",
  subsets: ["latin"],
  display: "swap",
  weight: ["600", "700", "800", "900"],
});

const mono = JetBrains_Mono({
  variable: "--font-mono-app",
  subsets: ["latin"],
  display: "swap",
  weight: ["400", "500", "600", "700"],
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
