# Sessions Marketplace

A full-stack platform where users can discover and book sessions while creators can publish and manage sessions.

---

## Live Application

* **Frontend**: [https://poetic-dream-production-abfb.up.railway.app](https://poetic-dream-production-abfb.up.railway.app/)
* **Backend**: [https://session-marketplace-production.up.railway.app](https://session-marketplace-production.up.railway.app/)
* **Health Check**: [https://session-marketplace-production.up.railway.app/api/health/](https://session-marketplace-production.up.railway.app/api/health/)

## GitHub Repository

* [https://github.com/sidhesh-code/Session-Marketplace](https://github.com/sidhesh-code/Session-Marketplace)

---

## Technology Stack

### Frontend
* React (v18)
* TypeScript
* Vite
* React Router (v6)
* Axios (with automatic JWT refresh interceptors)

### Backend
* Python (3.11)
* Django (5.0)
* Django REST Framework (DRF)
* Simple JWT (token authentication & rotation)

### Database
* PostgreSQL (with pessimistic row-level locking & partial unique constraints)

### Authentication
* Google OAuth 2.0
* JWT (Access & Refresh tokens)

### Deployment
* Railway (Full-stack containerized cloud deployment)

---

## Main Features

* **User registration / login**: Role-based authentication (`USER` / `CREATOR`).
* **Google OAuth login**: Standard Google OAuth 2.0 authorization code exchange.
* **User profiles**: Authenticated profile retrieval and editing.
* **Browse available sessions**: Public catalog with search filtering, scheduled timings, and live seat availability.
* **Session details**: Dynamic remaining seats calculation and creator details.
* **Session booking**: Concurrency-safe seat reservation utilizing PostgreSQL row-level locks (`select_for_update`) within atomic transactions (`transaction.atomic`).
* **My Bookings**: Active and past/cancelled booking dashboards with self-service cancellation and immediate seat release.
* **Creator dashboard**: Real-time attendee metrics and booking counts (`booked_seats / capacity`).
* **Create / manage sessions**: Full CRUD operations for session creators with object-level ownership isolation (`IsSessionOwner`).
* **PostgreSQL persistence**: Relational integrity with partial unique indexes preventing duplicate active bookings.
* **REST API**: Clean RESTful endpoints for all marketplace operations.
* **JWT authentication**: Stateless token authorization with silent token renewal.

---

## Production Architecture

```text
Frontend (Railway)
       ↓ (Axios + JWT)
Django REST API (Railway)
       ↓ (select_for_update / row-level locks)
PostgreSQL (Railway)
```

Google OAuth 2.0 is used for authentication.

---

## Testing

### Backend
* **45 tests passed** (`pytest` test suite covering authentication, role-based authorization, IDOR protection, and multi-threaded concurrency race conditions).

### Frontend
* **Production build successful** (`tsc && vite build` compiled with 0 errors).

---

## Deployment

* **Frontend**: [https://poetic-dream-production-abfb.up.railway.app](https://poetic-dream-production-abfb.up.railway.app/)
* **Backend**: [https://session-marketplace-production.up.railway.app](https://session-marketplace-production.up.railway.app/)
* **Health endpoint**: [https://session-marketplace-production.up.railway.app/api/health/](https://session-marketplace-production.up.railway.app/api/health/)

---

## Security

Never commit:
* `.env` files
* Secrets / API keys
* OAuth client secrets
* `DATABASE_URL`
* Railway credentials

Environment variables are configured securely through the Railway platform dashboard.
