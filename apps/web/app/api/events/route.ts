import { NextRequest, NextResponse } from "next/server";

import { apiUrl } from "../../../lib/api";
import { SESSION_COOKIE_NAME } from "../../../lib/auth-constants";

export async function POST(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  const payload = await request.json();

  try {
    await fetch(`${apiUrl}/events/track`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {})
      },
      body: JSON.stringify(payload),
      cache: "no-store"
    });
  } catch {
    return NextResponse.json({ accepted: true }, { status: 202 });
  }

  return NextResponse.json({ accepted: true }, { status: 202 });
}
