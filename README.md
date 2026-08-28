# Sessions Marketplace

> **Sessions Marketplace** is a full-stack platform where users can discover, browse, and book live sessions while creators can publish, manage, and track their sessions in real time. It features role-based access control (USER / CREATOR), concurrency-safe seat reservation using PostgreSQL row-level locks, stateless JWT authentication, and Google OAuth 2.0.

---

## Overview
Sessions Marketplace is a production-engineered web platform connecting **Creators** who publish and host interactive mentorship sessions with **Users** who discover and book available seats in real time. The platform features strict role-based access control, concurrency-safe transactional seat reservation using PostgreSQL row-level locks, and stateless JWT authentication integrated with Google OAuth 2.0.

## Motivation
"Build a compact Sessions Marketplace where users authenticate, browse sessions, and book them, while creators create and manage sessions. The assignment tests end-to-end product engineering rather than visual polish."

---

## Key Features

### User Features
* **Catalog Exploration & Filtering**: Search published sessions in real time by title, description, or creator name.
* **Live Seat Availability**: View real-time capacity and remaining seat counts dynamically updated upon reservation or cancellation.
* **Instant Booking**: One-click session booking with instant confirmation.
* **Booking Management**: Separate dashboard views for Active and Past/Cancelled bookings.
* **Self-Service Cancellation**: Cancel active bookings at any time, immediately releasing the seat for other users.
* **Profile Management**: View and update full name and profile avatar.

### Creator Features
* **Session Publishing**: Create live sessions with customized title, agenda description, scheduled start time, duration, and maximum seat capacity.
* **Creator Dashboard**: View all owned sessions alongside live attendee booking metrics (`booked_seats / capacity`).
* **Session Modification**: Edit owned session details, schedules, and capacity limits.
* **Session Deletion**: Delete owned sessions with automatic cascade cleanup of associated booking records.
* **Ownership Isolation**: Object-level permissions prevent creators from modifying or deleting sessions created by other creators.

### Authentication
* **Google OAuth 2.0 Integration**: Standard authorization code exchange flow.
* **Role Selection Synchronization**: Seamless initial role selection (User vs. Creator) preserved and synchronized during authentication.
* **Stateless JWT Tokens**: Issues short-lived access tokens (60 mins) and long-lived rotating refresh tokens (7 days).
* **Automated Silent Refresh**: Frontend Axios interceptor automatically renews expired access tokens transparently without user disruption.
* **Developer Quick Login**: Instant test authentication buttons (`Quick Login (User)` and `Quick Login (Creator)`) for fast local evaluation without external OAuth credentials.

### Booking
* **PostgreSQL Row-Level Locking**: Employs `select_for_update()` within atomic database transactions to eliminate race conditions and overbooking.
* **Capacity Invariants**: Strictly prevents booking when a session has reached maximum capacity (`active_count >= capacity`).
* **Session Expiration Guard**: Automatically forbids booking sessions that have already started.
* **Seat Release on Cancellation**: Cancelling an active booking immediately increments available seats for other attendees.

### Security
* **Server-Side Identity Enforcement**: Authenticated caller (`request.user`) is injected server-side during session creation and booking; client-supplied IDs are completely ignored.
* **Object-Level Authorization (IDOR Protection)**: Custom DRF permission classes ensure users cannot cancel bookings belonging to other users, and creators cannot modify sessions owned by other creators.
* **Role Escalation Prevention**: Profile update serializers restrict editable fields to `name` and `profile_image`, ignoring any client-injected `role` attributes.

### Database / Concurrency
* **PostgreSQL Engine Constraints**: Enforces a partial unique database constraint (`unique_active_booking_per_user_session`) that prevents duplicate active bookings for the same user while allowing re-booking after cancellation.
* **Cascade Cleanup**: Foreign key cascade rules prevent orphaned booking records when sessions are deleted.

---

## Technology Stack

### Frontend
* **Core**: React 18, TypeScript, Vite
* **Routing & State**: React Router v6, React Context API (`AuthProvider`)
* **Styling & UI**: Tailwind CSS, Lucide React Icons
* **HTTP Client**: Axios with dual request & response refresh interceptors

