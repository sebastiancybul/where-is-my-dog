# Push Notifications

The backend delivers notifications through **Firebase Cloud Messaging (FCM)**.
The REST endpoints (device-token registration, notification inbox) are
documented in Swagger at `/api/docs/`; this page covers the delivery model
behind them.

## Delivery model: online vs. offline

Every notification targets a single user. The backend decides *how* to deliver
based on that user's live presence:

- **Online** — delivered live over the WebSocket connection (see
  [`asyncapi.yaml`](asyncapi.yaml)). No push is sent.
- **Offline** — enqueued as an FCM push to all of the user's registered devices.
