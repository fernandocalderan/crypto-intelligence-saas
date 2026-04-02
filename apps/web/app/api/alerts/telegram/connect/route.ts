import { NextRequest, NextResponse } from "next/server";

import { apiUrl } from "../../../../../lib/api";
import { SESSION_COOKIE_NAME } from "../../../../../lib/auth-constants";

export async function POST(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  if (!token) {
    return NextResponse.json({ detail: "Authentication required" }, { status: 401 });
  }

  const payload = await request.json();
  const response = await fetch(`${apiUrl}/alerts/telegram/connect`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload),
    cache: "no-store"
  });
  const data = await response.json();

  return NextResponse.json(data, { status: response.status });
}
