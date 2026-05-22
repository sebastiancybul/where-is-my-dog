# Where Is My Dog?

Mobile application helping reunite lost dogs with their owners in Lublin, Poland.

## About

**Where Is My Dog?** is a mobile platform connecting people who have lost their dogs with those who have found them. The app uses geolocation, intelligent matching, and notifications to maximize the chances of successful reunions.

The project is focused on **Poland**.

---

> **Note:** The MVP is not yet complete. The backend is functional and below are current screenshots from the mobile interface.

## What's Already Working

**Mobile app**
- Authentication (JWT login, secure token storage)
- Browse lost/found listings — paginated, connected to API
- Multi-select filters (breed, characteristics)
- Listing detail view with card navigation
- Map view with location history on listing detail
- Multi-step create listing form (photos, location, characteristics)
- Edit and delete own listings
- Mark listing as resolved
- Profile screen with user's active and closed listings
- Settings screens (profile update, password change, account deletion)
- Loading states, skeleton loaders, pull-to-refresh

**Backend**
- REST API (Django + DRF) with JWT authentication
- Listings CRUD with photo upload (Cloudinary)
- PostGIS-based location support
- Multi-select filtering
- Automatic listing expiration (Celery)
- Basic duplicate detection
- Owner/permission checks on all mutating endpoints
- Email login with API tests
- Settings endpoints (profile update, password change, account deletion) with tests
- In-app chat (REST API + WebSocket consumer, ticket-based auth, read receipts)

**In progress**
- In-app chat (mobile UI)

---

## Screenshots

### Creating a Listing

| Step 1 | Step 2 | Step 3 | Step 4 |
|--------|--------|--------|--------|
| ![Step 1](docs/screenshots/create-form-step1.jpeg) | ![Step 2](docs/screenshots/create-form-step2.jpeg) | ![Step 3](docs/screenshots/create-form-step3.jpeg) | ![Step 4](docs/screenshots/create-form-step4.jpeg) |

| Step 5.1 | Step 5.2 | Creating... | Created |
|----------|----------|-------------|---------|
| ![Step 5.1](docs/screenshots/create-form-step5.1.jpeg) | ![Step 5.2](docs/screenshots/create-form-step5.2.jpeg) | ![Creating](docs/screenshots/creating.jpeg) | ![Created](docs/screenshots/created.jpeg) |

### Browsing & Details

| Home (Lost) | Home (Found) | Listing View |
|-------------|--------------|--------------|
| ![Home Lost](docs/screenshots/home-lost-view.jpeg) | ![Home Found](docs/screenshots/home-found-view.jpeg) | ![Listing](docs/screenshots/listing-view.jpeg) |

### Profile & Settings

| Profile | Settings |
|---------|----------|
| ![Profile](docs/screenshots/profile-view.jpeg) | ![Settings](docs/screenshots/settings-view.jpeg) |

### API Documentation

![API Docs 1](docs/screenshots/apidocs1.png)
![API Docs 2](docs/screenshots/apidocs2.png)

WebSocket API is documented in [docs/asyncapi.yaml](docs/asyncapi.yaml) (AsyncAPI 3.1.0).

---

## 1. Features

### 1.1. For Users Who Found a Dog

1. Browse "lost dog" listings in radius R
2. Add "found dog" listing with photo, characteristics, and location
3. Update listing status:
   - Found (default, expires after 48h without update)
   - Temporarily fostered (under care until owner is found)
   - Returned to owner (listing closed)
   - Expired
4. System suggests similar existing listings to prevent duplicates
5. If confirmed as same dog, can add location to existing listing
   - New location is immediately visible in location history
   - All locations displayed chronologically with timestamps
   - Users can report suspicious location updates
6. Earn loyalty points for helping reunite dogs
7. Contact owners via in-app chat

### 1.2. For Users Who Lost a Dog

1. Add "lost dog" listing with photo, characteristics, and location/area
2. Update their listing
3. Browse "found dog" listings in radius R
4. Filter by dog characteristics
5. Receive notifications about new "found dog" listings matching their dog's characteristics
6. Confirm when dog is found (awards points to finder)
7. Contact finders via in-app chat

### 1.3. For Moderators

1. Delete inappropriate listings (with reason)
2. Block users (with reason)
3. Review user reports
4. View moderation history

### 1.4. System Features

1. Email verification for new accounts
2. User reporting system
3. Geolocation: GPS auto-detect or manual area selection
4. Smart duplicate detection algorithm (compares location, characteristics, timing)
5. Automatic listing expiration (48h for "found" status without update)
6. Photo limit: 2 photos per listing
7. Loyalty points system with local rankings
8. Future: ML model for dog matching

---

## 2. Planned Tech Stack

**Backend**
- Python 3.11+
- Django 5.x + Django REST Framework
- PostgreSQL 15 + PostGIS 3.3
- Redis 7 (cache, message broker)
- Celery (async tasks, notifications)

**Mobile**
- React Native 0.72+
- TypeScript
- React Navigation
- React Native Maps

**Infrastructure**
- Docker + Docker Compose
- AWS EC2 + RDS
- Cloudinary (photo storage and compression)
- Firebase Cloud Messaging (push notifications)

---

## 3. Documentation

Full documentation is available in the [docs/](docs/) folder.

- [WebSocket API (AsyncAPI)](docs/asyncapi.yaml) — real-time chat over WSS

---

## 4. License

This project is licensed under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) — free for non-commercial use, learning, and viewing. Commercial use is not permitted.

---

## 5. Author

**Sebastian**
- GitHub: [@yethan](https://github.com/yethan4)