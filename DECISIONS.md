# Architectural & Engineering Decisions

This document records key non-trivial technical decisions made during the design and implementation of the Sessions Marketplace application.

---

# Decision 1: React + Vite vs Next.js for Frontend Architecture

## Problem / Ambiguity
The assignment requires a client-side frontend that renders session catalogs, handles OAuth callbacks, authenticates via JWT, and manages creator dashboard tools. We needed to choose between Vite (React SPA) and Next.js.

## Options considered
1. **Next.js (App Router / Pages Router)**: Server-side rendering (SSR), built-in routing, API routes.
2. **React + Vite**: Pure Client-Side Application (SPA), lightweight build toolchain, fast HMR, explicit separation between static frontend assets and backend API.

## Decision
Selected **React + Vite**.

## Reason
The requirements explicitly state that the frontend is client-side only and caution against introducing unnecessary SSR or Next.js complexity. React + Vite provides lightning-fast startup times, minimal bundle sizes, clear separation of concerns with Django DRF handling all REST API logic, and simplifies deployment via static asset serving through Nginx.

## Trade-off
Initial page load relies on client-side fetching rather than SSR HTML pre-rendering. However, for an authenticated SPA marketplace, CSR with clear loading states provides superior client responsiveness and decoupled container containerization.

---

# Decision 2: PostgreSQL Row-Level Locking (`select_for_update`) for Booking Concurrency

## Problem / Ambiguity
Booking capacity is a critical invariant (`active_bookings <= session.capacity`). Under high concurrency, simultaneous booking requests could read `active_bookings < capacity` at the same instant and both insert active bookings, leading to oversubscription.

## Options considered
1. **Application-level check (`if exists()` / `count() < capacity`)**: Perform validation in Python without DB locks.
2. **Optimistic Locking with version columns**: Add a version column to the Session table and retry on write conflict.
3. **Pessimistic Row-Level Locking (`select_for_update()`) inside PostgreSQL atomic transactions**: Lock the specific `Session` DB row during capacity calculation and booking creation.

## Decision
Selected **Pessimistic Row-Level Locking (`select_for_update()`)**.

## Reason
Pessimistic row locking directly instructs PostgreSQL to place an exclusive write lock on the target Session row (`SELECT ... FOR UPDATE`). Subsequent concurrent transactions attempting to book the same session block until the active transaction commits or rolls back. This guarantees strict serialized evaluation of remaining capacity without race conditions or retry overhead.

## Trade-off
Concurrent requests for the *same* session wait briefly for the row lock to release instead of immediately failing or executing in parallel. Given session booking volume per session, this brief serialization is the industry standard guarantee for exact inventory and ticket booking systems.

---

# Decision 3: PostgreSQL Partial Unique Index for Duplicate Active Bookings

## Problem / Ambiguity
A user must not have duplicate active bookings for the same session. However, if a user cancels a booking, they should be permitted to re-book the session later. Standard `unique_together = ('user', 'session')` would permanently block re-booking after cancellation.

## Options considered
1. **Application-only check**: `Booking.objects.filter(user=user, session=session, status='ACTIVE').exists()`.
2. **Standard UniqueConstraint on `(user, session)`**: Enforces uniqueness across ALL booking statuses (including CANCELLED).
3. **Partial Unique Index (PostgreSQL `UniqueConstraint` with `condition=Q(status='ACTIVE')`)**: Enforces uniqueness ONLY when `status='ACTIVE'`.

## Decision
Selected **Partial Unique Index via Django ORM `UniqueConstraint(fields=['user', 'session'], condition=Q(status='ACTIVE'), name='unique_active_booking_per_user_session')`**.

## Reason
Application-level checks alone are vulnerable to race conditions if two identical requests bypass locking. A DB-level partial unique index ensures PostgreSQL physically rejects duplicate active rows at the storage engine level, while allowing a user with a `CANCELLED` booking to create a new `ACTIVE` booking.

## Trade-off
Requires a database engine that supports partial indexes (PostgreSQL supports this natively, whereas SQLite standard table constraints do not). This aligns with the project requirement to use PostgreSQL exclusively.

---

# Decision 4: Dual-Mode OAuth + Local Developer/Testing Auth Handler

## Problem / Ambiguity
The application must support Google OAuth for authentication, issuing JWT access and refresh tokens. However, automated test suites (pytest/CI) and local development evaluation without active Google Client secrets require an authoritative way to issue authentic JWTs for both `USER` and `CREATOR` roles.

## Options considered
1. **Strict Google OAuth only**: Require valid Google API keys even during automated backend tests.
2. **Mock OAuth backend for testing**: Intercept requests with unittest mocks.
3. **Dedicated Dev/Testing OAuth Callback Endpoint (`/api/auth/dev-login/`) alongside real Google OAuth exchange**: Real Google OAuth standard code exchange flow is supported, while a controlled local development authentication endpoint generates valid JWT tokens for specified test roles when running in dev mode.

## Decision
Implemented **Full Google OAuth 2.0 flow alongside Dev/Test Token Handler**.

## Reason
Allows production deployment to authenticate seamlessly via Google OAuth while ensuring local Docker evaluation, manual QA, and automated Pytest concurrency suites run end-to-end without external third-party API dependencies or flaky internet credentials.

## Trade-off
Must ensure the dev-login endpoint is restricted or disabled when `DJANGO_DEBUG=False` in production environments.

---

# Decision 5: Session Deletion Policy with Active Bookings

## Problem / Ambiguity
When a Creator deletes a Session that already has active user bookings, the system must handle the cascading effect on existing `Booking` records without causing foreign key integrity violations or silent state corruption.

## Options considered
1. **Block deletion if active bookings exist**: Return 409 Conflict if `active_bookings > 0`.
2. **Hard Cascade Delete (`on_delete=models.CASCADE`)**: Automatically delete all booking records when session is deleted.
3. **Soft Cancellation / Mark as CANCELLED before deletion**: Set booking status to CANCELLED and maintain audit history.

## Decision
Selected **Hard Cascade Delete with pre-deletion validation/cancellation logic**.

## Reason
`on_delete=models.CASCADE` on the foreign key ensures database integrity remains clean. When a session is deleted by its authorized creator, linked bookings are removed from active sets, preventing orphan references.

## Trade-off
Users lose historical booking records for deleted sessions unless soft-deletion is implemented. For this marketplace scale, DB cascade guarantees clean schema state.
