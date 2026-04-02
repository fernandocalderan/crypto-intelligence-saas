import { AuthPanel } from "../../components/auth-panel";

type LoginPageProps = {
  searchParams?: {
    mode?: "login" | "register";
    plan?: string;
  };
};

export default function LoginPage({ searchParams }: LoginPageProps) {
  const initialMode = searchParams?.mode === "login" ? "login" : "register";
  const selectedPlan = searchParams?.plan ?? null;

  return (
    <div className="mx-auto flex min-h-[72vh] max-w-5xl items-center py-10">
      <section className="grid w-full gap-8 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-5">
          <span className="eyebrow">Acceso</span>
          <h1 className="section-title">Crea la cuenta, entra al panel y activa el plan cuando ya entiendas el producto.</h1>
          <p className="max-w-xl text-base leading-7 text-haze">
            El registro crea un usuario Free. Si vienes desde pricing, después podrás lanzar checkout para Pro o Pro+
            sin volver a introducir credenciales.
          </p>
          <div className="space-y-3 rounded-4xl border border-white/10 bg-black/10 p-6">
            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-tide">Qué obtienes al entrar</p>
            <ul className="space-y-3 text-sm leading-7 text-haze">
              <li>Acceso inmediato al dashboard con restricciones de plan.</li>
              <li>Feed de señales con scoring y evidencia.</li>
              <li>Upgrade posterior vía Stripe sin rehacer el flujo.</li>
            </ul>
          </div>
        </div>
        <AuthPanel initialMode={initialMode} selectedPlan={selectedPlan} />
      </section>
    </div>
  );
}
