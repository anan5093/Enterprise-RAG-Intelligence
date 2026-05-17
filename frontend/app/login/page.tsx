"use client";

import { LockKeyhole } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { login } from "@/lib/api";
import { saveSession } from "@/lib/session";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin-change-me");
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const response = await login(username, password);
      saveSession(response.access_token, response.principal);
      router.push("/chat");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-ink px-6 text-paper">
      <form onSubmit={submit} className="w-full max-w-sm border border-line bg-panel p-6">
        <div className="mb-6 flex items-center gap-3">
          <LockKeyhole className="h-5 w-5 text-mint" />
          <h1 className="text-lg font-semibold">Secure Login</h1>
        </div>
        <label className="mb-4 block text-sm">
          <span className="mb-1 block text-paper/60">Username</span>
          <input className="focus-ring w-full rounded border border-line bg-ink px-3 py-2" value={username} onChange={(event) => setUsername(event.target.value)} />
        </label>
        <label className="mb-4 block text-sm">
          <span className="mb-1 block text-paper/60">Password</span>
          <input className="focus-ring w-full rounded border border-line bg-ink px-3 py-2" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
        </label>
        {error ? <p className="mb-4 text-sm text-coral">{error}</p> : null}
        <button className="focus-ring w-full rounded bg-mint px-4 py-2 font-semibold text-ink">Sign in</button>
      </form>
    </main>
  );
}

