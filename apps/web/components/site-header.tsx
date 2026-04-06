import Link from "next/link";
import Image from "next/image";

const links = [
  { href: "/", label: "Inicio" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/pricing", label: "Planes" },
  { href: "/login", label: "Acceso" }
];

export function SiteHeader() {
  return (
    <header className="surface sticky top-4 z-20 mb-8 flex flex-col gap-5 px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
      <Link href="/" className="flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center overflow-hidden rounded-2xl border border-white/10 bg-black/10">
          <Image src="/logomarca.png" alt="Crypto Intelligence" width={44} height={44} className="h-11 w-11 object-cover" />
        </div>
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.22em] text-haze">Crypto Intelligence</p>
          <p className="text-sm text-ink">Setups PRO.</p>
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
        <Link
          href="/pricing"
          className="rounded-full bg-moss px-4 py-2 text-sm font-semibold uppercase tracking-[0.14em] text-canvas transition hover:bg-[#d2ff9d]"
        >
          Ver Setups PRO
        </Link>
      </nav>
    </header>
  );
}
