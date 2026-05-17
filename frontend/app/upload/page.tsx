"use client";

import {
  CheckCircle2,
  Database,
  FileJson,
  FileText,
  Fingerprint,
  Lock,
  Server,
  Shield,
  ShieldCheck,
  Sparkles,
  Tags,
  Zap,
  ChevronRight,
  Activity,
  BookOpen,
  FileSpreadsheet,
} from "lucide-react";
import { FormEvent, useState } from "react";
import { AuthGuard } from "@/components/AuthGuard";
import { DashboardPanel } from "@/components/DashboardPanel";
import { MetricCard } from "@/components/MetricCard";
import { Shell } from "@/components/Shell";
import { ingestSource } from "@/lib/api";
import { getToken } from "@/lib/session";

const SUPPORTED_SOURCES = [
  { format: "JSON", icon: FileJson, description: "Structured data" },
  { format: "CSV", icon: FileSpreadsheet, description: "Tabular datasets" },
  { format: "PDF", icon: FileText, description: "Documents" },
  { format: "DOCX", icon: FileText, description: "Word documents" },
  { format: "Markdown", icon: BookOpen, description: "Knowledge bases" },
  { format: "SQL", icon: Database, description: "Database queries" },
  { format: "Audit Logs", icon: Activity, description: "Security events" },
  { format: "Knowledge Base", icon: BookOpen, description: "Enterprise KB" },
];

const WORKFLOW_STEPS = [
  { icon: Server, label: "Source Path", description: "Server-accessible" },
  { icon: Fingerprint, label: "Validation", description: "Metadata check" },
  { icon: Shield, label: "RBAC", description: "Access control" },
  { icon: Zap, label: "Chunking", description: "Format parsing" },
  { icon: Sparkles, label: "Embedding", description: "Vector generation" },
  { icon: Database, label: "Persistence", description: "FAISS index" },
];

