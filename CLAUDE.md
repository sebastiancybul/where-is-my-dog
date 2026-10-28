# Where Is My Dog

Mobile platform that reunites lost dogs with their owners: lost/found listings, location history on a map, chat, and real-time + push notifications. See [README.md](README.md) for the product overview and architecture, and [docs/user-stories.md](docs/user-stories.md) for the user stories.

## Repository layout

```
.
├── backend/                     # Django + DRF, Channels (Daphne), Celery, PostGIS
├── mobile/                      # Expo (React Native + TypeScript), Expo Router, NativeWind
├── docs/                        # user stories, models.png, asyncapi.yaml (WebSocket contract)
├── .github/workflows/ci.yml     # flake8 + Django tests, expo lint + tsc
├── docker-compose.yml           # local stack: db, redis, backend, celery, celery-beat
└── render.yaml                  # production deploy (with backend/start.sh)
```

Backend: four apps. Each app has `models.py`, serializers, views, `schemas.py`, `urls.py` and `tests/`; serializers and views are packages in the bigger apps and single modules in `notifications`. The tree lists only the notable files.

```
backend/
├── config/                      # settings, root URLs, ASGI routing, Celery app + beat schedule
├── users/                       # custom User, email login backend, auth + account settings endpoints
├── listings/                    # core domain: listings, photos (Cloudinary), locations (PostGIS)
│   ├── filters.py               #   multi-select filters (breed, size, gender, color)
│   ├── permissions.py           #   owner-only checks
│   ├── services/
│   │   └── duplicate_detector.py   # similar-listing matching
│   └── tasks.py                 #   Celery: expiry + expiring-soon warnings
├── chats/                       # 1:1 and group chat
│   ├── consumers.py             #   WebSocket consumer: live messages, read receipts
│   ├── middleware.py            #   ticket-based WebSocket auth
│   ├── tickets.py               #   one-time WS tickets in Redis
│   └── signals.py
└── notifications/               # inbox, presence, delivery
    ├── dispatch.py              #   single entry point: persist, then WebSocket or push
    ├── presence.py              #   online/offline tracking in Redis
    ├── consumer.py              #   per-user notifications WebSocket
    ├── push.py                  #   FCM delivery
    └── tasks.py                 #   Celery: push sending
```

Mobile:

```
mobile/
├── app/                         # Expo Router: each file is a screen
│   ├── (auth)/                  #   login, register
│   ├── (tabs)/                  #   home feed, chats, create, profile
│   ├── listing/[id]/            #   detail, edit, map, add-new-location
│   ├── chat/[id].tsx            #   conversation
│   ├── settings/                #   username, phone, password, delete account
│   └── notifications.tsx        #   notification inbox
├── components/                  # reusable UI; manage-listing/ holds the multi-step listing form
├── contexts/                    # Auth, Listing, Location, Notification (WebSocket), Push (FCM)
├── types/                       # shared TypeScript types
├── utils/                       # helpers: chatApi (photo upload), date, imagePicker
└── constants/                   # dog options (breeds, colors, ...)
```

## Data model

See the [diagram](docs/models.png).

- `User` (email login)
- `Listing` (lost/found, status, `expires_at`) with `Photo`s (Cloudinary) and `Location`s (PostGIS points; the history of sightings, one `is_primary`)
- `Conversation` with members via `ConversationMembership`, plus `Message`, `MessagePhoto`, `MessageReadStatus`
- `Notification` (persisted inbox) and `DeviceToken` (FCM)

## Commands

Backend (full stack from the repo root):

```bash
docker compose up --build
docker compose exec backend python manage.py test
docker compose exec backend python manage.py makemigrations
cd backend && flake8 .
```

Mobile (from `mobile/`):

```bash
npx expo lint
npx tsc --noEmit
npx expo start
```

## Backend conventions

