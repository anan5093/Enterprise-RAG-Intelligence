"use client";

import { Upload } from "lucide-react";
import { FormEvent, useState } from "react";
import { Shell } from "@/components/Shell";
import { ingestSource } from "@/lib/api";
import { getToken } from "@/lib/session";

export default function UploadPage() {
  const [path, setPath] = useState("/mnt/d/rag_project/examples/data/finance_controls.csv");
  const [sourceType, setSourceType] = useState("csv");
  const [department, setDepartment] = useState("finance");
  const [roles, setRoles] = useState("Finance,Compliance");
  const [result, setResult] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    const token = getToken();
    if (!token) return;
    const payload = {
      path,
      source_type: sourceType,
      department,
      owner: department,
      confidentiality: "confidential",
      allowed_roles: roles.split(",").map((role) => role.trim()),
      rbac_tags: [department, "seeded"],
    };
    const response = await ingestSource(token, payload);
    setResult(JSON.stringify(response, null, 2));
  }

  return (
    <Shell>
      <section className="mx-auto max-w-3xl p-6">
        <h1 className="text-2xl font-semibold">Source Ingestion</h1>
        <form onSubmit={submit} className="mt-6 grid gap-4">
          <label className="text-sm">
            <span className="mb-1 block text-paper/60">Server path</span>
            <input className="focus-ring w-full rounded border border-line bg-panel px-3 py-2" value={path} onChange={(event) => setPath(event.target.value)} />
          </label>
          <div className="grid grid-cols-2 gap-4">
            <label className="text-sm">
              <span className="mb-1 block text-paper/60">Source type</span>
              <select className="focus-ring w-full rounded border border-line bg-panel px-3 py-2" value={sourceType} onChange={(event) => setSourceType(event.target.value)}>
                {["pdf", "docx", "sql", "csv", "json", "audit", "knowledge_base"].map((value) => <option key={value}>{value}</option>)}
              </select>
            </label>
            <label className="text-sm">
              <span className="mb-1 block text-paper/60">Department</span>
              <input className="focus-ring w-full rounded border border-line bg-panel px-3 py-2" value={department} onChange={(event) => setDepartment(event.target.value)} />
            </label>
          </div>
          <label className="text-sm">
            <span className="mb-1 block text-paper/60">Allowed roles</span>
            <input className="focus-ring w-full rounded border border-line bg-panel px-3 py-2" value={roles} onChange={(event) => setRoles(event.target.value)} />
          </label>
          <button className="focus-ring flex w-fit items-center gap-2 rounded bg-mint px-4 py-2 font-semibold text-ink">
            <Upload className="h-4 w-4" />
            Index source
          </button>
        </form>
        {result ? <pre className="mt-6 overflow-auto rounded border border-line bg-panel p-4 text-xs">{result}</pre> : null}
      </section>
    </Shell>
  );
}