### Backend
* **Framework**: Python 3.11, Django 5.0, Django REST Framework (DRF)
* **Authentication**: `djangorestframework-simplejwt`, Google OAuth 2.0 API client
* **WSGI Application Server**: Gunicorn

### Database
* **Relational Engine**: PostgreSQL 16 (Alpine)

### Infrastructure
* **Containerization**: Docker, Docker Compose
* **Web Server & Reverse Proxy**: Nginx (Alpine)

---

## Architecture

```text
                                  ┌──────────────────────────┐
                                  │   React + TypeScript     │
                                  │      Vite Frontend       │
                                  └─────────────┬────────────┘
                                                │ (Axios + JWT)
                         ┌──────────────────────┴──────────────────────┐
                         ▼                                             ▼
             ┌────────────────────────┐                   ┌────────────────────────┐
             │   Creator Endpoints    │                   │ Public/User Endpoints  │
             │   /api/creator/...     │                   │   /api/sessions/...    │
             │                        │                   │   /api/bookings/...    │
             │  [IsCreator,           │                   │  [IsUserRole,          │
             │   IsSessionOwner]      │                   │   AllowAny]            │
             └───────────┬────────────┘                   └───────────┬────────────┘
                         │                                             │
                         └──────────────────────┬──────────────────────┘
                                                ▼
                                  ┌──────────────────────────┐
                                  │  Django REST Framework   │
                                  │     (Business Logic)     │
                                  └─────────────┬────────────┘
                                                │ (select_for_update)
                                                ▼
                                  ┌──────────────────────────┐
                                  │   PostgreSQL Database    │
                                  │ (Row Locks + Constraints)│
                                  └──────────────────────────┘
```

### Role Separation Architecture
* **`USER`**: Can browse sessions, view details, book sessions, view own bookings, cancel own bookings, and update profile. Cannot access creator endpoints or publish sessions.
* **`CREATOR`**: Can browse sessions, view details, create sessions, edit own sessions, delete own sessions, and view booking metrics. Cannot book sessions.

### Booking Transaction Flow
```text
BEGIN TRANSACTION (transaction.atomic)
  │
  ├── 1. Acquire exclusive row-level lock:
  │      Session.objects.select_for_update().get(pk=session_id)
  │
  ├── 2. Validate session has not started:
  │      timezone.now() < session.start_time
  │
  ├── 3. Validate user does not already have an active booking:
  │      Booking.objects.filter(user=user, session=session, status='ACTIVE').exists() == False
  │
  ├── 4. Re-calculate active booking count under row lock:
  │      active_count = Booking.objects.filter(session=session, status='ACTIVE').count()
  │      Verify: active_count < session.capacity
  │
  ├── 5. Insert active booking record:
  │      Booking.objects.create(user=user, session=session, status='ACTIVE')
  │
COMMIT TRANSACTION (Lock released; real-time capacity updated)
```

---

## Project Structure

