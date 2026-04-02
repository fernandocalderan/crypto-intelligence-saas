import { NextRequest, NextResponse } from "next/server";

import { apiUrl } from "../../../../lib/api";
import { SESSION_COOKIE_NAME } from "../../../../lib/auth-constants";

export async function POST(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  if (!token) {
    return NextResponse.json({ detail: "Authentication required" }, { status: 401 });
  }

  const payload = await request.json();
  const response = await fetch(`${apiUrl}/billing/checkout`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload),
    cache: "no-store"
  });
  const data = await response.json();

  if (response.ok && data.is_mock && typeof data.checkout_url === "string") {
    const forwardedProto = request.headers.get("x-forwarded-proto");
    const protocol = (forwardedProto ?? request.nextUrl.protocol).replace(/:$/, "");
    const host = request.headers.get("x-forwarded-host") ?? request.headers.get("host");
    const requestOrigin = host ? `${protocol}://${host}` : request.nextUrl.origin;
    const targetUrl = new URL(data.checkout_url);
    data.checkout_url = `${requestOrigin}${targetUrl.pathname}${targetUrl.search}`;
  }

  return NextResponse.json(data, { status: response.status });
}
