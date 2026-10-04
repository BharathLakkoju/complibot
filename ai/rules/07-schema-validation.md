# Rule 07: Output must validate against the schema

1. Every LLM call uses Bedrock Converse `toolConfig` with a single tool and `toolChoice: {tool: {name}}`. The tool's `inputSchema` is generated from the Pydantic model, so the two are the same.
2. Responses are parsed with `Model.model_validate(tool_input)` (`extra="forbid"`). Free text outside the tool call is discarded.
3. **On validation failure**: one repair attempt that sends the validation errors back as a tool-result error. A second failure is a stage failure, handled by each agent's failure table. There is no lenient parsing, no regex extraction of JSON from prose, and no silent defaults.
4. Findings are validated again against `finding.schema.yaml` before the database write (Verifier check 1) and before emitting any WebSocket event. The API's response models use the same generated types.
5. **Schema changes** bump `schema_version`. Consumers (frontend, report renderer) must accept N and N-1 during rollout. Contract tests in CI cover backend Pydantic ↔ JSON Schema ↔ generated TS types.
6. **Enums are closed.** New status or severity values require a schema version bump, never a free-form string.
