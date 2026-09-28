import { cn } from "@/lib/utils";
import appConfig from "@/app.config";

/**
 * Pipely brand mark — a bespoke inline-SVG logomark (a sales pipeline: three
 * descending funnel bars narrowing into a forward arrow, in a sales-green
 * gradient) + the wordmark. No external image. The setup can swap
 * `appConfig.name` for the wordmark; a matching file lives at public/logo.svg.
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
        <linearGradient id="pipely-mark" x1="4" y1="3" x2="28" y2="29" gradientUnits="userSpaceOnUse">
          <stop stopColor="oklch(68% 0.15 158)" />
          <stop offset="1" stopColor="oklch(52% 0.13 168)" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="9" fill="url(#pipely-mark)" />
      {/* funnel: three descending stage bars narrowing toward the arrow */}
      <rect x="8" y="9" width="13" height="2.6" rx="1.3" fill="#fff" fillOpacity="0.95" />
      <rect x="10" y="14.7" width="9" height="2.6" rx="1.3" fill="#fff" fillOpacity="0.7" />
      <rect x="12" y="20.4" width="5" height="2.6" rx="1.3" fill="#fff" fillOpacity="0.5" />
      {/* forward "close the deal" arrow */}
      <path
        d="M19 13 L24.5 16 L19 19"
        stroke="#fff"
        strokeWidth="2.1"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
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
  /** Use a light wordmark on a dark surface (e.g. the auth brand panel). */
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
