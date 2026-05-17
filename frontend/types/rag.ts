export type Role = "Admin" | "HR" | "Finance" | "Engineering" | "Compliance" | "Operations" | "Guest";

export type Principal = {
  user_id: string;
  username: string;
  roles: Role[];
  departments: string[];
  clearance: "public" | "internal" | "confidential" | "restricted";
};

export type Citation = {
  chunk_id: string;
  source: string;
  page?: number | null;
  table?: string | null;
  row_id?: string | null;
  score?: number | null;
};

export type RetrievalTrace = {
  query: string;
  route: {
    query_type: string;
    sources: string[];
    strategy: string;
    needs_sql: boolean;
    needs_summarization: boolean;
    confidence: number;
    rationale: string;
  };
  candidate_chunk_ids: string[];
  authorized_chunk_ids: string[];
  denied_chunk_ids: string[];
  filters_applied: string[];
  latency_ms: number;
};

export type QueryResponse = {
  answer: string;
  citations: Citation[];
  confidence: number;
  trace: RetrievalTrace;
  access_filter_explanation: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: "bearer";
  principal: Principal;
};

