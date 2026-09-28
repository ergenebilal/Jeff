import { cn } from "@/lib/utils";

/**
 * Avatar — an SVG-initials chip. NO photos anywhere in Pipely; every person is
 * represented by their initials on a flat colored disc. `color` is any CSS
 * color (we pass brand-spread swatches from demo data).
 */
export function Avatar({
  initials,
  color = "var(--color-primary)",
  size = 32,
  className,
  ring = false,
}: {
  initials: string;
  color?: string;
  size?: number;
  className?: string;
  /** Add a thin white ring (for overlapping avatar stacks). */
  ring?: boolean;
}) {
  return (
    <span
      className={cn(
        "inline-grid shrink-0 place-items-center rounded-full font-semibold text-white",
        ring && "ring-2 ring-card",
        className,
      )}
      style={{
        width: size,
        height: size,
        background: color,
        fontSize: size * 0.38,
        letterSpacing: "-0.02em",
      }}
      aria-label={initials}
    >
      {initials}
    </span>
  );
}

/** A small overlapping stack of avatars. */
export function AvatarStack({
  people,
  size = 26,
  max = 4,
}: {
  people: { initials: string; color: string }[];
  size?: number;
  max?: number;
}) {
  const shown = people.slice(0, max);
  const extra = people.length - shown.length;
  return (
    <span className="inline-flex items-center">
      {shown.map((p, i) => (
        <span key={i} style={{ marginLeft: i === 0 ? 0 : -size * 0.32 }}>
          <Avatar initials={p.initials} color={p.color} size={size} ring />
        </span>
      ))}
      {extra > 0 && (
        <span
          className="ml-[-8px] inline-grid place-items-center rounded-full bg-muted font-semibold text-muted-foreground ring-2 ring-card"
          style={{ width: size, height: size, fontSize: size * 0.36 }}
        >
          +{extra}
        </span>
      )}
    </span>
  );
}
