Classify the enterprise query by source family and task type.

Return:
- query_type: factual | analytical | compliance | operational | audit
- sources: pdf | docx | sql | csv | json | audit | knowledge_base
- strategy: semantic | keyword | hybrid | sql
- needs_sql: boolean
- needs_summarization: boolean
- confidence: number between 0 and 1

