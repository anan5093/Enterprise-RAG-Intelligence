"use client";

import type { Principal } from "@/types/rag";

const TOKEN_KEY = "rag_token";
const PRINCIPAL_KEY = "rag_principal";

function hasBrowserStorage() {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

export function saveSession(token: string, principal: Principal) {
  if (!hasBrowserStorage()) return;
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(PRINCIPAL_KEY, JSON.stringify(principal));
}

export function setToken(token: string) {
  if (!hasBrowserStorage()) return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function getToken(): string | null {
  if (!hasBrowserStorage()) return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getPrincipal(): Principal | null {
  if (!hasBrowserStorage()) return null;
  const raw = localStorage.getItem(PRINCIPAL_KEY);
  return raw ? JSON.parse(raw) : null;
}

export function clearToken() {
  if (!hasBrowserStorage()) return;
  localStorage.removeItem(TOKEN_KEY);
}

export function clearSession() {
  if (!hasBrowserStorage()) return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(PRINCIPAL_KEY);
}
