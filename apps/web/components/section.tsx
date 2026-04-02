import { ReactNode } from "react";

type SectionProps = {
  id?: string;
  eyebrow?: string;
  title: string;
  description?: string;
  className?: string;
  children: ReactNode;
};

export function Section({ id, eyebrow, title, description, className = "", children }: SectionProps) {
  return (
    <section id={id} className={`space-y-6 ${className}`.trim()}>
      <div className="space-y-3">
        {eyebrow ? <span className="eyebrow">{eyebrow}</span> : null}
        <h2 className="section-title max-w-3xl">{title}</h2>
        {description ? <p className="max-w-3xl text-base leading-7 text-haze">{description}</p> : null}
      </div>
      {children}
    </section>
  );
}
