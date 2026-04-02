type StatCardProps = {
  label: string;
  value: string;
  accent: "moss" | "tide" | "ink";
};

const accentClasses: Record<StatCardProps["accent"], string> = {
  moss: "border-moss/30 bg-moss/10 text-moss",
  tide: "border-tide/30 bg-tide/10 text-tide",
  ink: "border-white/15 bg-white/5 text-ink"
};

export function StatCard({ label, value, accent }: StatCardProps) {
  return (
    <article className="surface p-6">
      <div className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] ${accentClasses[accent]}`}>
        {label}
      </div>
      <p className="mt-5 text-4xl font-semibold text-ink">{value}</p>
    </article>
  );
}

