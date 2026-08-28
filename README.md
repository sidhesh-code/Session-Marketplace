# Sessions Marketplace 🚀

A production-structured, concurrency-safe **Sessions Marketplace** platform built with Python (Django REST Framework), React (Vite & TypeScript), PostgreSQL, Nginx, and Docker Compose.

---

## 📌 Project Overview

The Sessions Marketplace connects **Creators** who publish interactive video/mentorship sessions with **Users** who browse and book available seats. 

### Key Highlights
* **Concurrency-Safe Bookings**: Enforces strict capacity limits even under high parallel traffic using PostgreSQL pessimistic row-level locking (`select_for_update`).
* **Role-Based Security**: Strict backend separation of `USER` and `CREATOR` roles enforced at the API layer.
* **OAuth 2.0 & JWT Authentication**: Google OAuth standard flow coupled with Django REST Framework Simple JWT access and refresh token management.
* **Database Invariant Integrity**: Partial database unique constraints preventing duplicate active bookings while supporting re-booking after cancellation.
* **Containerized Infrastructure**: Fully automated environment via Docker Compose with Nginx reverse proxy and persistent PostgreSQL volumes.

---

## 🏗️ Architecture

```text
Browser / Client
       │
       ▼
 ┌───────────┐
 │   Nginx   │ (Reverse Proxy - Port 8080)
 └─────┬─────┘
       │
       ├───► /api/ ────────┐
       │                   ▼
       │            ┌──────────────┐
       │            │ Django (DRF) │ (Gunicorn/WSGI - Port 8000)
       │            └──────┬───────┘
       │                   │
       │                   ▼
       │            ┌──────────────┐
       │            │  PostgreSQL  │ (Persistent Volume: postgres_data)
       │            └──────────────┘
       │
       └───► / ───────────┐
                           ▼
                    ┌──────────────┐
                    │ React (Vite) │ (Production Static Assets / Dev Server)
                    └──────────────┘
```

---

## 🛠️ Technology Stack

* **Backend**: Python 3.11, Django 5.0, Django REST Framework, Simple JWT, Pytest, Pytest-Django
* **Frontend**: React 18, Vite, TypeScript, React Router v6, Axios, Tailwind CSS
* **Database**: PostgreSQL 16
* **Reverse Proxy / Server**: Nginx
* **DevOps / Orchestration**: Docker, Docker Compose

---

## 🚀 Quick Start & Installation

### Prerequisites
* Docker Desktop & Docker Compose (`docker compose` or `docker-compose`)
* Git

### Step-by-Step Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd sessions-marketplace
   ```

2. **Configure Environment Variables**:
   Copy the example environment template:
   ```bash
   cp .env.example .env
   ```
   *(The default `.env` is pre-configured with ready-to-use local parameters for Docker evaluation).*

3. **Build and Launch Application Containers**:
   ```bash
   docker compose up --build
   ```

4. **Access the Application**:
   * **Web App (Nginx Proxy)**: [http://localhost:8080](http://localhost:8080)
   * **Backend API Base**: [http://localhost:8080/api/](http://localhost:8080/api/)
   * **Django Health Check**: [http://localhost:8080/api/health/](http://localhost:8080/api/health/)

---

## 🔐 Authentication & OAuth Flow

The application supports standard **Google OAuth 2.0** combined with stateless **JWT tokens**:

1. User clicks **"Continue with Google"** on the frontend.
2. User authenticates via Google OAuth and receives an authorization code.
3. The authorization code is sent to `/api/auth/oauth/callback/`.
4. Django exchanges the code with Google, retrieves user details, creates or fetches the `User` record, and issues:
   * `access_token` (Short-lived JWT, e.g., 60 mins)
   * `refresh_token` (Long-lived JWT, e.g., 7 days)
5. React stores JWTs in secure storage and attaches `Authorization: Bearer <access_token>` to API calls via Axios interceptor.
6. When an access token expires, Axios interceptor calls `/api/auth/token/refresh/` seamlessly.

### Developer / Local Test Auth Endpoint
For evaluation environments without live Google Client secrets:
* Click **"Quick Dev Login (User)"** or **"Quick Dev Login (Creator)"** on the `/login` page.
* Uses `/api/auth/dev-login/` to issue authentic JWT tokens instantly for testing role permissions.

---

## 🛡️ Roles & Permissions Matrix

| Capability | USER | CREATOR | Unauthenticated |
| :--- | :---: | :---: | :---: |
| Browse public session catalog | ✅ | ✅ | ✅ |
| View session details | ✅ | ✅ | ✅ |
| Book sessions | ✅ | ❌ | ❌ |
| View own active & past bookings | ✅ | ❌ | ❌ |
| Update own profile | ✅ | ✅ | ❌ |
| Create new sessions | ❌ | ✅ | ❌ |
| Edit own sessions | ❌ | ✅ | ❌ |
| Edit another creator's session | ❌ | ❌ (403) | ❌ |
| Delete own sessions | ❌ | ✅ | ❌ |
| View session booking counts | ❌ | ✅ | ❌ |

All permission checks are enforced on the Django DRF backend via custom permission classes (`IsCreator`, `IsSessionOwner`).

---

## 🔒 Concurrency-Safe Booking Engine

Booking inventory integrity is guaranteed via database transactions and PostgreSQL row locks:

```python
with transaction.atomic():
    # 1. Lock the session row to prevent race conditions
    session = Session.objects.select_for_update().get(pk=session_id)
    
    # 2. Check session start time
    if timezone.now() >= session.start_time:
        raise BookingError("Session has already started.", status_code=409)
        
    # 3. Check duplicate active booking
    if Booking.objects.filter(user=user, session=session, status='ACTIVE').exists():
        raise BookingError("You already have an active booking.", status_code=409)
        
    # 4. Check session capacity against active bookings
    active_count = Booking.objects.filter(session=session, status='ACTIVE').count()
    if active_count >= session.capacity:
        raise BookingError("Session is full.", status_code=409)
        
    # 5. Create booking
    booking = Booking.objects.create(user=user, session=session, status='ACTIVE')
