"use client";

import { BrainCircuit, Database, Github, Heart, KeyRound, Linkedin, LockKeyhole, Mail, Network, ShieldCheck, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { login } from "@/lib/api";
import { getToken, saveSession } from "@/lib/session";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin-change-me");
  const [error, setError] = useState("");

  useEffect(() => {
    if (getToken()) router.replace("/chat");
  }, [router]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const response = await login(username, password);
      saveSession(response.access_token, response.principal);
      router.replace("/chat");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    }
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#0b0d12] text-paper">
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.035)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.035)_1px,transparent_1px)] bg-[size:48px_48px]" />
      <div className="absolute inset-0 bg-[linear-gradient(135deg,rgba(123,220,181,0.12),transparent_34%,rgba(244,184,96,0.08)_68%,transparent)]" />

      <section className="relative z-10 grid min-h-screen grid-cols-1 lg:grid-cols-[minmax(0,1fr)_480px]">
        <div className="flex min-h-[48vh] flex-col justify-between px-6 py-6 sm:px-10 lg:min-h-screen lg:px-14 lg:py-10">
          <header className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="grid h-10 w-10 place-items-center rounded border border-mint/30 bg-mint/10 shadow-[0_0_28px_rgba(123,220,181,0.16)]">
                <BrainCircuit className="h-5 w-5 text-mint" />
              </div>
              <div>
                <div className="text-sm font-semibold tracking-wide">Enterprise Secure RAG</div>
                <div className="text-xs text-paper/50">Intelligence Access Console</div>
              </div>
            </div>
            <div className="hidden items-center gap-2 rounded border border-line/80 bg-panel/60 px-3 py-2 text-xs text-paper/60 shadow-2xl shadow-black/20 backdrop-blur md:flex">
              <ShieldCheck className="h-4 w-4 text-mint" />
              RBAC enforced
            </div>
          </header>

          <div className="mx-auto flex w-full max-w-4xl flex-1 items-center py-10 lg:py-0">
            <div className="grid w-full gap-8 lg:grid-cols-[1fr_320px] lg:items-center">
              <div>
                <div className="mb-5 inline-flex items-center gap-2 rounded border border-amber/30 bg-amber/10 px-3 py-2 text-xs font-medium text-amber">
                  <Sparkles className="h-4 w-4" />
                  Secure multi-source intelligence
                </div>
                <h1 className="max-w-3xl text-4xl font-semibold leading-tight text-paper sm:text-5xl lg:text-6xl">
                  Enterprise knowledge, grounded and access-aware.
                </h1>
                <p className="mt-5 max-w-2xl text-base leading-7 text-paper/60">
                  Authenticate into a protected AI workspace built for role-aware retrieval, cited responses, and auditable enterprise workflows.
                </p>
              </div>

              <MindMapPreview />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3 text-xs text-paper/50 sm:max-w-xl">
            <Metric label="Sources" value="8" />
            <Metric label="Policy" value="RBAC" />
            <Metric label="Trace" value="Live" />
          </div>
        </div>

        <aside className="flex items-center border-t border-line/70 bg-[#11151c]/90 px-6 py-10 shadow-[0_0_80px_rgba(0,0,0,0.45)] backdrop-blur-xl sm:px-10 lg:border-l lg:border-t-0">
          <form onSubmit={submit} className="mx-auto w-full max-w-sm">
            <div className="mb-8">
              <div className="mb-4 grid h-12 w-12 place-items-center rounded border border-line bg-ink shadow-xl shadow-black/25">
                <LockKeyhole className="h-5 w-5 text-mint" />
              </div>
              <h2 className="text-2xl font-semibold tracking-tight">Sign in</h2>
              <p className="mt-2 text-sm leading-6 text-paper/50">Use your enterprise credentials to continue.</p>
            </div>

            <div className="space-y-4">
              <label className="block text-sm">
                <span className="mb-2 block text-paper/60">Username</span>
                <div className="flex items-center rounded border border-line bg-[#0c0f15] px-3 shadow-inner shadow-black/20 transition focus-within:border-mint/70">
                  <Database className="mr-2 h-4 w-4 text-paper/30" />
                  <input
                    className="focus-ring h-12 w-full bg-transparent text-sm text-paper outline-none placeholder:text-paper/30"
                    value={username}
                    onChange={(event) => setUsername(event.target.value)}
                    autoComplete="username"
                    suppressHydrationWarning
                  />
                </div>
              </label>

              <label className="block text-sm">
                <span className="mb-2 block text-paper/60">Password</span>
                <div className="flex items-center rounded border border-line bg-[#0c0f15] px-3 shadow-inner shadow-black/20 transition focus-within:border-mint/70">
                  <KeyRound className="mr-2 h-4 w-4 text-paper/30" />
                  <input
                    className="focus-ring h-12 w-full bg-transparent text-sm text-paper outline-none placeholder:text-paper/30"
                    type="password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    autoComplete="current-password"
                    suppressHydrationWarning
                  />
                </div>
              </label>
            </div>

            {error ? (
              <div className="mt-5 rounded border border-coral/30 bg-coral/10 px-3 py-2 text-sm text-coral">
                {error}
              </div>
            ) : null}

            <button className="focus-ring mt-6 flex h-12 w-full items-center justify-center gap-2 rounded bg-mint px-4 text-sm font-semibold text-ink shadow-[0_14px_44px_rgba(123,220,181,0.22)] transition hover:bg-[#8de6c3] disabled:cursor-not-allowed disabled:opacity-60" suppressHydrationWarning>
              <ShieldCheck className="h-4 w-4" />
              Continue securely
            </button>

            <div className="mt-6 border-t border-line pt-5 text-xs leading-5 text-paper/40">JWT secured access · RBAC policy enforcement</div>
          </form>
        </aside>
      </section>

      <DeveloperFooter />
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-line/70 bg-panel/50 px-3 py-3 backdrop-blur">
      <div className="text-paper/40">{label}</div>
      <div className="mt-1 text-sm font-semibold text-paper">{value}</div>
    </div>
  );
}

