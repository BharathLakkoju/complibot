# Build skill: add a WebSocket event

**Use when** a new server→client or client→server message is needed (e.g. `review.cancelled`). The base contract is engineering's v1 (PRD §13). Prefer adding optional fields to an existing event over adding a new type.

## Steps
1. **Decide durable vs ephemeral.** Durable events change state that a late joiner must see: they get a `seq` and are replayed. Ephemeral events (typing, cursor, tokens) have `seq: null` and are never replayed. Prefer durable when in doubt.
2. **Contract first.** Add it to `ai/agents/schemas/events.yaml` (the source copied to `packages/schemas/`): a dotted name in the existing style (`finding.created`, `decision.applied`, `client.hello`), camelCase payload fields with types, and whether it is persisted. For client→server messages, also define the role check, required fields, and error codes (`forbidden`, `invalid`, `version_conflict`).
3. **Codegen.** `make schemas` produces the Pydantic event model and the TS discriminated-union member.
4. **Server.**
   - Durable: emit via `events.emit(session, type, payload)` **inside the same transaction** as the state change (outbox). Never send directly to sockets.
   - Ephemeral: `realtime.broadcast_ephemeral(review_id, type, payload)`, rate-limited.
   - Client→server: add a handler in `apps/api/ws/handlers/` that checks tenant and project role (`owner`/`reviewer`/`viewer`), dedupes on `clientMsgId`, applies optimistic concurrency (`findingVersion`) where state is mutated, and answers with `decision.rejected`-style errors carrying `correlationId`.
5. **Client.** Handle the new `type` in the `useReviewSocket` reducer. TypeScript's exhaustive `switch` with a `never` check will fail the build until you do. Make the update idempotent by `seq`.
6. **Tests.**
   - Contract: the payload validates against `events.yaml`.
   - Integration: emit, then receive on two sockets; disconnect, `client.hello{lastSeq}`, and receive it exactly once between `replay.begin`/`replay.end` (persisted events only).
   - Playwright, when user-visible.
7. **Docs.** Add the event to the emitting agent's "Events emitted" section if an agent produces it.

## Pitfalls
- Payload > 8 KB in NOTIFY: NOTIFY carries only `{review_id, seq}`, and the API reads the row.
- Breaking a payload shape: add new optional fields instead, or bump to `v: 2`. The server supports N and N-1, and older clients get `error{unsupported_version}`.
- Leaking PII: payloads go to every project member. Don't include data that the receiving role can't already see via REST.
