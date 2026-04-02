import { AlertsSettingsCard } from "../../components/alerts-settings-card";
import { SetupsHistory } from "../../components/dashboard/setups-history";
import { SetupsPerformance } from "../../components/dashboard/setups-performance";
import { SetupsSection } from "../../components/dashboard/setups-section";
import { LogoutButton } from "../../components/logout-button";
import { SignalCard } from "../../components/signal-card";
import { StatCard } from "../../components/stat-card";
import { UpgradeBanner } from "../../components/upgrade-banner";
import {
  confirmCheckout,
  getAssets,
  getMarketSnapshots,
  getMyAlerts,
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
  const [assets, signalFeed, setupState, setupsHistory, setupsPerformance, marketSnapshots, myAlerts, telegramInstructions] = await Promise.all([
    getAssets(token),
    getSignalFeed(token),
    getSignalSetups(token, dashboardPlan),
    getSetupsHistory(token, dashboardPlan),
    getSetupsPerformance(token, dashboardPlan),
    getMarketSnapshots(token),
    getMyAlerts(token),
    getTelegramConnectInstructions(token)
  ]);

  const accessPlan = user?.plan ?? signalFeed.access_plan;
  const avgScore = signalFeed.signals.length
    ? signalFeed.signals.reduce((sum, signal) => sum + signal.score, 0) / signalFeed.signals.length
    : 0;
  const hiddenSignals = Math.max(signalFeed.total_available - signalFeed.visible_count, 0);
  const isFreePlan = accessPlan === "free";
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
          <h1 className="section-title">Panel de señales, snapshots y acceso por plan.</h1>
          <p className="max-w-2xl text-base leading-7 text-haze">
            {user
              ? `Sesión activa para ${user.email}. Plan actual: ${user.plan}.`
              : "Estás viendo el modo Free. Regístrate para guardar sesión y activar checkout cuando quieras."}
          </p>
        </div>
        {user ? <LogoutButton /> : null}
      </section>

      {checkoutMessage ? (
        <section className="rounded-3xl border border-moss/20 bg-moss/10 px-5 py-4 text-sm text-ink">{checkoutMessage}</section>
      ) : null}

      {checkoutError ? (
        <section className="rounded-3xl border border-red-300/20 bg-red-300/10 px-5 py-4 text-sm text-red-100">{checkoutError}</section>
      ) : null}

      <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Tracked assets" value={String(assets.length)} accent="moss" />
        <StatCard label="Visible signals" value={String(signalFeed.visible_count)} accent="tide" />
        <StatCard label="Locked signals" value={String(hiddenSignals)} accent="ink" />
        <StatCard label="Average score" value={`${percentFormatter.format(avgScore)}/10`} accent="moss" />
      </section>

      {isFreePlan && hiddenSignals > 0 ? <UpgradeBanner hiddenSignals={hiddenSignals} /> : null}

      <SetupsSection setupState={setupState} accessPlan={accessPlan} />

      <SetupsHistory historyState={setupsHistory} accessPlan={accessPlan} />

      <SetupsPerformance performanceState={setupsPerformance} accessPlan={accessPlan} />

      <AlertsSettingsCard
        initialState={alertState}
        instructions={telegramInstructions}
        isAuthenticated={Boolean(user)}
      />

      <section className="surface p-6 sm:p-8">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-haze">Market data</p>
            <h2 className="mt-2 text-2xl font-semibold text-ink">Normalized snapshots</h2>
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

      <section className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
        <div className="surface p-6 sm:p-8">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-haze">Assets</p>
              <h2 className="mt-2 text-2xl font-semibold text-ink">Universe snapshot</h2>
            </div>
          </div>
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

        <div className="surface p-6 sm:p-8">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-haze">Señales base</p>
          <h2 className="mt-2 text-2xl font-semibold text-ink">Lecturas individuales del engine</h2>
          <p className="mt-3 max-w-2xl text-sm leading-7 text-haze">
            Este bloque mantiene visibles las señales unitarias del motor. Sirven como capa técnica de inspección y
            como respaldo cuando no hay setups de confluencia válidos.
          </p>
          <div className="mt-6 space-y-4">
            {signalFeed.signals.map((signal) => (
              <SignalCard key={signal.id} signal={signal} accessPlan={accessPlan} />
            ))}
            {Array.from({ length: lockedPreviewCount }).map((_, index) => (
              <SignalCard key={`locked-${index}`} locked />
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
