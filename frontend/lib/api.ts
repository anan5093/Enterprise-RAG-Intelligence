import type { QueryResponse, TokenResponse } from "@/types/rag";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function login(username: string, password: string): Promise<TokenResponse> {
  const response = await fetch(`${API_BASE}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) throw new Error("Invalid username or password");
  return response.json();
}

export async function queryRag(token: string, query: string): Promise<QueryResponse> {
  const response = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ query }),
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

export async function ingestSource(token: string, payload: unknown) {
  const response = await fetch(`${API_BASE}/ingest`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

export async function getAuditLogs(token: string) {
  const response = await fetch(`${API_BASE}/audit-logs`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

