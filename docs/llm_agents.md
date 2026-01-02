# LLM & Agent Workstream

Focus areas for the LLM/agents owner.

## Key files
- `app/core/trading_styles.py`: style prompts; extend/adjust prompts here.
- `app/core/llm_service.py`: provider adapters + orchestrator; add models/providers or improve parsing.
- `app/services/agent_service.py`: builds the 10-agent catalog; validates model/style combos.
- `app/api/trading_api.py`: `/decisions/*` endpoints exercise the orchestrator.

## Ideas / next steps
- Harden LLM parsing and add guardrails (schema validation, retries on malformed JSON).
- Add provider selection/quotas per cost tier; centralize model map for easier tuning.
- Expand decision payload schema (risk flags, stop levels) while keeping backward compatibility in the API responses.
- Add lightweight tests that stub provider responses and validate prompts → decisions flow.***
