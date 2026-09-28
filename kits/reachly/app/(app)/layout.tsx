import { Sidebar } from "@/components/app/sidebar";
import { Topbar } from "@/components/app/topbar";

export default function AppLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <div className="flex h-dvh overflow-hidden bg-background">
      <Sidebar />
      <div className="relative flex flex-1 flex-col overflow-hidden">
        {/* faint sky wash at the very top of the app */}
        <div
          className="pointer-events-none absolute inset-x-0 top-0 -z-0 h-64"
          style={{ background: "var(--grad-cloud)" }}
          aria-hidden
        />
        <Topbar />
        <main className="relative z-10 flex-1 overflow-y-auto p-5 lg:p-8">{children}</main>
      </div>
    </div>
  );
}