- Business logic that doesn't belong in a view or serializer goes into the app's `services/`. drf-spectacular `extend_schema` decorators live in the app's `schemas.py`, not inline in views.
- Every mutating endpoint checks permissions; owner-only actions use the app's `permissions.py`.
- Defaults: JWT auth (SimpleJWT), `IsAuthenticatedOrReadOnly`, page-number pagination.
- Non-chat notifications go through `notifications.dispatch.dispatch_notification`: it persists the notification, sends it over WebSocket if the user is online, and otherwise queues a push. Don't call `notify_user` or the push helpers directly for new notification types.
- WebSocket clients authenticate with a one-time ticket from `POST /api/chats/ws-ticket/`, passed as `?ticket=`. Never put a JWT in a WebSocket URL.
- [docs/asyncapi.yaml](docs/asyncapi.yaml) is the WebSocket contract. Update it whenever WebSocket messages change.
- Tests live in `<app>/tests/test_*.py`. Use `APITestCase` for endpoints and `TestCase` for models and tasks. Build URLs with `reverse()` and route names, never hard-coded paths.
- Tests never touch external services: mock Cloudinary, FCM and the Redis ticket client with `unittest.mock.patch`, as the existing tests do.
- Migrations: generate them with `makemigrations`, commit them in the same PR as the model change, and never edit a migration that is already on `main`.
- Line length is 79 (flake8 + black). Migrations are excluded from linting.

## API versioning

- The API is moving to `/api/v1/` (REST) and `/ws/v1/` (WebSockets). Until that lands, routes live under `/api/` and `/ws/`.
- Additive changes (new endpoints, new optional fields) go into the current version.
- Breaking changes (removing or renaming fields or endpoints, changing types or meaning) require a new version.
- Swagger UI stays at `/api/docs/` and the schema at `/api/schema/`.

## Mobile conventions

- The API base URL comes from `EXPO_PUBLIC_API_URL` and the WebSocket URL from `EXPO_PUBLIC_WS_URL`. These are inlined at bundle time, so restart with `npx expo start -c` after changing them.
- Shared types live in `types/`, React contexts in `contexts/`, helpers in `utils/`.
- There is no shared API client yet: screens call `axios` directly, and `contexts/AuthContext.tsx` sets the JWT on the global axios defaults.
- Place search (Nominatim) is restricted to Poland with `countrycodes=pl`. Keep that restriction.
- Push notifications need a native dev build (`npx expo run:android`); they don't work in Expo Go.

## Workflow

- GitHub flow: branch from `main` → PR → CI + Copilot review → squash merge. `main` auto-deploys to Render.
- Branch names: `<type>/<short-description>`, e.g. `feat/demo-accounts`, `fix/mobile-type-check`.
- Commits and PR titles follow Conventional Commits: `type(scope): summary`. Types: `feat`, `fix`, `refactor`, `test`, `docs`, `ci`, `chore`. Scopes: `backend`, `mobile`, `deploy`, or an app name. The PR title becomes the squash commit on `main`.
- Keep PRs small and focused on one change.

## Rules

- Write everything in English: code, names, strings, docs.
- Comments explain why, never what. Add one only for something the code can't say: a business rule, a constraint, a workaround, or a non-obvious decision. Don't restate what the code does, and don't remove existing comments.
- Never commit secrets: `.env` files and `firebase-service-account.json` stay untracked.
- The developer runs every git command that changes state (branch, commit, push, merge). Propose them; don't run them.
- `manage.py` needs GDAL. Run it inside the `backend` container, or ask the developer to run it.

## Definition of done

- Backend changes come with new or updated tests, and the tests pass.
- `flake8`, `npx expo lint` and `npx tsc --noEmit` pass.
- New or changed endpoints have `extend_schema` docs, and the Swagger schema still builds.
- README is updated when user-visible behaviour or setup changes.

## Gotchas

- Push notifications are only sent if a Celery worker is running. Check it first when push doesn't arrive.
- Presence: the app sends a heartbeat every 30s, and the server TTL is 90s. Don't tighten these values; offline is detected through WebSocket disconnect, and the TTL is only a backstop.
- Production on Render runs Celery in eager mode (no separate worker or beat), so scheduled tasks don't run there.
- The free Render Postgres expires after 30 days and has to be recreated.
