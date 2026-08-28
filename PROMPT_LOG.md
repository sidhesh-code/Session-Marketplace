# Prompt Log & Engineering Judgment

This document logs material AI assistance prompts, engineering decisions, and specific corrections made during the development of the Sessions Marketplace.

---

## Prompt 1

### Tool / Model
Google DeepMind Antigravity / Gemini 3.7 Sonnet

### Prompt
"Design a concurrency-safe booking system for a Sessions Marketplace where session capacity cannot be exceeded and users cannot duplicate active bookings."

### What I used
The suggestion to use Django's `transaction.atomic()` context manager and DRF custom permission classes for role-based authorization.

### What I changed
Explicitly added `.select_for_update()` to the `Session` queryset inside the atomic transaction to enforce row-level locking at the PostgreSQL level.

### What I rejected
Initial suggestion to perform application-level `if session.bookings.count() < session.capacity:` checks without pessimistic row locking.

### How I verified it
Ran concurrent multi-threaded booking test script against PostgreSQL and verified that simultaneous requests result in exactly 1 success (HTTP 201) and 1 failure (HTTP 409).

---

## Prompt 2

### Tool / Model
Google DeepMind Antigravity / Gemini 3.7 Sonnet

### Prompt
"Create frontend routing and state management for user and creator roles with OAuth authentication."

### What I used
React Context API structure for holding auth state (`AuthContext`) and Axios interceptors for handling Bearer tokens and automatic refresh.

### What I changed
Added strict role-based route guards (`ProtectedRoute` and `CreatorRoute`) on the frontend, while retaining mandatory server-side DRF permission checks on all backend endpoints.

### What I rejected
Relying on client-side state alone to hide UI elements for security.

### How I verified it
Attempted direct API requests to Creator endpoints using a `USER` role JWT token and verified the backend returned `403 Forbidden`.

---

# What AI Got Wrong / What I Corrected

## Correction 1: Relying on Application-Level Capacity Checks for Booking

* **What AI Got Wrong**: The initial booking snippet suggested checking available seats via `session.bookings.filter(status='ACTIVE').count() < session.capacity` without acquiring a database lock on the `Session` row.
* **Why it was wrong**: Under concurrent traffic (e.g. two users booking the last remaining seat simultaneously), both database queries execute concurrently before either transaction commits. Both observe `active_count < capacity` and both insert active bookings, causing oversubscription (`active_bookings = 2`, `capacity = 1`).
* **Correction**: Replaced the plain read query with `Session.objects.select_for_update().get(pk=session_id)` wrapped inside `transaction.atomic()`. This forces PostgreSQL to place an exclusive write lock on the session row, serializing capacity evaluation.
* **Verification**: Created an automated multi-threaded Pytest test case targeting PostgreSQL with 2 concurrent requests for a capacity=1 session. Verified that 1 request succeeds (201 Created) and 1 request fails with 409 Conflict.

---

## Correction 2: Unconditional Duplicate Booking Checks via Table-wide Unique Constraint

* **What AI Got Wrong**: The AI initially suggested adding a standard Django ORM `unique_together = ('user', 'session')` on the `Booking` model to prevent duplicate bookings.
* **Why it was wrong**: A standard unique constraint on `('user', 'session')` prevents a user from EVER booking a session again if they previously booked and subsequently cancelled their booking (`status='CANCELLED'`). A cancelled booking still exists in the database for history/audit purposes, so any future booking attempt by the same user would trigger a DB unique violation.
* **Correction**: Replaced `unique_together` with a PostgreSQL partial unique index: `models.UniqueConstraint(fields=['user', 'session'], condition=models.Q(status='ACTIVE'), name='unique_active_booking_per_user_session')`. This enforces uniqueness ONLY for active bookings.
* **Verification**: Created a test case where a user books a session, cancels the booking (status becomes CANCELLED), and then re-books the same session. Verified that re-booking succeeds cleanly without database constraint errors, while booking twice concurrently returns 409 Conflict.

---

## Prompt 3 (Senior Code Review & QA Audit)

### Tool / Model
Google DeepMind Antigravity / Gemini 3.7 Sonnet

### Prompt
"Perform a complete audit of the CURRENT implementation against every requirement from the original assignment. Inspect code, Docker configuration, database models, APIs, frontend, tests, and documentation. Verify concurrency, authorization, secrets, and database constraints. Fix high-priority issues."

### What I used
Automated repository scan, git log secret inspection, and full backend Django DRF test execution suite.

### What I changed
1. Enforced `IsUserRole` permission class across booking API views in `backend/bookings/views.py` so `CREATOR` accounts receive HTTP 403 Forbidden when attempting to book sessions.
2. Added `test_creator_cannot_book_session` to `backend/bookings/tests.py`.
3. Added `test_invalid_jwt_token_returns_401` to `backend/accounts/tests.py`.

### What I rejected
Rejected making large architecture refactors or rewriting the codebase since all 32 requirement criteria were structurally intact and passed verification.

