import Link from "next/link";

const links = [
  { href: "/", label: "Home" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/pricing", label: "Pricing" },
  { href: "/login", label: "Login" }
];

export function SiteHeader() {
  return (
    <header className="surface sticky top-4 z-20 mb-8 flex flex-col gap-5 px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
      <Link href="/" className="flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-moss to-tide text-sm font-bold text-canvas">
          CI
        </div>
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.22em] text-haze">Crypto Intelligence</p>
          <p className="text-sm text-ink">Signals, scoring and execution context.</p>
        </div>
      </Link>
      <nav className="flex flex-wrap items-center gap-2">
        {links.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className="rounded-full px-4 py-2 text-sm font-medium text-haze transition hover:bg-white/5 hover:text-ink"
          >
            {link.label}
          </Link>
        ))}
      </nav>
    </header>
  );
}

