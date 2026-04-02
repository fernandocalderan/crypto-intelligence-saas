"use client";

import Link from "next/link";

import { trackEvent } from "../lib/tracking";

type CTAButtonProps = {
  href: string;
  label: string;
  variant?: "primary" | "secondary";
  eventName: string;
  eventContext: string;
  className?: string;
};

const variantClasses = {
  primary: "bg-moss text-canvas hover:bg-[#d2ff9d]",
  secondary: "border border-white/15 text-ink hover:border-tide hover:text-tide"
};

export function CTAButton({
  href,
  label,
  variant = "primary",
  eventName,
  eventContext,
  className = ""
}: CTAButtonProps) {
  return (
    <Link
      href={href}
      onClick={() =>
        trackEvent({
          event: eventName,
          context: eventContext,
          properties: {
            href,
            label,
            variant
          }
        })
      }
      className={`rounded-full px-6 py-3 text-sm font-semibold uppercase tracking-[0.16em] transition ${variantClasses[variant]} ${className}`.trim()}
    >
      {label}
    </Link>
  );
}
