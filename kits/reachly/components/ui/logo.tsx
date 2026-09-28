import { cn } from "@/lib/utils";
import appConfig from "@/app.config";

/**
 * Reachly brand mark — a bespoke inline-SVG logomark: a paper-plane / send
 * arrow lifting off, framed by two broadcasting signal arcs (the "reach"), in a
 * sky→cyan gradient. No external image. The setup can swap `appConfig.name` for
 * the wordmark; drop a real file at public/logo.svg if you have one.
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
        <linearGradient id="reachly-mark" x1="4" y1="3" x2="28" y2="29" gradientUnits="userSpaceOnUse">
          <stop stopColor="oklch(70% 0.14 212)" />
          <stop offset="1" stopColor="oklch(55% 0.16 234)" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="9" fill="url(#reachly-mark)" />
      {/* broadcasting "reach" arcs */}
      <path d="M9 22.5 a8.5 8.5 0 0 1 14 -6.6" stroke="#fff" strokeOpacity="0.34" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M11.6 21.4 a5.4 5.4 0 0 1 8.6 -4.1" stroke="#fff" strokeOpacity="0.55" strokeWidth="1.5" strokeLinecap="round" />
      {/* paper-plane / send mark */}
      <path
        d="M23.4 9.2 L11 14.8 L15.4 16.6 L17.2 21 L23.4 9.2 Z"
        fill="#fff"
      />
      <path d="M15.4 16.6 L18.6 13.4" stroke="url(#reachly-mark)" strokeWidth="1.2" strokeLinecap="round" />
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
