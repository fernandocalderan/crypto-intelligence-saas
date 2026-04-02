import { AuthPanel } from "../../components/auth-panel";

type SignupPageProps = {
  searchParams?: {
    plan?: string;
  };
};

export default function SignupPage({ searchParams }: SignupPageProps) {
  const selectedPlan = searchParams?.plan ?? null;

  return (
    <div className="mx-auto flex min-h-[72vh] max-w-5xl items-center py-10">
      <section className="grid w-full gap-8 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-5">
          <span className="eyebrow">Signup</span>
          <h1 className="section-title">Empieza con una cuenta Free y decide después si necesitas acceso completo.</h1>
          <p className="max-w-xl text-base leading-7 text-haze">
            El registro te da acceso inmediato al dashboard, a una muestra del feed y al flujo de upgrade sin rehacer
            credenciales.
          </p>
          <div className="space-y-3 rounded-4xl border border-white/10 bg-black/10 p-6">
            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-tide">Qué validas al entrar</p>
            <ul className="space-y-3 text-sm leading-7 text-haze">
              <li>Formato de las señales y claridad del scoring.</li>
              <li>Valor percibido del feed antes de pagar.</li>
              <li>Camino simple desde Free hacia Pro o Pro+.</li>
            </ul>
          </div>
        </div>
        <AuthPanel initialMode="register" selectedPlan={selectedPlan} />
      </section>
    </div>
  );
}
