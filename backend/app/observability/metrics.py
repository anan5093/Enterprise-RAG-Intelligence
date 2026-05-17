from prometheus_client import Counter, Histogram

QUERY_COUNTER = Counter("rag_queries_total", "Total RAG queries", ["role", "query_type"])
ACCESS_DENIED_COUNTER = Counter("rag_access_denied_chunks_total", "Denied chunks before generation")
QUERY_LATENCY = Histogram("rag_query_latency_seconds", "RAG query latency")
HALLUCINATION_REFUSALS = Counter("rag_hallucination_refusals_total", "Refusals due to missing authorized evidence")

