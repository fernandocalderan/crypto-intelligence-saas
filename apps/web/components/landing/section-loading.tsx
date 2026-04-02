export default function SectionLoading() {
  return (
    <section className="surface animate-pulse p-8">
      <div className="h-6 w-28 rounded-full bg-white/10" />
      <div className="mt-5 h-10 max-w-2xl rounded-2xl bg-white/10" />
      <div className="mt-4 h-5 max-w-3xl rounded-2xl bg-white/10" />
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div className="h-28 rounded-3xl bg-black/10" />
        <div className="h-28 rounded-3xl bg-black/10" />
        <div className="h-28 rounded-3xl bg-black/10" />
      </div>
    </section>
  );
}
