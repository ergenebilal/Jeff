import { cn } from "@/lib/utils";
import appConfig from "@/app.config";

/**
 * Brain brand mark — a bespoke inline-SVG logomark: a small knowledge graph —
 * connected nodes converging on a brighter "answer" node, in an indigo→violet
 * gradient. No external image. The setup can swap `appConfig.name` for the
 * wordmark; drop a real file at public/logo.svg if you have one.
 */
export function LogoMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 32 32"
      className={cn("h-8 w-8 shrink-0", className)}
      aria-hidden
      fill="none"
    >
      <defs>
        <linearGradient id="brain-mark" x1="4" y1="3" x2="28" y2="29" gradientUnits="userSpaceOnUse">
          <stop stopColor="oklch(62% 0.16 282)" />
          <stop offset="1" stopColor="oklch(48% 0.2 302)" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="9" fill="url(#brain-mark)" />
      {/* connecting edges of the knowledge graph */}
      <g stroke="#fff" strokeOpacity="0.5" strokeWidth="1.3" strokeLinecap="round">
        <path d="M9 10 L16 16" />
        <path d="M23 9.5 L16 16" />
        <path d="M8.5 21 L16 16" />
        <path d="M22.5 21.5 L16 16" />
      </g>
      {/* satellite source nodes */}
      <g fill="#fff" fillOpacity="0.85">
        <circle cx="9" cy="10" r="2.1" />
        <circle cx="23" cy="9.5" r="1.8" />
        <circle cx="8.5" cy="21" r="1.8" />
        <circle cx="22.5" cy="21.5" r="2.1" />
      </g>
      {/* central "answer" node — brighter, ringed */}
      <circle cx="16" cy="16" r="4.6" fill="#fff" />
      <circle cx="16" cy="16" r="2.3" fill="url(#brain-mark)" />
    </svg>
  );
}

export function Logo({
  className,
  withWordmark = true,
  withChevron = false,
  onDark = false,
}: {
  className?: string;
  withWordmark?: boolean;
  /** Render a small chevron after the wordmark (matches the sidebar header). */
  withChevron?: boolean;
  /** Use light wordmark on a dark surface (e.g. the auth brand panel). */
  onDark?: boolean;
}) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <LogoMark className="h-8 w-8 shadow-pill" />
      {withWordmark && (
        <span className="inline-flex items-center gap-1.5">
          <span
            className={cn(
              "font-display text-[17px] font-bold tracking-[-0.02em]",
              onDark ? "text-white" : "text-foreground",
            )}
          >
            {appConfig.name}
          </span>
          {withChevron && (
            <svg viewBox="0 0 16 16" className="h-3.5 w-3.5 text-muted-foreground" aria-hidden>
              <path d="M5 6l3 3 3-3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" fill="none" />
            </svg>
          )}
        </span>
      )}
    </span>
  );
}