```

---

## 💾 Database Persistence

PostgreSQL database state is persisted using a named Docker volume:
```yaml
volumes:
  postgres_data:
```
Database records survive container restarts and rebuilds (`docker compose restart` or `docker compose up --build`).

---

## 🧪 Running Automated Tests

Run backend tests (including unit tests, authorization checks, and the PostgreSQL concurrency test) inside the Django container:

```bash
docker compose exec backend pytest
```

Or run directly using manage.py:
```bash
docker compose exec backend python manage.py test
```

### Concurrency Test Verification
The automated concurrency test (`test_booking_concurrency`) simulates multiple parallel threads trying to book the final available seat simultaneously on PostgreSQL:
* **Expected Result**: 1 request returns HTTP 201 (Created), 1 request returns HTTP 409 (Conflict). Final active bookings count = 1.

---

## 📄 API Endpoints Overview

### Authentication
* `POST /api/auth/oauth/` - Google OAuth authentication
* `POST /api/auth/oauth/callback/` - OAuth code exchange
* `POST /api/auth/dev-login/` - Dev/Test instant JWT generation
* `POST /api/auth/token/refresh/` - Refresh expired access token

### User Profile
* `GET /api/profile/` - Retrieve current user profile
* `PATCH /api/profile/` - Update profile name/image

### Public Sessions
* `GET /api/sessions/` - List public active sessions
* `GET /api/sessions/<id>/` - Retrieve session details

### Creator Dashboard APIs
* `GET /api/creator/sessions/` - List creator's owned sessions with booking counts
* `POST /api/creator/sessions/` - Create a new session
* `PATCH /api/creator/sessions/<id>/` - Edit owned session
* `DELETE /api/creator/sessions/<id>/` - Delete owned session

### Booking Operations
* `POST /api/sessions/<id>/book/` - Book session (concurrency protected)
* `GET /api/bookings/` - List user's bookings
* `GET /api/bookings/active/` - List user's active bookings
* `GET /api/bookings/past/` - List user's past bookings
* `POST /api/bookings/<id>/cancel/` - Cancel an active booking

---

## 📝 Design Decisions & Debugging Documentation

Detailed engineering decisions and real debugging logs are documented in dedicated files:
* [`DECISIONS.md`](./DECISIONS.md) - Contains 5 detailed technical decisions (locking mechanisms, DB constraints, framework choices).
* [`DEBUGGING.md`](./DEBUGGING.md) - Documents real issue symptoms, root causes, fixes, and verification steps.
* [`PROMPT_LOG.md`](./PROMPT_LOG.md) - AI prompts, engineering judgment, and concrete AI corrections.

---

## 🔮 Known Limitations & Future Improvements

1. **Email / Calendar Notifications**: In a production environment, successful bookings could trigger calendar invites (.ics) and automated email reminders via Celery + Redis.
2. **Payment Gateway Integration**: Integration with Stripe for paid creator sessions.
3. **WebSockets for Real-time Capacity Updates**: WebSockets (Django Channels) could push real-time remaining seat updates to the React frontend.
