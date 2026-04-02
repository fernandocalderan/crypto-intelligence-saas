import { cookies } from "next/headers";

import { getCurrentUser } from "./api";
import { SESSION_COOKIE_NAME } from "./auth-constants";

export function getSessionToken() {
  return cookies().get(SESSION_COOKIE_NAME)?.value ?? null;
}

export async function getSessionUser() {
  const token = getSessionToken();
  if (!token) {
    return null;
  }
  return getCurrentUser(token);
}
