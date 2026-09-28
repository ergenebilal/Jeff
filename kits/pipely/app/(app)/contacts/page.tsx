"use client";

import { useMemo, useState } from "react";
import { Plus, Search, Mail, Building2, Briefcase } from "lucide-react";
import { Avatar } from "@/components/app/avatar";
import { useLang } from "@/components/i18n/language-provider";
import { cn, formatMoney } from "@/lib/utils";
import { contacts, deals, repById, stageById } from "@/lib/demo/data";

export default function ContactsPage() {
  const { t, lang } = useLang();
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<string>(contacts[0].id);

  const rows = useMemo(
    () =>
      contacts.filter(
        (c) =>
          !query ||
          c.name.toLowerCase().includes(query.toLowerCase()) ||
          c.company.toLowerCase().includes(query.toLowerCase()) ||
          c.email.toLowerCase().includes(query.toLowerCase()),
      ),
    [query],
  );

  const active = contacts.find((c) => c.id === selected) ?? contacts[0];
  const contactDeals = deals.filter((d) => d.contactId === active.id);
  const totalValue = contactDeals.reduce((s, d) => s + d.value, 0);

  return (
    <div className="mx-auto max-w-[1500px] animate-fade-in">
      {/* header */}
      <div className="mb-6 flex flex-wrap items-center gap-3">
        <div>
          <h1 className="font-display text-2xl font-bold tracking-tight">{lang === "tr" ? "Kişiler" : "Contacts"}</h1>
          <p className="mt-0.5 text-sm text-muted-foreground">
            {contacts.length} {lang === "tr" ? "kişi ve şirket" : "people & companies"}
          </p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <div className="flex h-9 items-center gap-2 rounded-lg border border-border bg-card px-3 text-sm">
            <Search className="h-4 w-4 text-muted-foreground" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={lang === "tr" ? "Kişi ara…" : "Search contacts…"}
              className="w-40 bg-transparent text-foreground placeholder:text-muted-foreground/70 focus:outline-none sm:w-52"
            />
          </div>
          <button className="inline-flex h-9 items-center gap-1.5 rounded-lg bg-primary px-3.5 text-[13px] font-semibold text-primary-foreground shadow-sm transition-opacity hover:opacity-90">
            <Plus className="h-4 w-4" /> {lang === "tr" ? "Kişi ekle" : "Add contact"}
          </button>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_360px]">
        {/* list */}
        <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-soft">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left">
                  <th className="label-mono py-2.5 pl-4 font-medium text-muted-foreground">{lang === "tr" ? "Kişi" : "Person" }</th>
                  <th className="label-mono py-2.5 font-medium text-muted-foreground">{lang === "tr" ? "Şirket" : "Company"}</th>
                  <th className="label-mono py-2.5 font-medium text-muted-foreground">{lang === "tr" ? "Unvan" : "Title"}</th>
                  <th className="label-mono py-2.5 pr-4 text-right font-medium text-muted-foreground">{lang === "tr" ? "Açık deal" : "Open deals"}</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((c) => {
                  const isSel = c.id === selected;
                  return (
                    <tr
                      key={c.id}
                      onClick={() => setSelected(c.id)}
                      className={cn(
                        "cursor-pointer border-b border-border/60 transition-colors last:border-0",
                        isSel ? "bg-primary/[0.04]" : "hover:bg-muted/50",
                      )}
                    >
                      <td className="py-3 pl-4">
                        <div className="flex items-center gap-2.5">
                          <Avatar initials={c.initials} color={c.color} size={32} />
                          <div className="min-w-0">
                            <p className="truncate font-semibold leading-tight">{c.name}</p>
                            <p className="truncate text-xs text-muted-foreground">{c.email}</p>
                          </div>
                        </div>
                      </td>
                      <td className="py-3 text-muted-foreground">{c.company}</td>
                      <td className="py-3 text-muted-foreground">{c.title}</td>
                      <td className="py-3 pr-4 text-right">
                        <span className="rounded-full bg-primary/10 px-2 py-0.5 text-[11px] font-semibold text-primary">{c.openDeals}</span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* detail drawer */}
        <aside className="xl:sticky xl:top-2 xl:self-start">
          <div className="space-y-5 rounded-2xl border border-border bg-card p-5 shadow-soft">
            <div className="flex items-center gap-3">
              <Avatar initials={active.initials} color={active.color} size={48} />
              <div className="min-w-0">
                <p className="truncate font-display text-lg font-bold leading-tight">{active.name}</p>
                <p className="truncate text-[13px] text-muted-foreground">{active.title}</p>
              </div>
            </div>

            <div className="space-y-2.5 rounded-xl border border-border bg-muted/40 p-3 text-[13px]">
              <Row icon={Mail} value={active.email} />
              <Row icon={Building2} value={active.company} />
              <Row icon={Briefcase} value={active.title} />
            </div>

            <div className="flex items-center justify-between rounded-xl bg-primary/[0.06] px-4 py-3">
              <span className="text-sm font-medium">{lang === "tr" ? "Toplam deal değeri" : "Total deal value"}</span>
              <span className="tnum text-lg font-bold text-primary">{formatMoney(totalValue)}</span>
            </div>

            <div>
              <p className="label-mono mb-2 text-muted-foreground">{lang === "tr" ? "İlişkili deal'ler" : "Linked deals"}</p>
              <div className="space-y-2">
                {contactDeals.map((d) => {
                  const rep = repById[d.ownerId];
                  const st = stageById[d.stage];
                  return (
                    <div key={d.id} className="rounded-xl border border-border p-3">
                      <div className="flex items-center justify-between">
                        <p className="text-[13px] font-semibold">{d.title}</p>
                        <span className="tnum text-[13px] font-bold">{formatMoney(d.value)}</span>
                      </div>
                      <div className="mt-1.5 flex items-center gap-2">
                        <span
                          className="inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-[10px] font-semibold"
                          style={{ background: `color-mix(in oklch, ${st.color} 14%, transparent)`, color: st.color }}
                        >
                          {t(st.label)}
                        </span>
                        <Avatar initials={rep.initials} color={rep.color} size={16} />
                        <span className="text-[11px] text-muted-foreground">{rep.name.split(" ")[0]}</span>
                      </div>
                    </div>
                  );
                })}
                {contactDeals.length === 0 && (
                  <p className="text-[13px] text-muted-foreground">{lang === "tr" ? "Henüz deal yok." : "No deals yet."}</p>
                )}
              </div>
            </div>

            <button className="flex w-full items-center justify-center gap-1.5 rounded-lg bg-primary py-2.5 text-[13px] font-semibold text-primary-foreground transition-opacity hover:opacity-90">
              <Plus className="h-4 w-4" /> {lang === "tr" ? "Bu kişiye deal ekle" : "Add deal for contact"}
            </button>
          </div>
        </aside>
      </div>
    </div>
  );
}

function Row({ icon: I, value }: { icon: typeof Mail; value: string }) {
  return (
    <div className="flex items-center gap-2.5">
      <I className="h-4 w-4 shrink-0 text-muted-foreground" />
      <span className="truncate">{value}</span>
    </div>
  );
}