function MindMapPreview() {
  return (
    <div className="relative mx-auto h-[300px] w-full max-w-[340px] sm:h-[340px]">
      <div className="absolute left-1/2 top-1/2 grid h-24 w-24 -translate-x-1/2 -translate-y-1/2 place-items-center rounded border border-mint/50 bg-mint/10 shadow-[0_0_42px_rgba(123,220,181,0.18)]">
        <Network className="h-8 w-8 text-mint" />
      </div>

      <Connector className="left-[50%] top-[32%] h-[2px] w-[96px] -rotate-[34deg]" />
      <Connector className="right-[50%] top-[32%] h-[2px] w-[96px] rotate-[34deg]" />
      <Connector className="left-[50%] bottom-[32%] h-[2px] w-[104px] rotate-[34deg]" />
      <Connector className="right-[50%] bottom-[32%] h-[2px] w-[104px] -rotate-[34deg]" />

      <Node className="left-0 top-8" label="Vector" tone="mint" />
      <Node className="right-0 top-8" label="RBAC" tone="amber" />
      <Node className="bottom-8 left-2" label="Trace" tone="coral" />
      <Node className="bottom-8 right-2" label="Cite" tone="mint" />
    </div>
  );
}

function Connector({ className }: { className: string }) {
  return <div className={`absolute origin-left bg-gradient-to-r from-mint/0 via-mint/50 to-amber/40 ${className}`} />;
}

function Node({ className, label, tone }: { className: string; label: string; tone: "mint" | "amber" | "coral" }) {
  const tones = {
    mint: "border-mint/40 bg-mint/10 text-mint",
    amber: "border-amber/40 bg-amber/10 text-amber",
    coral: "border-coral/40 bg-coral/10 text-coral",
  };

  return (
    <div className={`absolute grid h-16 w-24 place-items-center rounded border text-xs font-semibold shadow-2xl shadow-black/30 backdrop-blur ${tones[tone]} ${className}`}>
      {label}
    </div>
  );
}

function DeveloperFooter() {
  const copyrightYear = "2026";
  const links = [
    {
      label: "Email Anand Raj",
      href: "mailto:anand.ar1806@gmail.com",
      icon: Mail,
    },
    {
      label: "LinkedIn profile",
      href: "https://www.linkedin.com/in/anand-raj-006a41217/",
      icon: Linkedin,
    },
    {
      label: "GitHub profile",
      href: "https://github.com/anan5093",
      icon: Github,
    },
  ];

  return (
    <footer className="relative z-10 border-t border-line/70 bg-[#0b0d12]/80 px-6 py-6 backdrop-blur-xl">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-5 text-center sm:flex-row sm:text-left">
        <div>
          <div className="text-sm font-medium text-paper/80">Designed &amp; Developed by Anand Raj</div>
          <div className="mt-1 flex items-center justify-center gap-1.5 text-xs text-paper/40 sm:justify-start">
            <span>Made with</span>
            <Heart className="h-3.5 w-3.5 fill-coral text-coral" aria-label="love" />
            <span>for secure enterprise AI</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {links.map((link) => {
            const Icon = link.icon;
            return (
              <a
                key={link.href}
                href={link.href}
                target={link.href.startsWith("http") ? "_blank" : undefined}
                rel={link.href.startsWith("http") ? "noreferrer" : undefined}
                aria-label={link.label}
                className="focus-ring group grid h-10 w-10 place-items-center rounded border border-line/80 bg-panel/50 text-paper/60 shadow-lg shadow-black/20 backdrop-blur transition duration-200 hover:-translate-y-0.5 hover:border-cyan-300/50 hover:text-cyan-200 hover:shadow-[0_0_28px_rgba(103,232,249,0.16)]"
              >
                <Icon className="h-4 w-4 transition duration-200 group-hover:scale-110" />
              </a>
            );
          })}
        </div>

        <div className="text-xs text-paper/40">© {copyrightYear} Enterprise Secure RAG</div>
      </div>
    </footer>
  );
}
