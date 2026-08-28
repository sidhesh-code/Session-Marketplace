# Debugging Log

This log documents real technical issues, symptoms, root causes, and fixes encountered during the development, testing, and Docker deployment of the Sessions Marketplace application.

---

# Issue 1: Race Condition in Concurrent Booking Test when executed without Database Row Locks

## Symptom
During early concurrency testing with 2 simultaneous threads attempting to book a session with capacity = 1, both requests returned `201 Created`, resulting in 2 active bookings for a session with capacity 1 (`active_bookings = 2`, violating Invariant 1).

## Diagnosis
Inspected the booking service execution logs. Both request threads executed `Booking.objects.filter(session=session, status='ACTIVE').count()` at the exact same millisecond before either thread committed its `Booking.create()` transaction. Both threads read `count = 0`, evaluated `0 < 1` as `True`, and proceeded to insert booking records.

## Root Cause
The initial read query did not lock the `Session` database row. Without pessimistic row locking (`select_for_update()`), PostgreSQL allowed concurrent read transactions to read snapshot data prior to transaction commit.

## Fix
Wrapped the booking verification and creation logic inside `transaction.atomic()` and acquired an exclusive lock on the session row using `.select_for_update()`:

```python
with transaction.atomic():
    session = Session.objects.select_for_update().get(pk=session_id)
    # validate capacity & duplicate booking inside locked block
```

## Verification
Re-ran the automated concurrency test with Pytest and `ThreadPoolExecutor` against PostgreSQL. Thread 1 acquired the row lock, created the booking, and committed. Thread 2 waited on the row lock, re-read `active_count = 1`, failed the capacity check, and received an HTTP `409 Conflict`. Final active bookings count verified exactly equal to `1`.

---

# Issue 2: OAuth JWT Refresh Loop on Frontend Axios Interceptor

## Symptom
When an access token expired on the React frontend, Axios interceptor triggered a refresh request to `/api/auth/token/refresh/`. If the refresh token was also expired or invalid, the interceptor repeatedly retried the refresh endpoint in an infinite loop, freezing the browser.

## Diagnosis
The response interceptor caught the 401 error from `/api/auth/token/refresh/` and tried to send another refresh request using the same broken refresh token because `_retry` flag was not checked for refresh endpoint URLs specifically.

## Root Cause
The Axios interceptor logic checked `!originalRequest._retry`, but did not exclude requests pointing directly to `auth/token/refresh/`.

## Fix
Updated the response interceptor to check if `originalRequest.url.includes('/auth/token/refresh/')`. If a refresh request itself returns HTTP 401, clear local authentication state, wipe tokens from storage, and redirect immediately to `/login`.

## Verification
Simulated expired refresh token scenario in browser subagent / unit tests. Verified that an invalid refresh token immediately logs out the user and redirects to `/login` without extra network requests.

---

# Issue 3: Missing Role Permission Enforcement on Booking API Endpoints

## Symptom
During QA security audit, an authenticated user with the `CREATOR` role sent a `POST` request to `/api/sessions/<id>/book/` and received `201 Created`, successfully booking a session seat.

## Diagnosis
Inspected `backend/bookings/views.py`. `BookSessionView`, `BookingListView`, `ActiveBookingListView`, `PastBookingListView`, and `CancelBookingView` were configured with `permission_classes = [permissions.IsAuthenticated]`.

## Root Cause
`IsAuthenticated` grants access to any authenticated request regardless of role. While `IsUserRole` permission class was defined in `accounts/permissions.py`, it was not applied to the booking API views.

## Fix
Updated `backend/bookings/views.py` to import `IsUserRole` and updated all booking views to set `permission_classes = [IsUserRole]`.

## Verification
Created test case `test_creator_cannot_book_session` in `backend/bookings/tests.py`. Executed Django test suite and verified that a `CREATOR` role receives `403 Forbidden` when attempting to book a session.

---

# Issue 4: Empty Public Session Catalog Due to Unseeded PostgreSQL Database

