import { NextRequest, NextResponse } from "next/server";

import { apiUrl } from "../../../../lib/api";
import { SESSION_COOKIE_NAME } from "../../../../lib/auth-constants";

function withSessionCookie(response: NextResponse, token: string, isSecure: boolean) {
  response.cookies.set(SESSION_COOKIE_NAME, token, {
    httpOnly: true,
    sameSite: "lax",
    secure: isSecure,
    path: "/",
    maxAge: 60 * 60 * 24 * 14
  });
  return response;
}

export async function POST(request: NextRequest) {
  const isSecure = request.nextUrl.protocol === "https:";
  const payload = await request.json();
  const response = await fetch(`${apiUrl}/auth/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload),
    cache: "no-store"
  });

  const data = await response.json();
  if (!response.ok) {
    return NextResponse.json(data, { status: response.status });
  }

  return withSessionCookie(NextResponse.json(data), data.token, isSecure);
}
