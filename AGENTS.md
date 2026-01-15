You are a senior AI engineer and product-minded data engineer.
Your task is to design, implement, and deliver an end-to-end, production-grade AI system called:

“AI CSV → Business Insight Generator”

This project MUST be suitable for:
- Zoomcamp capstone evaluation
- Portfolio / GitHub showcase
- Monetizable MVP (micro-SaaS readiness)

You must think and act like a real engineer, not a tutorial generator.

────────────────────────────────────────────
PRIMARY OBJECTIVE
────────────────────────────────────────────
Build an end-to-end system that allows a user to upload a CSV file and receive:
1) Automated data profiling & validation
2) Deterministic EDA metrics and charts
3) LLM-generated business insights and recommendations
4) Exportable reports (Markdown + PDF-ready)
5) Full observability and reproducibility
6) GCP or AWS deployability

The system MUST separate:
- Truth (Python analytics)
- Reasoning (LLM interpretation)
- Orchestration (workflow control)

────────────────────────────────────────────
ARCHITECTURAL CONSTRAINTS (MANDATORY)
────────────────────────────────────────────

1. NEVER allow the LLM to see raw CSV data
2. ALL numerical calculations must be done in Python
3. LLMs are ONLY used for interpretation and explanation
4. All LLM interactions must use structured inputs (JSON)
5. Use MCP-style contracts to constrain LLM behavior
6. Use n8n for workflow orchestration (not Python scripts)
7. All components must be modular and testable

────────────────────────────────────────────
REQUIRED TECH STACK
────────────────────────────────────────────
Backend:
- Python
- FastAPI
- Pandas
- Matplotlib / Seaborn / Plotly

LLM Layer:
- MCP-style prompt schema
- Single LLM provider abstraction
- Deterministic temperature for reporting

Orchestration:
- n8n (workflow-driven execution)

Storage:
- Local filesystem or object storage
- SQLite or Postgres for metadata

Frontend:
- Streamlit OR minimal React UI

────────────────────────────────────────────
SYSTEM COMPONENTS YOU MUST IMPLEMENT
────────────────────────────────────────────

1) API Gateway (FastAPI)
   - POST /upload
   - GET /job/{job_id}
   - GET /report/{job_id}

2) Data Quality Service
   - Automated Column Standardization - Converts column names to snake_case
   - Non-Value Detection - Identifies and replaces ERROR/UNKNOWN/N/A placeholders
   - String Normalization - Converts values to lowercase snake_case
   - Smart Type Casting - Auto-detects and casts numeric and datetime columns
   - Duplicate Removal - Identifies and removes duplicate rows
   - Schema inference
   - Missing value stats
   - Data type detection
   - Validation summary
   - Output structured JSON

3) EDA Service
   - KPI computation
   - Trend detection
   - Distribution summaries
   - Anomaly detection
   - Chart generation
   - Output structured JSON + images

4) Insight Service (LLM via MCP)
   - Accepts ONLY validated metrics JSON
   - Generates:
     - Executive summary
     - Key insights
     - Risks & caveats
     - Actionable recommendations
   - Must obey constraints:
     - No speculation
     - No new numbers
     - No assumptions beyond provided context

5) Report Builder
   - Combine insights + charts
   - Output Markdown
   - Structure suitable for PDF export

6) Orchestration (n8n)
   - Triggered by CSV upload
   - Handles retries and failures
   - Supports branching:
     - Poor data quality → limited report
     - Good data quality → full report

7) Logging & Audit
   - Store:
     - Uploaded file metadata
     - Validation results
     - Metrics JSON
     - LLM prompts & responses
   - Enable reproducibility

────────────────────────────────────────────
MCP REQUIREMENTS (CRITICAL)
────────────────────────────────────────────

Define a strict MCP-style context object with:
- Business context
- Allowed metrics
- Explicit constraints
- Prohibited behaviors

Example constraints:
- “Use only provided metrics”
- “Do not infer causes without evidence”
- “Do not perform calculations”

You MUST show:
- MCP schema definition
- Example MCP payload
- Example LLM response

────────────────────────────────────────────
n8n REQUIREMENTS (CRITICAL)
────────────────────────────────────────────

You MUST:
- Design the n8n workflow
- Explain each node’s responsibility
- Provide workflow logic (pseudo or JSON)
- Justify why orchestration is externalized

n8n must handle:
- Job execution order
- Failure recovery
- Async processing

────────────────────────────────────────────
DELIVERABLES (MANDATORY)
────────────────────────────────────────────

You MUST produce:

1) Repository structure
2) Architecture diagram (textual description is fine)
3) Key service implementations (code)
4) MCP prompt schema
5) n8n workflow design
6) Example input CSV → output report
7) README.md suitable for GitHub
8) GCP or AWS deployability

────────────────────────────────────────────
QUALITY BAR (VERY IMPORTANT)
────────────────────────────────────────────

DO:
- Use clean architecture
- Explain design decisions
- Write production-quality code
- Avoid unnecessary complexity
- Prioritize correctness over flashiness

DO NOT:
- Build a notebook-only solution
- Let the LLM “analyze” raw data
- Skip error handling
- Hardcode business logic into prompts

────────────────────────────────────────────
SUCCESS CRITERIA
────────────────────────────────────────────

The project is considered successful if:
- A non-technical user can upload a CSV
- The system produces a credible business report
- Results are reproducible
- The architecture can scale
- The project can be deployed on GCP or AWS

Proceed step by step.
Explain your reasoning.
Deliver a real system, not a demo.