```text
Session-Marketplace/
├── docker-compose.yml              # Multi-container orchestration (Nginx, Backend, Frontend, Postgres)
├── .env.example                    # Environment variable template with placeholders
├── README.md                       # Comprehensive project documentation
├── DECISIONS.md                    # Engineering architecture & design decisions
├── DEBUGGING.md                    # Root-cause debugging notes and fixes
│
├── backend/                        # Django REST Framework Backend
│   ├── Dockerfile                  # Python 3.11 slim container definition
│   ├── entrypoint.sh               # DB readiness wait, migration runner, demo seeder
│   ├── requirements.txt            # Python dependencies (Django, DRF, SimpleJWT, etc.)
│   ├── pytest.ini                  # Pytest runner configuration
│   ├── config/                     # Django core settings & routing
│   │   ├── settings.py             # Database, JWT, CORS, OAuth settings
│   │   ├── urls.py                 # Top-level API router
│   │   └── exceptions.py           # Standardized DRF custom exception handler
│   ├── accounts/                   # Authentication & User Profiles App
│   │   ├── models.py               # Custom User model (USER / CREATOR roles)
│   │   ├── views.py                # OAuth code exchange, DevLogin, Profile views
│   │   ├── permissions.py          # IsCreator, IsUserRole, IsSessionOwner
│   │   └── tests.py                # 18 unit tests for auth & OAuth error handling
│   ├── sessions_app/               # Sessions Domain App
│   │   ├── models.py               # Session model with capacity and schedule
│   │   ├── serializers.py          # Dynamic booked_seats and remaining_seats logic
│   │   ├── views.py                # Public catalog and Creator CRUD views
│   │   └── tests.py                # 11 unit tests for creator permissions & isolation
│   └── bookings/                   # Bookings Domain App
│       ├── models.py               # Booking model with partial unique constraint
│       ├── services.py             # Concurrency-safe book_session & cancel_booking
│       ├── views.py                # BookSession, BookingList, CancelBooking views
│       └── tests.py                # 16 unit & multi-threaded concurrency tests
│
├── frontend/                       # React 18 + TypeScript Frontend
│   ├── Dockerfile                  # Multi-stage production build (Node build -> Nginx static)
│   ├── nginx.frontend.conf         # Static SPA routing configuration
│   ├── package.json                # React, TypeScript, Tailwind dependencies
│   ├── vite.config.ts              # Vite bundler configuration
│   └── src/
│       ├── App.tsx                 # Root router and route guards setup
│       ├── types/                  # Shared TypeScript interfaces
│       ├── api/                    # Axios client, auth, sessions, bookings API modules
│       ├── context/                # AuthContext state provider and token manager
│       ├── components/             # Navbar, SessionCard, ProtectedRoute, CreatorRoute
│       └── pages/                  # LoginPage, Catalog, Detail, Bookings, Dashboard, Edit
│
└── nginx/                          # Nginx Reverse Proxy
    ├── Dockerfile                  # Nginx Alpine container definition
    └── nginx.conf                  # Port 8080 proxy routing (/api -> backend, / -> frontend)
```

---

## API Documentation

### Authentication (`/api/auth/`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `GET` | `/api/auth/oauth/url/` | Retrieve Google OAuth consent URL | Public |
| `POST` | `/api/auth/oauth/callback/` | Exchange Google OAuth code for JWT tokens | Public |
| `POST` | `/api/auth/dev-login/` | Issue instant JWT for User or Creator | Public |
| `POST` | `/api/auth/token/refresh/` | Refresh expired access token | Public |

### User Profile (`/api/profile/`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `GET` | `/api/profile/` | Retrieve authenticated user profile | Authenticated |
| `PATCH` | `/api/profile/` | Update user name and profile image | Authenticated |

### Public Sessions (`/api/sessions/`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `GET` | `/api/sessions/` | List all published sessions with live seats | Public |
| `GET` | `/api/sessions/<id>/` | Retrieve session detail and host info | Public |

### Creator Sessions (`/api/creator/sessions/`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `GET` | `/api/creator/sessions/` | List creator's owned sessions with booking counts | `CREATOR` |
| `POST` | `/api/creator/sessions/` | Publish a new session | `CREATOR` |
| `GET` | `/api/creator/sessions/<id>/` | Retrieve owned session detail | `CREATOR` (Owner) |
| `PATCH` | `/api/creator/sessions/<id>/` | Edit owned session details or capacity | `CREATOR` (Owner) |
| `DELETE` | `/api/creator/sessions/<id>/` | Delete owned session and cascade bookings | `CREATOR` (Owner) |

### Bookings (`/api/bookings/` & `/api/sessions/<id>/book/`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/api/sessions/<id>/book/` | Concurrency-safe seat reservation | `USER` |
| `GET` | `/api/bookings/` | List all bookings for authenticated user | `USER` |
| `GET` | `/api/bookings/active/` | List active bookings for authenticated user | `USER` |
| `GET` | `/api/bookings/past/` | List past and cancelled bookings | `USER` |
| `POST` | `/api/bookings/<id>/cancel/` | Cancel an active booking and release seat | `USER` (Owner) |

---

## Authentication Flow