### How I verified it
Ran all 14 Django DRF unit and authorization tests across `accounts`, `sessions_app`, and `bookings` apps. Verified zero secrets committed in git history.

---

## Prompt 4 (Public Catalog Investigation & Demo Data Seed Command)

### Tool / Model
Google DeepMind Antigravity / Gemini 3.6 Flash (High)

### Prompt
"Investigate public catalog flow. Ensure catalog is publicly accessible without auth, fetches available sessions from REST API, session detail opens on click, and authentication is only required for protected actions. Determine why catalog is empty, create seed demo data command, verify Nginx routing, test backend tests, frontend production build, and commit changes."

### What I used
API response testing (`GET /api/sessions/`), PostgreSQL ORM inspection, Django custom management command structure.

### What I changed
1. Created `backend/sessions_app/management/commands/seed_demo_data.py` to seed sample creator/user accounts and 3 mentorship sessions.
2. Updated `backend/entrypoint.sh` to automatically run `python manage.py seed_demo_data` on startup if DB is empty.

### What I rejected
Rejected hardcoding mock data inside frontend React components or weakening API authentication/permissions.

### How I verified it
1. Verified `GET http://localhost:8080/api/sessions/` returns HTTP 200 with 3 demo sessions.
2. Verified `GET http://localhost:8080/api/sessions/1/` returns HTTP 200 with full session detail.
3. Verified `GET http://localhost:8080/` renders React catalog UI.
4. Executed `npm run build` in `frontend/` (0 errors).
5. Executed 14-test backend test suite against PostgreSQL (100% pass rate).

---

## Prompt 5 (Google OAuth Error 401 Investigation & Error Surfacing)

### Tool / Model
Google DeepMind Antigravity / Gemini 3.6 Flash (High)

### Prompt
"Investigate Google OAuth Error 401 invalid_client ('The OAuth client was not found'). Inspect frontend & backend OAuth configs, Django settings, environment variables, Google OAuth client ID, and redirect URI. Verify backend code exchange, JWT token issuance, protected endpoints, and existing booking functionality. Surface OAuth cancellation/failure gracefully in UI."

### What I used
Django settings inspection, OAuth URL parameter verification, frontend React error state handling, DRF unit test suite.

### What I changed
1. Added backend credential validation in `OAuthLoginUrlView` (`backend/accounts/views.py`) to return a clear 400 Bad Request error if `GOOGLE_CLIENT_ID` is missing/placeholder.
2. Added `test_oauth_login_url_endpoint` to `backend/accounts/tests.py`.
3. Verified frontend cancellation and failure handling (`LoginPage.tsx` & `OAuthCallbackPage.tsx`).

### What I rejected
Rejected replacing OAuth with password authentication, bypassing Google authentication, or hardcoding credentials into source files.

### How I verified it
1. Verified `GET http://localhost:8080/api/auth/oauth/` returns HTTP 400 with actionable configuration instructions when placeholder credentials are used.
2. Verified OAuth cancellation (`error=access_denied`) displays "Login was cancelled." in UI.
3. Executed 15-test backend test suite against PostgreSQL (100% pass rate).
4. Executed `npm run build` in `frontend/` (0 errors).

---

## Prompt 6 (End-to-End Production Hardening, Concurrency & Security Audits — Steps 2–9)

### Tool / Model
Google DeepMind Antigravity / Gemini 3.7 Sonnet

### Prompt
"Perform a complete 9-step audit covering role system synchronization, authorization & IDOR edge cases, multi-threaded PostgreSQL booking race conditions, JWT refresh/expiration lifecycle, session/booking business rules, and frontend end-to-end integration."

### What I used
1. Django REST Framework `IsCreator`, `IsUserRole`, `IsSessionOwner` permission classes and `select_for_update()` row-level locks.
2. Concurrent `ThreadPoolExecutor` test harness using separate database connections to test high-volume simultaneous booking attempts.
3. Comprehensive DRF and JWT test suite expansion covering anonymous access denials, identity spoofing, duplicate booking rejections, seat release on cancellation, and session cascade deletions.

### What I changed
1. Synchronized the frontend role selector (`USER` / `CREATOR`) with backend Google OAuth registration and token issuance in `OAuthCallbackView`.
2. Expanded backend test suite from 15 to 45 passing tests across `accounts`, `sessions_app`, and `bookings`.
3. Verified clean frontend production builds (`tsc && vite build`) and updated `README.md` with complete architecture, API tables, and testing documentation.

### What I rejected
Rejected introducing unnecessary third-party packages, AI agents, LLM wrappers, or modifying the approved visual design.

### How I verified it
1. Executed `docker compose exec -T backend pytest` -> **45 passed in 8.56s (100% pass rate)**.
2. Executed `docker compose build --no-cache frontend` -> **0 TypeScript errors, 0 warnings**.
3. Verified all 4 Docker containers (`sessions_backend`, `sessions_frontend`, `sessions_nginx`, `sessions_postgres`) running and healthy.

