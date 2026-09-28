import { cn } from "@/lib/utils";

/**
 * SourceIcon — clean inline-SVG glyphs for the connectors Brain indexes.
 * No external images. Each is a flat colored tile with a recognizable mark.
 */
export type SourceKey = "notion" | "drive" | "slack" | "confluence" | "github" | "web";

export const SOURCE_LABEL: Record<SourceKey, string> = {
  notion: "Notion",
  drive: "Google Drive",
  slack: "Slack",
  confluence: "Confluence",
  github: "GitHub",
  web: "Web",
};

const FILL: Record<SourceKey, string> = {
  notion: "var(--color-src-notion)",
  drive: "var(--color-src-drive)",
  slack: "var(--color-src-slack)",
  confluence: "var(--color-src-confluence)",
  github: "var(--color-src-github)",
  web: "var(--color-src-web)",
};

function Glyph({ source }: { source: SourceKey }) {
  switch (source) {
    case "notion":
      return (
        <>
          <rect x="9" y="8" width="14" height="16" rx="1.6" fill="#fff" />
          <path d="M12 12 L12 20 M12 12 L18 20 M18 12 L18 20" stroke={FILL.notion} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
        </>
      );
    case "drive":
      // tri-color triangle/folder simplified to a white triangle motif
      return (
        <>
          <path d="M13 8 L19 8 L24 17 L18 17 Z" fill="#fff" fillOpacity="0.95" />
          <path d="M13 8 L8 17 L11 22 L16 13 Z" fill="#fff" fillOpacity="0.7" />
          <path d="M11 22 L21 22 L24 17 L14 17 Z" fill="#fff" fillOpacity="0.85" />
        </>
      );
    case "slack":
      return (
        <>
          <rect x="10" y="14" width="4" height="9" rx="2" fill="#fff" />
          <rect x="9" y="10" width="9" height="4" rx="2" fill="#fff" fillOpacity="0.8" />
          <rect x="18" y="9" width="4" height="9" rx="2" fill="#fff" />
          <rect x="14" y="18" width="9" height="4" rx="2" fill="#fff" fillOpacity="0.8" />
        </>
      );
    case "confluence":
      return (
        <>
          <path d="M8 21 C12 16 16 16 24 20" stroke="#fff" strokeWidth="2.6" fill="none" strokeLinecap="round" />
          <path d="M24 11 C20 16 16 16 8 12" stroke="#fff" strokeWidth="2.6" fill="none" strokeLinecap="round" strokeOpacity="0.7" />
        </>
      );
    case "github":
      return (
        <path
          d="M16 8.4c-3.9 0-7 3.1-7 7 0 3.1 2 5.7 4.8 6.6.35.06.48-.15.48-.34v-1.2c-1.95.42-2.36-.94-2.36-.94-.32-.81-.78-1.03-.78-1.03-.64-.43.05-.42.05-.42.7.05 1.07.72 1.07.72.63 1.07 1.64.76 2.04.58.06-.45.25-.76.45-.94-1.56-.18-3.2-.78-3.2-3.46 0-.77.27-1.39.72-1.88-.07-.18-.31-.9.07-1.86 0 0 .59-.19 1.93.72a6.7 6.7 0 0 1 3.5 0c1.34-.91 1.93-.72 1.93-.72.38.96.14 1.68.07 1.86.45.49.72 1.11.72 1.88 0 2.69-1.64 3.28-3.2 3.45.25.22.48.65.48 1.3v1.93c0 .19.13.41.49.34A7 7 0 0 0 23 15.4c0-3.9-3.1-7-7-7Z"
          fill="#fff"
        />
      );
    case "web":
      return (
        <>
          <circle cx="16" cy="16" r="7" fill="none" stroke="#fff" strokeWidth="1.6" />
          <path d="M9 16 H23 M16 9 C13 12 13 20 16 23 C19 20 19 12 16 9" stroke="#fff" strokeWidth="1.4" fill="none" />
        </>
      );
  }
}

export function SourceIcon({ source, size = 28, className }: { source: SourceKey; size?: number; className?: string }) {
  return (
    <span
      className={cn("inline-grid shrink-0 place-items-center rounded-lg", className)}
      style={{ width: size, height: size, background: FILL[source] }}
    >
      <svg viewBox="0 0 32 32" width={size} height={size} aria-hidden>
        <Glyph source={source} />
      </svg>
    </span>
  );
}

/** A compact source chip: glyph + label. */
export function SourcePill({ source, className }: { source: SourceKey; className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-2 py-0.5 text-[11.5px] font-medium text-foreground/80", className)}>
      <SourceIcon source={source} size={14} className="rounded-[4px]" />
      {SOURCE_LABEL[source]}
    </span>
  );
}
