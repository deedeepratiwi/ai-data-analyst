# AI ENGINEERING GUIDELINES (READ FIRST)

This repository implements a production-grade AI analytics system.

## Role
You are acting as a senior AI engineer building a production-grade system.

## Non-negotiable Rules
- LLMs never see raw CSV data
- All calculations must be done in Python
- LLMs only interpret structured JSON
- MCP schemas must be used for LLM interaction
- Orchestration is handled by n8n

## Copilot Instructions
- Follow existing module boundaries
- Do not introduce notebook-only solutions
- Do not embed business logic in prompts
- Prefer explicit, readable code over clever tricks

## Architecture Principles
- Separation of concerns
- Deterministic analytics
- Reproducible outputs
- No notebook-only solutions