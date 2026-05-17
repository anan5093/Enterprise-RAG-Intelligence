"use client";

import type { Principal } from "@/types/rag";

const TOKEN_KEY = "rag_token";
const PRINCIPAL_KEY = "rag_principal";

export function saveSession(token: string, principal: Principal) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(PRINCIPAL_KEY, JSON.stringify(principal));
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function getPrincipal(): Principal | null {
  const raw = localStorage.getItem(PRINCIPAL_KEY);
  return raw ? JSON.parse(raw) : null;
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(PRINCIPAL_KEY);
}

