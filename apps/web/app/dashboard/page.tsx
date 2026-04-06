import { AlertsSettingsCard } from "../../components/alerts-settings-card";
import { BaseSignalsSection } from "../../components/dashboard/base-signals-section";
import { SetupsHistory } from "../../components/dashboard/setups-history";
import { SetupsSection } from "../../components/dashboard/setups-section";
import { LogoutButton } from "../../components/logout-button";
import { StatCard } from "../../components/stat-card";
import {
  confirmCheckout,
  getAssets,
  getMarketSnapshots,
  getMyAlerts,
  getMyAlertsDebug,
  getSignalSetups,
  getSetupsPerformance,
  getSetupsHistory,
  getTelegramConnectInstructions,
  getSignalFeed
} from "../../lib/api";
import { getSessionToken, getSessionUser } from "../../lib/server-session";

const percentFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1
});

const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 2
});

const compactFormatter = new Intl.NumberFormat("en-US", {
  notation: "compact",
  maximumFractionDigits: 1
});

const fundingFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 4,
  maximumFractionDigits: 4
});

type DashboardPageProps = {
  searchParams?: {
    checkout?: string;
    session_id?: string;
  };
};

export default async function DashboardPage({ searchParams }: DashboardPageProps) {
  const token = getSessionToken();
  let user = await getSessionUser();
  let checkoutMessage: string | null = null;
  let checkoutError: string | null = null;

  if (token && searchParams?.checkout === "success" && searchParams.session_id) {
    try {
      const subscription = await confirmCheckout(searchParams.session_id, token);
      if (user) {
        user = {
          ...user,
          plan: subscription.plan,
          subscription_status: subscription.status,
          signal_limit: subscription.plan === "free" ? 2 : null,
          can_access_all_signals: subscription.plan !== "free"
        };
      }
      checkoutMessage = "Suscripción activada. El feed completo ya está disponible para esta sesión.";
    } catch {
      checkoutError = "No se pudo confirmar el checkout. Si ya pagaste, vuelve a cargar la página o revisa billing.";
    }
  }

  const dashboardPlan = user?.plan ?? "free";
  const [assets, signalFeed, setupState, setupsHistory, setupsPerformance, marketSnapshots, myAlerts, alertsDebug, telegramInstructions] = await Promise.all([
    getAssets(token),
    getSignalFeed(token),
    getSignalSetups(token, dashboardPlan),
    getSetupsHistory(token, dashboardPlan),
    getSetupsPerformance(token, dashboardPlan),
    getMarketSnapshots(token),
    getMyAlerts(token),
    getMyAlertsDebug(token),
    getTelegramConnectInstructions(token)
  ]);

  const accessPlan = user?.plan ?? signalFeed.access_plan;
  const avgScore = signalFeed.signals.length
    ? signalFeed.signals.reduce((sum, signal) => sum + signal.score, 0) / signalFeed.signals.length
    : 0;
  const hiddenSignals = Math.max(signalFeed.total_available - signalFeed.visible_count, 0);
  const lockedPreviewCount = hiddenSignals > 0 ? Math.min(hiddenSignals, 2) : 0;
  const alertState = user
    ? {
        ...myAlerts,
        plan: user.plan,
        can_receive_alerts: user.plan !== "free"
      }
    : myAlerts;

  return (
    <div className="space-y-8 py-8">
      <section className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-3">
          <span className="eyebrow">Dashboard</span>
          <h1 className="section-title">Pantalla de decisiones para Setups PRO.</h1>
          <p className="max-w-2xl text-sm leading-6 text-haze">
            {user
              ? `${user.email} · ${user.plan}.`
              : "Modo Free. Vista teaser."}
          </p>
        </div>
        {user ? <LogoutButton /> : null}
      </section>

      {checkoutMessage ? (
        <section className="rounded-3xl border border-moss/20 bg-moss/10 px-5 py-4 text-sm text-ink">Checkout confirmado.</section>
      ) : null}

      {checkoutError ? (
        <section className="rounded-3xl border border-red-300/20 bg-red-300/10 px-5 py-4 text-sm text-red-100">No se pudo confirmar el checkout.</section>
      ) : null}

      <SetupsSection setupState={setupState} accessPlan={accessPlan} />

      <AlertsSettingsCard
        initialState={alertState}
        initialDebugState={alertsDebug}
        instructions={telegramInstructions}
        isAuthenticated={Boolean(user)}
      />

      <SetupsHistory historyState={setupsHistory} performanceState={setupsPerformance} accessPlan={accessPlan} />

      <BaseSignalsSection
        signals={signalFeed.signals}
        accessPlan={accessPlan}
        lockedPreviewCount={lockedPreviewCount}
      />

      <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Tracked assets" value={String(assets.length)} accent="moss" />
        <StatCard label="Visible signals" value={String(signalFeed.visible_count)} accent="tide" />
        <StatCard label="Locked signals" value={String(hiddenSignals)} accent="ink" />
        <StatCard label="Average score" value={`${percentFormatter.format(avgScore)}/10`} accent="moss" />
      </section>

      <section className="surface p-6 sm:p-8">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-haze">Market data</p>
            <h2 className="mt-2 text-2xl font-semibold text-ink">Snapshots</h2>
          </div>
        </div>
        <div className="space-y-4">
          {marketSnapshots.map((snapshot) => (
            <div
              key={`${snapshot.symbol}-${snapshot.captured_at}`}
              className="grid gap-3 rounded-3xl border border-white/8 bg-black/10 p-4 lg:grid-cols-[1.1fr_1fr_0.9fr_0.9fr_1.2fr]"
            >
              <div>
                <p className="text-lg font-semibold text-ink">{snapshot.symbol}</p>
                <p className="text-sm text-haze">
                  {snapshot.source} · {snapshot.timeframe}
                </p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.16em] text-haze">Price / 24h</p>
                <p className="mt-1 text-base font-medium text-ink">{currencyFormatter.format(snapshot.price_usd)}</p>
                <p className={`text-sm ${snapshot.change_24h >= 0 ? "text-moss" : "text-red-300"}`}>
                  {snapshot.change_24h >= 0 ? "+" : ""}
                  {percentFormatter.format(snapshot.change_24h)}%
                </p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.16em] text-haze">Funding / OI</p>
                <p className="mt-1 text-base font-medium text-ink">{fundingFormatter.format(snapshot.funding_rate)}</p>
                <p className="text-sm text-haze">
                  OI {snapshot.oi_change_24h >= 0 ? "+" : ""}
                  {percentFormatter.format(snapshot.oi_change_24h)}%
                </p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.16em] text-haze">Volume</p>
                <p className="mt-1 text-base font-medium text-ink">{compactFormatter.format(snapshot.volume_24h)}</p>
                <p className="text-sm text-haze">Avg {compactFormatter.format(snapshot.avg_volume_24h)}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.16em] text-haze">Captured</p>
                <p className="mt-1 text-base font-medium text-ink">
                  {new Date(snapshot.captured_at).toLocaleString()}
                </p>
                <p className="text-sm text-haze">Momentum {percentFormatter.format(snapshot.momentum_score)}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <details className="surface p-6 sm:p-8">
        <summary className="cursor-pointer list-none">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div className="space-y-3">
              <span className="eyebrow">Universe snapshot</span>
              <h2 className="section-title">Activos y mercado.</h2>
            </div>
            <div className="rounded-full border border-white/10 bg-black/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-ink">
              Abrir
            </div>
          </div>
        </summary>

        <div className="mt-6 border-t border-white/8 pt-6">
          <div className="space-y-4">
            {assets.map((asset) => (
              <div
                key={asset.symbol}
                className="grid gap-3 rounded-3xl border border-white/8 bg-black/10 p-4 sm:grid-cols-[1.2fr_1fr_1fr_1fr]"
              >
                <div>
                  <p className="text-lg font-semibold text-ink">{asset.symbol}</p>
                  <p className="text-sm text-haze">{asset.name}</p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-[0.16em] text-haze">Price</p>
                  <p className="mt-1 text-base font-medium text-ink">{currencyFormatter.format(asset.price_usd)}</p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-[0.16em] text-haze">24h</p>
                  <p className={`mt-1 text-base font-medium ${asset.change_24h >= 0 ? "text-moss" : "text-red-300"}`}>
                    {asset.change_24h >= 0 ? "+" : ""}
                    {percentFormatter.format(asset.change_24h)}%
                  </p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-[0.16em] text-haze">Momentum</p>
                  <p className="mt-1 text-base font-medium text-ink">{percentFormatter.format(asset.momentum_score)}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </details>
    </div>
  );
}
