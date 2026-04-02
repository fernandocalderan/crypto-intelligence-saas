"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import {
  AlertSettings,
  connectTelegramAlerts,
  updateAlertPreferences
} from "../lib/api";
import { trackEvent } from "../lib/tracking";

type AlertsSettingsCardProps = {
  initialState: AlertSettings;
  isAuthenticated: boolean;
};

export function AlertsSettingsCard({
  initialState,
  isAuthenticated
}: AlertsSettingsCardProps) {
  const router = useRouter();
  const [settings, setSettings] = useState(initialState);
  const [telegramChatId, setTelegramChatId] = useState(initialState.telegram_chat_id ?? "");
  const [telegramEnabled, setTelegramEnabled] = useState(initialState.telegram_enabled);
  const [emailEnabled, setEmailEnabled] = useState(initialState.email_enabled);
  const [minScore, setMinScore] = useState(String(initialState.min_score));
  const [minConfidence, setMinConfidence] = useState(String(initialState.min_confidence));
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!isAuthenticated) {
    return (
      <section className="surface p-6 sm:p-8">
        <span className="eyebrow">Alertas</span>
        <h2 className="mt-3 text-2xl font-semibold text-ink">Inicia sesión para configurar alertas push.</h2>
        <p className="mt-3 max-w-2xl text-base leading-7 text-haze">
          Las alertas inmediatas se vinculan a tu cuenta. Primero crea sesión y luego conecta Telegram desde este mismo
          dashboard.
        </p>
        <Link
          href="/login"
          className="mt-6 inline-flex rounded-full bg-moss px-6 py-3 text-sm font-semibold uppercase tracking-[0.16em] text-canvas transition hover:bg-[#d2ff9d]"
        >
          Ir a acceso
        </Link>
      </section>
    );
  }

  if (settings.plan === "free") {
    return (
      <section className="surface border-moss/20 bg-gradient-to-r from-moss/10 via-transparent to-tide/10 p-6 sm:p-8">
        <span className="eyebrow">Alertas PRO</span>
        <h2 className="mt-3 text-2xl font-semibold text-ink">Las alertas inmediatas están disponibles para planes Pro.</h2>
        <p className="mt-3 max-w-2xl text-base leading-7 text-haze">
          El plan Free sirve para validar el feed. Las alertas push convierten el producto en un flujo inmediato y solo
          se activan en Pro o Pro+.
        </p>
        <Link
          href="/pricing"
          className="mt-6 inline-flex rounded-full bg-moss px-6 py-3 text-sm font-semibold uppercase tracking-[0.16em] text-canvas transition hover:bg-[#d2ff9d]"
        >
          Ver planes
        </Link>
      </section>
    );
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setSuccess(null);
    setError(null);

    if (telegramEnabled && !telegramChatId.trim()) {
      setError("Debes indicar un Telegram chat ID antes de activar las alertas.");
      setLoading(false);
      return;
    }

    try {
      trackEvent({
        event: "alerts_preferences_submitted",
        context: "dashboard",
        properties: {
          plan: settings.plan,
          telegram_enabled: telegramEnabled,
          email_enabled: emailEnabled
        }
      });

      if (telegramChatId.trim() || settings.telegram_chat_id) {
        await connectTelegramAlerts({
          telegram_chat_id: telegramChatId.trim() || settings.telegram_chat_id || "",
          is_active: telegramEnabled
        });
      }

      const nextSettings = await updateAlertPreferences({
        min_score: Number(minScore),
        min_confidence: Number(minConfidence),
        telegram_enabled: telegramEnabled,
        email_enabled: emailEnabled
      });

      setSettings(nextSettings);
      setTelegramChatId(nextSettings.telegram_chat_id ?? telegramChatId.trim());
      setTelegramEnabled(nextSettings.telegram_enabled);
      setEmailEnabled(nextSettings.email_enabled);
      setMinScore(String(nextSettings.min_score));
      setMinConfidence(String(nextSettings.min_confidence));
      setSuccess("Preferencias guardadas. Recibirás alertas inmediatas de señales completas con prioridad.");
      router.refresh();
    } catch (submissionError) {
      setError(
        submissionError instanceof Error
          ? submissionError.message
          : "No se pudo actualizar la configuración de alertas."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="surface p-6 sm:p-8">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-3">
          <span className="eyebrow">Alertas PRO</span>
          <h2 className="text-2xl font-semibold text-ink">Recibirás alertas inmediatas de señales completas con prioridad.</h2>
          <p className="max-w-2xl text-base leading-7 text-haze">
            El scheduler persiste señales nuevas y, si cumplen threshold, dispara el envío por Telegram de forma
            inmediata. El dashboard sigue disponible como capa pull.
          </p>
        </div>
        <div className="rounded-3xl border border-white/10 bg-black/10 px-4 py-3 text-sm text-haze">
          Plan actual: <span className="font-semibold text-ink">{settings.plan}</span>
        </div>
      </div>

      {!settings.alerts_globally_enabled ? (
        <div className="mt-6 rounded-3xl border border-yellow-300/20 bg-yellow-300/10 px-4 py-3 text-sm text-yellow-100">
          El sistema de alertas está desactivado por configuración global. Puedes dejar la preferencia guardada y
          activarlo después por flags.
        </div>
      ) : null}

      {!settings.telegram_available ? (
        <div className="mt-4 rounded-3xl border border-white/10 bg-black/10 px-4 py-3 text-sm text-haze">
          Telegram no está listo en este entorno. Si el bot token falta o el canal está desactivado, el sistema no
          enviará mensajes aunque la preferencia quede guardada.
        </div>
      ) : null}

      <form className="mt-6 grid gap-5 lg:grid-cols-[1.1fr_0.9fr]" onSubmit={handleSubmit}>
        <div className="space-y-5">
          <div className="space-y-2">
            <label htmlFor="telegram-chat-id" className="text-sm font-medium text-ink">
              Telegram chat ID
            </label>
            <input
              id="telegram-chat-id"
              type="text"
              value={telegramChatId}
              onChange={(event) => setTelegramChatId(event.target.value)}
              placeholder="123456789"
              className="w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-ink outline-none transition placeholder:text-haze/60 focus:border-moss/50"
            />
            <p className="text-sm leading-6 text-haze">
              Guarda aquí el chat ID del destino Telegram que recibirá las alertas inmediatas.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <label htmlFor="min-score" className="text-sm font-medium text-ink">
                Min score
              </label>
              <input
                id="min-score"
                type="number"
                min="1"
                max="10"
                step="0.1"
                value={minScore}
                onChange={(event) => setMinScore(event.target.value)}
                className="w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-ink outline-none transition focus:border-moss/50"
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="min-confidence" className="text-sm font-medium text-ink">
                Min confidence
              </label>
              <input
                id="min-confidence"
                type="number"
                min="0"
                max="1"
                step="0.05"
                value={minConfidence}
                onChange={(event) => setMinConfidence(event.target.value)}
                className="w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-ink outline-none transition focus:border-moss/50"
              />
              <p className="text-sm leading-6 text-haze">
                Se interpreta en rango 0-1 para alertas, aunque el dashboard siga mostrando confidence en porcentaje.
              </p>
            </div>
          </div>
        </div>

        <div className="space-y-4 rounded-4xl border border-white/10 bg-black/10 p-5">
          <label className="flex items-start gap-3 rounded-3xl border border-white/8 bg-black/10 px-4 py-4 text-sm text-haze">
            <input
              type="checkbox"
              checked={telegramEnabled}
              onChange={(event) => setTelegramEnabled(event.target.checked)}
              className="mt-1 h-4 w-4 rounded border-white/15 bg-black/20 text-moss focus:ring-moss/40"
            />
            <span>
              <span className="block font-semibold text-ink">Telegram prioritario</span>
              Activa envíos inmediatos por Telegram en cuanto el backend persista una señal nueva elegible.
            </span>
          </label>

          <label className="flex items-start gap-3 rounded-3xl border border-white/8 bg-black/10 px-4 py-4 text-sm text-haze">
            <input
              type="checkbox"
              checked={emailEnabled}
              onChange={(event) => setEmailEnabled(event.target.checked)}
              disabled={!settings.email_available}
              className="mt-1 h-4 w-4 rounded border-white/15 bg-black/20 text-moss focus:ring-moss/40 disabled:opacity-50"
            />
            <span>
              <span className="block font-semibold text-ink">Email fallback</span>
              La infraestructura queda preparada, pero el envío puede seguir desactivado por flag en este entorno.
            </span>
          </label>

          <div className="rounded-3xl border border-white/8 bg-black/10 px-4 py-4 text-sm text-haze">
            <p className="font-semibold text-ink">Estado actual</p>
            <ul className="mt-3 space-y-2 leading-6">
              <li>Telegram configurado: {settings.telegram_configured ? "sí" : "no"}</li>
              <li>Email configurado: {settings.email_configured ? "sí" : "no"}</li>
              <li>Threshold efectivo: score {settings.min_score} / confidence {settings.min_confidence}</li>
            </ul>
          </div>

          {error ? (
            <p className="rounded-2xl border border-red-300/20 bg-red-300/10 px-4 py-3 text-sm text-red-100">{error}</p>
          ) : null}
          {success ? (
            <p className="rounded-2xl border border-moss/20 bg-moss/10 px-4 py-3 text-sm text-ink">{success}</p>
          ) : null}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-full bg-moss px-5 py-3 text-sm font-semibold uppercase tracking-[0.16em] text-canvas transition hover:bg-[#d2ff9d] disabled:cursor-not-allowed disabled:opacity-70"
          >
            {loading ? "Guardando..." : "Guardar alertas"}
          </button>
        </div>
      </form>
    </section>
  );
}
