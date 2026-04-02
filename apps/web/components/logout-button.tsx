"use client";

import { useRouter } from "next/navigation";

export function LogoutButton() {
  const router = useRouter();

  async function handleLogout() {
    await fetch("/api/auth/logout", {
      method: "POST"
    });
    router.push("/");
    router.refresh();
  }

  return (
    <button
      type="button"
      onClick={handleLogout}
      className="rounded-full border border-white/15 px-4 py-2 text-sm font-semibold uppercase tracking-[0.14em] text-haze transition hover:border-moss hover:text-moss"
    >
      Salir
    </button>
  );
}