## Symptom
When navigating to the public Session Catalog at `http://localhost:8080/` or `http://localhost:8080/sessions`, the catalog displayed "No sessions available" and no session cards were present to view session details or evaluate booking flows.

## Diagnosis
1. Tested backend REST API directly: `GET http://localhost:8080/api/sessions/` returned `HTTP 200 OK` with payload `[]` (empty list).
2. Queried PostgreSQL database via Django shell: `User.objects.count() = 1`, `Session.objects.count() = 0`.
3. The database contained 0 published session records. Because no seed command existed in Django, fresh deployments lacked demo sessions for public browsing.

## Root Cause
Lack of an automated database seed command in Django to populate demo mentorship sessions on startup when `Session.objects.count() == 0`.

## Fix
1. Created custom Django management command `backend/sessions_app/management/commands/seed_demo_data.py` to auto-populate sample creator/user accounts and 3 realistic future sessions with capacities (5, 1, 10).
2. Updated `backend/entrypoint.sh` to execute `python manage.py seed_demo_data` automatically following database migration.

## Verification
1. Rebuilt backend container (`docker compose build backend`) and restarted stack (`docker compose up -d`).
2. Verified `GET http://localhost:8080/api/sessions/`: Returned `HTTP 200 OK` with 3 session objects containing creator details, remaining seats, and duration.
3. Verified `GET http://localhost:8080/api/sessions/1/`: Returned `HTTP 200 OK` with complete session details.
4. Executed `npm run build` in `frontend/`: Compiled 1574 modules with 0 errors.
5. Executed containerized test suite: All 14 tests passed against PostgreSQL.

---

# Issue 5: Google OAuth `Error 401: invalid_client` ("The OAuth client was not found")

## Symptom
When clicking "Continue with Google" on the login page and submitting Google credentials, Google Cloud's OAuth server returned `Access blocked: Authorization Error - The OAuth client was not found. Error 401: invalid_client`.

## Diagnosis
1. Inspected `OAuthLoginUrlView` in `backend/accounts/views.py` and `GOOGLE_CLIENT_ID` in `.env` / `docker-compose.yml`.
2. Environment configuration analysis: `.env` and `docker-compose.yml` contain placeholder credentials (`your-google-client-id.apps.googleusercontent.com`).
3. Google OAuth 2.0 flow: When `OAuthLoginUrlView` passed `client_id=your-google-client-id...` in the Google authorization URL (`https://accounts.google.com/o/oauth2/v2/auth`), Google's server looked up the Client ID in Google Cloud Platform. Finding no registered GCP project for that placeholder string, Google threw `Error 401: invalid_client`.

## Root Cause
1. Deployment/Evaluation environments had unconfigured or placeholder `GOOGLE_CLIENT_ID` values in `.env`.
2. Backend lacked validation to detect missing/placeholder OAuth credentials before redirecting users to Google, and frontend needed clear UI error surfacing for unconfigured OAuth or user cancellation.

## Fix
1. Updated `OAuthLoginUrlView` in `backend/accounts/views.py` to validate `settings.GOOGLE_CLIENT_ID`. If credentials are unconfigured or placeholder, the view returns `HTTP 400 Bad Request` with actionable instructions: `"Google OAuth is not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env, or use Quick Login."`
2. Enhanced frontend error handling in `LoginPage.tsx` and `OAuthCallbackPage.tsx` to surface OAuth configuration warnings, network errors, and user consent cancellations (`error=access_denied` -> `"Login was cancelled."`) gracefully in the UI.
3. Documented exact Google Cloud Console setup requirements (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and Authorized Redirect URI `http://localhost:8080/auth/callback`).

## Verification
1. Tested `GET http://localhost:8080/api/auth/oauth/`: Returned `HTTP 400 Bad Request` with structured error message when placeholder is present, preventing opaque Google 401 errors.
2. Verified OAuth cancellation handling: Simulating `access_denied` callback parameter surfaces `"Login was cancelled."` gracefully in the UI.
3. Added unit test `test_oauth_login_url_endpoint` in `backend/accounts/tests.py`. Executed 15-test backend suite (100% pass rate).
4. Executed `npm run build` in `frontend/` (0 errors).
