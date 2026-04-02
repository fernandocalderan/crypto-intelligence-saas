"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { trackEvent } from "../lib/tracking";

type AuthPanelProps = {
  initialMode?: "login" | "register";
  selectedPlan?: string | null;
  redirectTo?: string;
};

export function AuthPanel({
  initialMode = "register",
  selectedPlan,
  redirectTo = "/dashboard"
}: AuthPanelProps) {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">(initialMode);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const destination = useMemo(() => {
    if (!selectedPlan || selectedPlan === "free") {
      return redirectTo;
    }
    return `/pricing?plan=${selectedPlan}`;
  }, [redirectTo, selectedPlan]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);

    trackEvent({
      event: "auth_submitted",
      context: "login",
      properties: {
        mode,
        plan: selectedPlan ?? "free"
      }
    });

    const response = await fetch(`/api/auth/${mode}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ email, password })
    });
    const payload = await response.json();

    if (!response.ok) {
      setError(payload.detail ?? "No se pudo completar el acceso");
      setLoading(false);
      return;
    }

    trackEvent({
      event: "auth_success",
      context: "login",
      properties: {
        mode,
        plan: payload.user?.plan ?? "free"
      }
    });
    router.push(destination);
    router.refresh();
  }

  return (
    <div className="surface p-8 sm:p-10">
      <div className="mb-6 flex gap-2 rounded-full border border-white/10 bg-black/10 p-1">
        {(["register", "login"] as const).map((option) => (
          <button
            key={option}
            type="button"
            onClick={() => setMode(option)}
            className={`flex-1 rounded-full px-4 py-2 text-sm font-semibold uppercase tracking-[0.14em] transition ${
              mode === option ? "bg-moss text-canvas" : "text-haze hover:text-ink"
            }`}
          >
            {option === "register" ? "Crear cuenta" : "Entrar"}
          </button>
        ))}
      </div>

      <form className="space-y-5" onSubmit={handleSubmit}>
        <div className="space-y-2">
          <label htmlFor="email" className="text-sm font-medium text-ink">
            Email
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="founder@cryptointel.ai"
            className="w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-ink outline-none transition placeholder:text-haze/60 focus:border-moss/50"
            required
          />
        </div>

        <div className="space-y-2">
          <label htmlFor="password" className="text-sm font-medium text-ink">
            Password
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="mínimo 8 caracteres"
            className="w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-ink outline-none transition placeholder:text-haze/60 focus:border-moss/50"
            minLength={8}
            required
          />
        </div>

        {selectedPlan && selectedPlan !== "free" ? (
          <div className="rounded-3xl border border-tide/20 bg-tide/10 p-4 text-sm text-haze">
            El acceso se crea primero en plan Free. Después podrás activar <span className="text-ink">{selectedPlan}</span>{" "}
            desde pricing.
          </div>
        ) : null}

        {error ? <p className="rounded-2xl border border-red-300/20 bg-red-300/10 px-4 py-3 text-sm text-red-200">{error}</p> : null}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-full bg-moss px-5 py-3 text-sm font-semibold uppercase tracking-[0.16em] text-canvas transition hover:bg-[#d2ff9d] disabled:cursor-not-allowed disabled:opacity-70"
        >
          {loading ? "Procesando..." : mode === "register" ? "Crear cuenta" : "Entrar"}
        </button>
      </form>
    </div>
  );
}