export default function SourceRegistrationPage() {
  const [path, setPath] = useState("D:/rag_project/examples/data/security_alerts.json");
  const [sourceType, setSourceType] = useState("json");
  const [department, setDepartment] = useState("compliance");
  const [roles, setRoles] = useState("Admin,Compliance");
  const [result, setResult] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    const token = getToken();
    if (!token) return;

    setIsLoading(true);
    setError("");
    setResult("");
    const payload = {
      path,
      source_type: sourceType,
      department,
      owner: department,
      confidentiality: "confidential",
      allowed_roles: roles.split(",").map((role) => role.trim()),
      rbac_tags: [department, "seeded"],
    };
    try {
      const response = await ingestSource(token, payload);
      setResult(JSON.stringify(response, null, 2));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ingestion failed");
      setResult("");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <AuthGuard>
      <Shell>
        <section className="px-4 py-5 sm:px-6 lg:px-8">
          {/* Enhanced Header */}
          <header className="mb-8">
            <div className="inline-flex items-center gap-2 rounded border border-mint/25 bg-mint/10 px-3 py-1.5 text-xs font-medium text-mint">
              <Server className="h-3.5 w-3.5" />
              Server-side ingestion
            </div>
            <h1 className="mt-4 text-3xl font-semibold tracking-tight sm:text-4xl">Knowledge Source Registration</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-paper/50">
              Register trusted enterprise knowledge sources with RBAC-aware indexing and vector persistence. Secure server-path ingestion for authorized personnel.
            </p>
          </header>

          {/* Top Metrics */}
          <div className="mb-8 grid gap-4 md:grid-cols-4">
            <MetricCard label="Vector store" value="FAISS" detail="Local persisted index" icon={Database} tone="mint" />
            <MetricCard label="Metadata" value="RBAC" detail="Roles and sensitivity tags" icon={ShieldCheck} tone="amber" />
            <MetricCard label="Chunking" value="Auto" detail="Loader-specific parsing" icon={Tags} tone="cyan" />
            <MetricCard label="Lineage" value="Tracked" detail="Source provenance retained" icon={Fingerprint} tone="coral" />
          </div>

          {/* Main Content Grid */}
          <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
            {/* Left Column: Form and Info */}
            <div className="grid gap-6">
              {/* Source Registration Form */}
              <DashboardPanel eyebrow="Configuration" title="Register Enterprise Source">
                <form onSubmit={submit} className="grid gap-6">
                  {/* Path Input Section */}
                  <div>
                    <label className="text-sm">
                      <span className="mb-2 block font-medium text-paper">Server-accessible source path</span>
                      <input
                        className="focus-ring h-12 w-full rounded border border-line/80 bg-[#0c0f15] px-4 text-sm text-paper outline-none transition focus:border-mint/70"
                        value={path}
                        onChange={(event) => setPath(event.target.value)}
                        placeholder="D:/rag_project/examples/data/live_attack.json"
                      />
                      <p className="mt-2 text-xs text-paper/40">Source must exist on the backend server filesystem. Use forward slashes (/) or Windows paths (C:/path or C:\path).</p>
                    </label>
                  </div>

                  {/* Source Type and Department Grid */}
                  <div className="grid gap-4 md:grid-cols-2">
                    <label className="text-sm">
                      <span className="mb-2 block font-medium text-paper">Source format</span>
                      <select
                        className="focus-ring h-12 w-full rounded border border-line/80 bg-[#0c0f15] px-4 text-sm text-paper outline-none transition focus:border-mint/70"
                        value={sourceType}
                        onChange={(event) => setSourceType(event.target.value)}
                      >
                        {["pdf", "docx", "sql", "csv", "json", "audit", "knowledge_base"].map((value) => (
                          <option key={value} value={value}>
                            {value.charAt(0).toUpperCase() + value.slice(1)}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="text-sm">
                      <span className="mb-2 block font-medium text-paper">Department / Owner</span>
                      <input
                        className="focus-ring h-12 w-full rounded border border-line/80 bg-[#0c0f15] px-4 text-sm text-paper outline-none transition focus:border-mint/70"
                        value={department}
                        onChange={(event) => setDepartment(event.target.value)}
                        placeholder="e.g., compliance, engineering"
                      />
                    </label>
                  </div>

                  {/* RBAC Section */}
                  <div className="rounded border border-line/50 bg-gradient-to-br from-mint/5 to-cyan/5 p-4">
                    <div className="mb-3 flex items-center gap-2">
                      <Shield className="h-4 w-4 text-mint" />
                      <span className="text-xs font-semibold text-mint">RBAC Configuration</span>
                    </div>
                    <label className="text-sm">
                      <span className="mb-2 block font-medium text-paper">Allowed roles (comma-separated)</span>
                      <input
                        className="focus-ring h-12 w-full rounded border border-line/80 bg-[#0c0f15] px-4 text-sm text-paper outline-none transition focus:border-mint/70"
                        value={roles}
                        onChange={(event) => setRoles(event.target.value)}
                        placeholder="Admin, Compliance, Security"
                      />
                      <p className="mt-2 text-xs text-paper/40">Access control enforced at query time via RBAC policy engine.</p>
                    </label>
                  </div>

                  {/* Ingestion Architecture Info Panel */}
                  <div className="rounded border border-line/40 bg-gradient-to-br from-cyan/5 via-transparent to-mint/5 p-5">
                    <div className="mb-3 flex items-start gap-3">
                      <Server className="mt-0.5 h-5 w-5 text-cyan" />
                      <div>
                        <h3 className="text-sm font-semibold text-paper">Server-side Ingestion Architecture</h3>
                        <p className="mt-1 text-xs leading-5 text-paper/60">
                          This hackathon build uses secure server-path ingestion. Provide a trusted backend-accessible file path to register and index enterprise knowledge. Files are processed server-side without browser uploads.
                        </p>
                        <div className="mt-3 flex flex-wrap gap-2">
                          <div className="inline-flex items-center gap-1.5 rounded bg-ink/60 px-2.5 py-1 text-xs">
                            <Lock className="h-3 w-3 text-mint" />
                            <span className="text-paper/70">Encrypted at rest</span>
                          </div>
                          <div className="inline-flex items-center gap-1.5 rounded bg-ink/60 px-2.5 py-1 text-xs">
                            <ShieldCheck className="h-3 w-3 text-cyan" />
                            <span className="text-paper/70">RBAC enforced</span>
                          </div>
                          <div className="inline-flex items-center gap-1.5 rounded bg-ink/60 px-2.5 py-1 text-xs">
                            <Database className="h-3 w-3 text-amber" />
                            <span className="text-paper/70">Local FAISS persistence</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Submit Button */}
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="focus-ring group flex h-12 w-full items-center justify-center gap-2 rounded bg-gradient-to-r from-mint to-cyan px-6 text-sm font-semibold text-ink shadow-[0_14px_44px_rgba(123,220,181,0.18)] transition disabled:opacity-50 hover:shadow-[0_20px_56px_rgba(123,220,181,0.25)] hover:disabled:shadow-[0_14px_44px_rgba(123,220,181,0.18)]"
                  >
                    {isLoading ? (
                      <>
                        <Activity className="h-4 w-4 animate-spin" />
                        <span>Indexing in progress...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-4 w-4 transition group-hover:scale-110" />
                        <span>Register & Index Source</span>
                      </>
                    )}
                  </button>
                </form>
              </DashboardPanel>

              {/* Supported Formats Panel */}
              <DashboardPanel eyebrow="Capabilities" title="Supported Source Formats">
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                  {SUPPORTED_SOURCES.map((source) => {
                    const IconComponent = source.icon;
                    return (
                      <div
                        key={source.format}
                        className="group rounded border border-line/40 bg-gradient-to-br from-mint/5 to-transparent p-3 transition hover:border-mint/60 hover:bg-mint/10"
                      >
                        <div className="mb-2 grid h-10 w-10 place-items-center rounded border border-line/60 bg-ink group-hover:border-mint/60">
                          <IconComponent className="h-5 w-5 text-mint transition group-hover:scale-110" />
                        </div>
                        <h4 className="text-xs font-semibold text-paper">{source.format}</h4>
                        <p className="mt-1 text-xs text-paper/50">{source.description}</p>
                      </div>
                    );
                  })}
                </div>
              </DashboardPanel>

              {/* Ingestion Workflow Visualization */}
              <DashboardPanel eyebrow="Pipeline" title="Ingestion Workflow">
                <div className="space-y-3">
                  {WORKFLOW_STEPS.map((step, idx) => {
                    const StepIcon = step.icon;
                    return (
                      <div key={idx}>
                        <div className="flex items-center gap-3">
                          <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded border border-mint/30 bg-mint/10">
                            <StepIcon className="h-5 w-5 text-mint" />
                          </div>
                          <div className="flex-1">
                            <p className="text-xs font-semibold text-paper">{step.label}</p>
                            <p className="text-xs text-paper/50">{step.description}</p>
                          </div>
                          {idx < WORKFLOW_STEPS.length - 1 && (
                            <ChevronRight className="h-4 w-4 text-line/60" />
                          )}
                        </div>
                        {idx < WORKFLOW_STEPS.length - 1 && (
                          <div className="ml-5 h-6 border-l border-line/30" />
                        )}
                      </div>
                    );
                  })}
                </div>
              </DashboardPanel>
            </div>

            {/* Right Column: Status Panel */}
            <DashboardPanel eyebrow="Result" title="Indexing Status">
              {error && (
                <div className="rounded border border-coral/40 bg-gradient-to-br from-coral/10 to-red-900/5 p-4 mb-4">
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5 h-2 w-2 flex-shrink-0 rounded-full bg-coral" />
                    <div>
                      <h3 className="text-sm font-semibold text-coral">Ingestion failed</h3>
                      <p className="mt-1 text-xs leading-5 text-paper/60">{error}</p>
                    </div>
                  </div>
                </div>
              )}
              {result ? (
                <div className="space-y-4">
                  {/* Success State */}
                  <div className="rounded border border-mint/40 bg-gradient-to-br from-mint/10 to-cyan/5 p-4">
                    <div className="flex items-start gap-3">
                      <CheckCircle2 className="mt-0.5 h-5 w-5 flex-shrink-0 text-mint" />
                      <div>
                        <h3 className="text-sm font-semibold text-mint">Source indexed successfully</h3>
                        <p className="mt-1 text-xs text-paper/60">Source has been registered, vectorized, and persisted to FAISS index.</p>
                      </div>
                    </div>
                  </div>

                  {/* Response Data */}
                  <div>
                    <p className="mb-2 text-xs font-semibold text-paper/60 uppercase tracking-wide">Ingestion Response</p>
                    <pre className="max-h-96 overflow-auto rounded border border-line/75 bg-ink/60 p-3 text-xs leading-5 text-paper/60">
                      {result}
                    </pre>
                  </div>

                  {/* Enterprise Badges */}
                  <div className="space-y-2 border-t border-line/40 pt-4">
                    <p className="text-xs font-semibold text-paper/60 uppercase tracking-wide">Security & Compliance</p>
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-xs">
                        <ShieldCheck className="h-3.5 w-3.5 text-mint" />
                        <span className="text-paper/70">RBAC enforced</span>
                      </div>
                      <div className="flex items-center gap-2 text-xs">
                        <Fingerprint className="h-3.5 w-3.5 text-cyan" />
                        <span className="text-paper/70">Audit logging active</span>
                      </div>
                      <div className="flex items-center gap-2 text-xs">
                        <Database className="h-3.5 w-3.5 text-amber" />
                        <span className="text-paper/70">Local FAISS persistence</span>
                      </div>
                      <div className="flex items-center gap-2 text-xs">
                        <Sparkles className="h-3.5 w-3.5 text-coral" />
                        <span className="text-paper/70">Grounded retrieval ready</span>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="grid min-h-[480px] place-items-center text-center">
                  <div>
                    <div className="mx-auto grid h-16 w-16 place-items-center rounded border border-line bg-ink/60">
                      <Server className="h-8 w-8 text-mint" />
                    </div>
                    <h2 className="mt-4 text-base font-semibold text-paper">Ready for registration</h2>
                    <p className="mt-2 text-sm leading-6 text-paper/50">
                      Configure a source and submit to see chunk count, metadata verification, and persistence confirmation.
                    </p>
                  </div>
                </div>
              )}
            </DashboardPanel>
          </div>
        </section>
      </Shell>
    </AuthGuard>
  );
}
