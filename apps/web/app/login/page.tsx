export default function LoginPage() {
  return (
    <div className="mx-auto flex min-h-[72vh] max-w-5xl items-center py-10">
      <section className="grid w-full gap-8 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-5">
          <span className="eyebrow">Operator Access</span>
          <h1 className="section-title">Accede al panel de inteligencia y gestiona el producto.</h1>
          <p className="max-w-xl text-base leading-7 text-haze">
            Esta pantalla queda lista para integrar autenticación real con JWT, sesión administrada o proveedor externo en un siguiente sprint.
          </p>
        </div>
        <div className="surface p-8 sm:p-10">
          <form className="space-y-5">
            <div className="space-y-2">
              <label htmlFor="email" className="text-sm font-medium text-ink">
                Email
              </label>
              <input
                id="email"
                type="email"
                placeholder="founder@cryptointel.ai"
                className="w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-ink outline-none transition placeholder:text-haze/60 focus:border-moss/50"
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="password" className="text-sm font-medium text-ink">
                Password
              </label>
              <input
                id="password"
                type="password"
                placeholder="••••••••"
                className="w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-ink outline-none transition placeholder:text-haze/60 focus:border-moss/50"
              />
            </div>
            <button
              type="submit"
              className="w-full rounded-full bg-moss px-5 py-3 text-sm font-semibold uppercase tracking-[0.16em] text-canvas transition hover:bg-[#d2ff9d]"
            >
              Entrar
            </button>
            <p className="text-sm text-haze">
              Demo UI sin autenticación conectada todavía. La estructura está preparada para añadir auth y billing.
            </p>
          </form>
        </div>
      </section>
    </div>
  );
}

