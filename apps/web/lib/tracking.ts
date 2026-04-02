"use client";

type TrackPayload = {
  event: string;
  context?: string;
  properties?: Record<string, string | number | boolean | null | undefined>;
};

export async function trackEvent(payload: TrackPayload) {
  try {
    await fetch("/api/events", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload),
      keepalive: true
    });
  } catch {
    return;
  }
}