1. **Sign In**: User visits `/login`, selects desired role (`User` or `Creator`), and clicks `"Continue with Google"`.
2. **Consent & Code Exchange**: User authenticates with Google; Google redirects to `/auth/callback?code=...`.
3. **Backend Validation**: `POST /api/auth/oauth/callback/` validates the code, registers or fetches the user in PostgreSQL, applies the chosen role, and returns JWT tokens (`access` and `refresh`).
4. **Token Storage**: React stores JWTs in `localStorage` and initializes the session in `AuthContext`.
5. **Silent Renewal**: When the access token expires (60 mins), Axios response interceptor catches the 401, calls `/api/auth/token/refresh/`, updates the access token, and retries original requests transparently.
6. **Sign Out**: Clicking `"Logout"` removes all tokens from `localStorage`, resets React state, and redirects to `/login`.

---

## Booking Flow

1. **Browse**: User navigates to `/sessions` and clicks on an available session.
2. **Inspection**: The detail page loads live data (`remaining_seats`, `capacity`, `is_started`, host).
3. **Reservation**: User clicks `"Book Session"`. Backend initiates `transaction.atomic()` with `select_for_update()`.
4. **Verification**: Backend ensures session has not started, user has no duplicate active reservation, and capacity remains available.
5. **Confirmation**: Booking row is created with status `ACTIVE`. Frontend displays green confirmation banner with a direct link to `/bookings`.
6. **Cancellation & Release**: User can cancel their booking on `/bookings`. Status updates to `CANCELLED`, and the seat is immediately freed on the marketplace.

---

## Security

* **Role-Based Access Control (RBAC)**: `IsCreator` and `IsUserRole` permissions strictly guard endpoints at the DRF view level.
* **Object-Level Authorization**: `IsSessionOwner` ensures creators can only access and modify their own sessions (returns `403 Forbidden` on unauthorized access).
* **IDOR Protection**: `cancel_booking` queries `Booking.objects.get(pk=id, user=request.user)`. Attempting to cancel another user's booking returns `404 Not Found`.
* **Server-Side Identity**: `creator` and `user` fields are marked read-only in serializers and populated exclusively from `request.user`.
* **Database Engine Constraints**: Partial unique index `unique_active_booking_per_user_session` prevents duplicate active bookings at the database engine level.

---

## Running Locally

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd Session-Marketplace
```

### Step 2: Configure Environment Variables
```bash
cp .env.example .env
```
*(The default `.env` is pre-configured with ready-to-use local parameters for Docker evaluation).*

### Step 3: Build and Run Containers
```bash
docker compose up --build -d
```

### Step 4: Access the Application
* **Web Application (Nginx Proxy)**: [http://localhost:8080](http://localhost:8080)
* **Backend API Base**: [http://localhost:8080/api/](http://localhost:8080/api/)
* **Django Admin**: [http://localhost:8080/admin/](http://localhost:8080/admin/)

---

## Testing

Run the complete backend automated test suite (including unit tests, authorization checks, and multi-threaded PostgreSQL concurrency race-condition tests) inside the Docker container:

```bash
docker compose exec -T backend pytest
```

### Verified Test Result
```text
============================= test session starts ==============================
platform linux -- Python 3.11.16, pytest-9.1.1, pluggy-1.6.0
django: version: 5.0.14, settings: config.settings (from ini)
rootdir: /app
configfile: pytest.ini
plugins: django-4.14.0
collected 45 items

accounts/tests.py ..................                                     [ 40%]
sessions_app/tests.py ...........                                        [ 64%]
bookings/tests.py ................                                       [100%]

======================== 45 passed, 1 warning in 8.52s =========================
```

---

## Production Notes

* **HTTPS Termination**: In production environments (AWS ECS, GCP Cloud Run, DigitalOcean), configure TLS certificates (Let's Encrypt / Certbot) on the Nginx reverse proxy.
* **Production Secrets**: Replace all default passwords and `DJANGO_SECRET_KEY` with cryptographically secure values generated via `secrets.token_urlsafe(50)`.
* **Database Backups**: Schedule automated PostgreSQL WAL backups and daily snapshots.
* **Logging & Observability**: Configure centralized logging (e.g. Sentry, Datadog) for production error tracking.

---

## Future Improvements

1. **Email & Calendar Notifications**: Integration with Celery + Redis to dispatch confirmation emails and `.ics` calendar invites upon booking.
2. **Payment Processing**: Stripe integration for paid creator masterclasses.
3. **WebSockets for Live Seat Counts**: Django Channels integration to broadcast remaining seat counts to connected browsers in real time.
