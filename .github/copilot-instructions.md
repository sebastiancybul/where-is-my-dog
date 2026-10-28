# Review instructions

Django + DRF + Channels backend (`backend/`), Expo React Native + TypeScript app (`mobile/`).

## How to review

- Report real problems first: bugs, security holes, data loss, broken API contracts. Skip style issues that flake8 or ESLint already catch.
- Start each comment with its severity: **blocking** (bug, security, data loss, broken contract), **suggestion**, or **nit**.
- One comment per issue. Say why it is a problem and suggest a fix.
- If you find no real problems, say so in one sentence. Don't invent issues to fill the review.
- If the PR mixes unrelated changes, say so.

## Backend: security and data

- Writes: every mutating endpoint checks authentication and ownership (see `listings/permissions.py`). No user may change another user's listing, location, conversation or account.
- Reads: conversations and messages are visible only to their members. Querysets must filter by membership, never return all rows.
- WebSocket consumers: the ticket only identifies the user. The consumer must also check that the user is a member of the conversation before joining its group. A JWT must never appear in a WebSocket URL.
- Serializers don't expose private data (email, phone, tokens) to other users.
- File uploads validate type and size (max 5 MB, as in `PhotoSerializer`) before sending anything to Cloudinary.
- Writes that create several related rows run in `transaction.atomic`.

## Backend: correctness

- List endpoints are paginated; never return an unbounded list. Avoid N+1 queries (`select_related` / `prefetch_related`).
- New or changed endpoints have tests (`APITestCase`, URLs built with `reverse()`) and `extend_schema` docs in the app's `schemas.py`.
- Tests mock external services: Cloudinary, FCM and the Redis ticket client.
- Non-chat notifications go through `notifications.dispatch.dispatch_notification`, not the push or WebSocket helpers directly.
- When WebSocket messages change, `docs/asyncapi.yaml` is updated in the same PR.
- A PR must not modify existing migration files; it may only add new ones. Model changes include their new migration.
- Versioning: the API is moving to `/api/v1/` and `/ws/v1/`; until then routes live under `/api/` and `/ws/`. Additive changes go into the current version; breaking changes (removed or renamed field or endpoint, changed type or meaning) need a new version.
- Secrets: `.env` files and `firebase-service-account.json` must never appear in a diff. Settings come from environment variables.
- Presence: heartbeat 30s, TTL 90s. Don't tighten them; offline is detected through WebSocket disconnect.
- Production runs Celery in eager mode (no beat). Flag code that relies on scheduled tasks in production.
- Celery tasks may run twice. They check state before acting (filter on `status`, or set a guard field like `expiring_notified_at`), so a retry doesn't repeat side effects.
- New auth or messaging endpoints: suggest throttling (DRF throttle classes). The project has none yet, so mark this as a suggestion.

## Mobile

- Every API call handles both errors and loading state; a failed request must never leave an endless spinner.
- `useEffect` dependencies are correct, and WebSockets, listeners and timers are cleaned up.
- Auth tokens live in `expo-secure-store`, never in `AsyncStorage`.
- API and WebSocket URLs come from `EXPO_PUBLIC_API_URL` / `EXPO_PUBLIC_WS_URL`, never hard-coded.
- No secrets in `EXPO_PUBLIC_*` variables: they are bundled into the app.
- No `any` without a reason; shared types live in `types/`.
- Place search keeps `countrycodes=pl`: the app serves Poland only, and results from other countries confuse users.

## Low priority (nit)

- Comments explain why, never what. No commented-out code.
- Code, comments, commits and UI strings are in English (the app's UI is English).
