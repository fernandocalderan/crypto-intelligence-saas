"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import {
  AlertSettings,
  connectTelegramAlerts,
  sendTelegramTest,
  TelegramConnectInstructions,
  updateAlertPreferences
} from "../lib/api";
import { trackEvent } from "../lib/tracking";

type AlertsSettingsCardProps = {
  initialState: AlertSettings;
  instructions: TelegramConnectInstructions;
  isAuthenticated: boolean;
};

type FeedbackState = {
  tone: "success" | "error";
  message: string;
} | null;

function FeedbackBanner({ feedback }: { feedback: FeedbackState }) {
  if (!feedback) {
    return null;
  }

  if (feedback.tone === "error") {
    return <p className="rounded-2xl border border-red-300/20 bg-red-300/10 px-4 py-3 text-sm text-red-100">{feedback.message}</p>;
  }

  return <p className="rounded-2xl border border-moss/20 bg-moss/10 px-4 py-3 text-sm text-ink">{feedback.message}</p>;
}

export function AlertsSettingsCard({
  initialState,
  instructions,
  isAuthenticated
}: AlertsSettingsCardProps) {
  const router = useRouter();
  const [settings, setSettings] = useState(initialState);
  const [telegramChatId, setTelegramChatId] = useState(initialState.telegram_chat_id ?? "");
  const [telegramEnabled, setTelegramEnabled] = useState(initialState.telegram_enabled);
  const [emailEnabled, setEmailEnabled] = useState(initialState.email_enabled);
  const [minScore, setMinScore] = useState(String(initialState.min_score));
  const [minConfidence, setMinConfidence] = useState(String(initialState.min_confidence));
  const [connectPanelOpen, setConnectPanelOpen] = useState(!initialState.telegram_configured);
  const [savingPreferences, setSavingPreferences] = useState(false);
  const [connectingTelegram, setConnectingTelegram] = useState(false);
  const [sendingTest, setSendingTest] = useState(false);
  const [feedback, setFeedback] = useState<FeedbackState>(null);

  const applySettings = (nextSettings: AlertSettings) => {
    setSettings(nextSettings);
    setTelegramEnabled(nextSettings.telegram_enabled);
    setEmailEnabled(nextSettings.email_enabled);
    setMinScore(String(nextSettings.min_score));
    setMinConfidence(String(nextSettings.min_confidence));
    setTelegramChatId(nextSettings.telegram_chat_id ?? "");
  };

  if (!isAuthenticated) {
    return (
      <section className="surface p-6 sm:p-8">
        <span className="eyebrow">Alertas</span>
        <h2 className="mt-3 text-2xl font-semibold text-ink">Inicia sesión para conectar Telegram y activar alertas push.</h2>
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
        <h2 className="mt-3 text-2xl font-semibold text-ink">Telegram y las alertas push están disponibles para planes Pro.</h2>
        <p className="mt-3 max-w-2xl text-base leading-7 text-haze">
          El plan Free sirve para validar el feed. Las alertas inmediatas, el test manual y la conexión Telegram se
          activan en Pro o Pro+.
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

  const isTelegramReadyForTest = settings.alerts_globally_enabled && settings.telegram_available;
  const canSendTest = Boolean(settings.telegram_configured) && !sendingTest && isTelegramReadyForTest;
  const botReference = instructions.bot_username ?? "el bot configurado para este entorno";

  async function handleConnectTelegram(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFeedback(null);

    if (!telegramChatId.trim()) {
      setFeedback({ tone: "error", message: "Debes indicar un chat ID de Telegram antes de vincular la cuenta." });
      return;
    }

    setConnectingTelegram(true);

    try {
      trackEvent({
        event: "telegram_connect_clicked",
        context: "dashboard",
        properties: {
          plan: settings.plan
        }
      });

      const nextSettings = await connectTelegramAlerts({
        telegram_chat_id: telegramChatId.trim(),
        is_active: telegramEnabled
      });

      applySettings(nextSettings);
      setConnectPanelOpen(false);
      setFeedback({ tone: "success", message: "Telegram conectado correctamente." });
      router.refresh();
    } catch (submissionError) {
      setFeedback({
        tone: "error",
        message:
          submissionError instanceof Error
            ? submissionError.message
            : "No pudimos conectar Telegram. Revisa el chat ID y vuelve a intentarlo."
      });
    } finally {
      setConnectingTelegram(false);
    }
  }

  async function handleSavePreferences(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFeedback(null);

    if (telegramEnabled && !settings.telegram_configured) {
      setFeedback({
        tone: "error",
        message: "Conecta Telegram antes de activar las alertas por este canal."
      });
      return;
    }

    setSavingPreferences(true);

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

      const nextSettings = await updateAlertPreferences({
        min_score: Number(minScore),
        min_confidence: Number(minConfidence),
        telegram_enabled: telegramEnabled,
        email_enabled: emailEnabled
      });

      applySettings(nextSettings);
      setFeedback({
        tone: "success",
        message: "Preferencias guardadas. Recibirás alertas inmediatas de señales completas con prioridad."
      });
      router.refresh();
    } catch (submissionError) {
      setFeedback({
        tone: "error",
        message:
          submissionError instanceof Error
            ? submissionError.message
            : "No se pudo actualizar la configuración de alertas."
      });
    } finally {
      setSavingPreferences(false);
    }
  }

  async function handleSendTest() {
    setFeedback(null);
    setSendingTest(true);

    try {
      trackEvent({
        event: "telegram_test_sent",
        context: "dashboard",
        properties: {
          plan: settings.plan,
          telegram_enabled: telegramEnabled
        }
      });

      const result = await sendTelegramTest();
      setFeedback({ tone: "success", message: result.detail || "Mensaje de prueba enviado." });
    } catch (submissionError) {
      setFeedback({
        tone: "error",
        message:
          submissionError instanceof Error
            ? submissionError.message
            : "No pudimos enviar la prueba. Inicia el bot en Telegram y vuelve a intentarlo."
      });
    } finally {
      setSendingTest(false);
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
          Telegram no disponible temporalmente. Puedes dejar el chat vinculado, pero el envío real y la prueba manual
          dependen de que el bot esté operativo en este entorno.
        </div>
      ) : null}

      <div className="mt-6 grid gap-5 lg:grid-cols-[1.05fr_0.95fr]">
        <div className="space-y-5">
          <section className="rounded-[2rem] border border-white/10 bg-black/10 p-5">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-haze">Telegram</p>
                <h3 className="mt-2 text-xl font-semibold text-ink">Conecta tu chat y valida la entrega.</h3>
              </div>
              <span
                className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] ${
                  settings.telegram_configured
                    ? "border border-moss/20 bg-moss/10 text-ink"
                    : "border border-white/10 bg-black/20 text-haze"
                }`}
              >
                {settings.telegram_configured ? "Conectado" : "No conectado"}
              </span>
            </div>

            <div className="mt-5 grid gap-4 sm:grid-cols-2">
              <div className="rounded-3xl border border-white/8 bg-black/10 px-4 py-4 text-sm text-haze">
                <p className="font-semibold text-ink">Estado</p>
                <ul className="mt-3 space-y-2 leading-6">
                  <li>Telegram: {settings.telegram_enabled ? "Activado" : "Desactivado"}</li>
                  <li>Chat ID: {settings.telegram_chat_id ?? "Sin vincular"}</li>
                  <li>Bot: {botReference}</li>
                </ul>
              </div>

              <div className="rounded-3xl border border-white/8 bg-black/10 px-4 py-4 text-sm text-haze">
                <p className="font-semibold text-ink">Cómo funciona</p>
                <ul className="mt-3 space-y-2 leading-6">
                  {instructions.steps.map((step) => (
                    <li key={step}>{step}</li>
                  ))}
                </ul>
                <p className="mt-3 text-xs text-haze">{instructions.note}</p>
              </div>
            </div>

            <div className="mt-5 flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => setConnectPanelOpen((current) => !current)}
                className="rounded-full bg-moss px-5 py-3 text-sm font-semibold uppercase tracking-[0.16em] text-canvas transition hover:bg-[#d2ff9d]"
              >
                Conectar Telegram
              </button>
              <button
                type="button"
                onClick={handleSendTest}
                disabled={!canSendTest}
                className="rounded-full border border-white/12 px-5 py-3 text-sm font-semibold uppercase tracking-[0.16em] text-ink transition hover:border-moss/50 hover:text-moss disabled:cursor-not-allowed disabled:opacity-50"
              >
                {sendingTest ? "Enviando..." : "Enviar prueba"}
              </button>
            </div>

            {connectPanelOpen ? (
              <form className="mt-5 space-y-4 rounded-[2rem] border border-white/10 bg-black/15 p-5" onSubmit={handleConnectTelegram}>
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
                </div>

                <div className="rounded-3xl border border-white/8 bg-black/10 px-4 py-4 text-sm text-haze">
                  <p>
                    Abre Telegram, busca <span className="font-semibold text-ink">{botReference}</span> y pulsa{" "}
                    <span className="font-semibold text-ink">{instructions.start_command}</span> antes de vincular.
                  </p>
                </div>

                <div className="flex flex-wrap gap-3">
                  <button
                    type="submit"
                    disabled={connectingTelegram}
                    className="rounded-full bg-moss px-5 py-3 text-sm font-semibold uppercase tracking-[0.16em] text-canvas transition hover:bg-[#d2ff9d] disabled:cursor-not-allowed disabled:opacity-70"
                  >
                    {connectingTelegram ? "Vinculando..." : "Vincular"}
                  </button>
                  <button
                    type="button"
                    onClick={() => setConnectPanelOpen(false)}
                    className="rounded-full border border-white/12 px-5 py-3 text-sm font-semibold uppercase tracking-[0.16em] text-ink transition hover:border-white/25"
                  >
                    Cerrar
                  </button>
                </div>
              </form>
            ) : null}
          </section>

          <form className="rounded-[2rem] border border-white/10 bg-black/10 p-5" onSubmit={handleSavePreferences}>
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
              </div>
            </div>

            <div className="mt-5 space-y-4">
              <label className="flex items-start gap-3 rounded-3xl border border-white/8 bg-black/10 px-4 py-4 text-sm text-haze">
                <input
                  type="checkbox"
                  checked={telegramEnabled}
                  onChange={(event) => setTelegramEnabled(event.target.checked)}
                  className="mt-1 h-4 w-4 rounded border-white/15 bg-black/20 text-moss focus:ring-moss/40"
                />
                <span>
                  <span className="block font-semibold text-ink">Activar alertas por Telegram</span>
                  Cuando haya una señal nueva elegible, el backend la enviará a este chat con prioridad.
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
            </div>

            <div className="mt-5 rounded-3xl border border-white/8 bg-black/10 px-4 py-4 text-sm text-haze">
              <p className="font-semibold text-ink">Threshold efectivo</p>
              <ul className="mt-3 space-y-2 leading-6">
                <li>Score mínimo: {settings.min_score}</li>
                <li>Confidence mínima: {settings.min_confidence}</li>
              </ul>
            </div>

            <div className="mt-5">
              <FeedbackBanner feedback={feedback} />
            </div>

            <button
              type="submit"
              disabled={savingPreferences}
              className="mt-5 w-full rounded-full bg-moss px-5 py-3 text-sm font-semibold uppercase tracking-[0.16em] text-canvas transition hover:bg-[#d2ff9d] disabled:cursor-not-allowed disabled:opacity-70"
            >
              {savingPreferences ? "Guardando..." : "Guardar alertas"}
            </button>
          </form>
        </div>

        <aside className="rounded-[2rem] border border-white/10 bg-black/10 p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-haze">Estado actual</p>
          <h3 className="mt-2 text-xl font-semibold text-ink">Resumen de conexión</h3>
          <div className="mt-5 space-y-4 text-sm text-haze">
            <div className="rounded-3xl border border-white/8 bg-black/10 px-4 py-4">
              <p className="font-semibold text-ink">Telegram</p>
              <p className="mt-2">{settings.telegram_configured ? "Conectado" : "No conectado"}</p>
            </div>
            <div className="rounded-3xl border border-white/8 bg-black/10 px-4 py-4">
              <p className="font-semibold text-ink">Canal prioritario</p>
              <p className="mt-2">{settings.telegram_enabled ? "Activado" : "Desactivado"}</p>
            </div>
            <div className="rounded-3xl border border-white/8 bg-black/10 px-4 py-4">
              <p className="font-semibold text-ink">Prueba manual</p>
              <p className="mt-2">
                {canSendTest
                  ? "Lista para enviar."
                  : "Conecta tu chat y asegúrate de que Telegram esté disponible para probar la entrega."}
              </p>
            </div>
          </div>
        </aside>
      </div>
    </section>
  );
}
