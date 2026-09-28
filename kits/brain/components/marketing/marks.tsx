/* ── Inline-SVG fake-company wordmarks for the trusted-by row ───────────────── */
export function CompanyMark({ name }: { name: string }) {
  const glyphs: Record<string, React.ReactNode> = {
    Northwind: <path d="M3 17 L9 4 L12 11 L15 4 L21 17" />,
    Parable: <circle cx="12" cy="11" r="7" />,
    Formwork: <path d="M4 5 h16 v4 h-6 v9 h-4 v-9 h-6 z" />,
    Cedarworks: <path d="M12 3 L20 18 H4 Z M12 9 L16 17 H8 Z" />,
    Lumen: <path d="M6 4 v14 h10" />,
    Brightline: <path d="M4 12 h16 M12 5 v14" />,
    Meridian: <path d="M4 18 L9 6 L12 14 L15 6 L20 18" />,
    Harvest: <path d="M12 4 c5 4 5 10 0 14 c-5 -4 -5 -10 0 -14 z" />,
  };
  return (
    <span className="inline-flex items-center gap-2 text-muted-foreground/70">
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
        {glyphs[name]}
      </svg>
      <span className="text-[15px] font-semibold tracking-tight">{name}</span>
    </span>
  );
}

/** SVG-initial avatar for testimonials (no photos). */
export function InitialAvatar({ name, i = 0 }: { name: string; i?: number }) {
  const grads = [
    "linear-gradient(140deg, oklch(60% 0.17 282), oklch(48% 0.2 300))",
    "linear-gradient(140deg, oklch(62% 0.15 152), oklch(52% 0.16 175))",
    "linear-gradient(140deg, oklch(60% 0.17 320), oklch(50% 0.18 300))",
    "linear-gradient(140deg, oklch(66% 0.13 240), oklch(54% 0.15 260))",
    "linear-gradient(140deg, oklch(72% 0.14 70), oklch(62% 0.15 50))",
  ];
  const initials = name.split(" ").map((p) => p[0]).join("").slice(0, 2).toUpperCase();
  return (
    <span
      className="grid h-10 w-10 shrink-0 place-items-center rounded-full text-[13px] font-bold text-white shadow-pill"
      style={{ backgroundImage: grads[i % grads.length] }}
    >
      {initials}
    </span>
  );
}
