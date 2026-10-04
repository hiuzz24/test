# Manual Test Plan: Authentication & Authorization

## 1. Scope & Objective

Manually verify 12 authentication, todo ownership, and session isolation scenarios,
covering Tier 1 regressions and DEF-MANUAL-01. Following the
[template](templates/TEST_PLAN_TEMPLATE.md) and [README §2C](README.md#2c-manual-test-plan),
each case includes preconditions, steps, expected/actual results, priority, and
severity. Section headings identify the module.

**Results: 12 Pass / 0 Fail / 0 Blocked / 0 Not Run.**
11 cases retain their earlier manual results; only TC-AUTH-04 was retested after
the login fix.

## 2. Test Environment & Prerequisites

| Item | Configuration |
|---|---|
| URLs | Frontend `http://localhost:3000`; backend `http://localhost:8000`; Swagger `/docs`. API endpoints below use the `/api/v1` prefix. |
| Stack | Docker Compose: frontend, backend, PostgreSQL, Redis. |
| Test data | Dedicated accounts A/B; A owns todo `X` with a unique title/description. Credentials and tokens are not recorded. |
| Authorization setup | Before each cross-user GET/PUT/DELETE: A GETs X → 200; record the title/description/completed baseline. After switching Bearer tokens, call `/auth/me` to confirm identity. |
| Execution | 4 October 2026: direct UI/Swagger testing; TC-AUTH-07 and TC-AUTHZ-01 include additional screenshots and manual verification confirmations. |
| Browsers | Codex In-app Browser; Brave regular/private windows. Versions were not recorded; two tabs in the same profile are not independent sessions. |
| Retest | TC-AUTH-04 after `docker compose up -d --build --no-deps backend`. |

Wait for API/list loading to finish; inspect **Server response** in Swagger.
TC-AUTH-01–03 use separate UI and Swagger requests; Swagger responses are not
captures of UI requests. Expected statuses follow the auth/todo handlers; the
generic login failure status of 401 follows the template's security objective.

## 3. Test Cases Matrix

Priority (P0/P1/P2: highest to lowest urgency) and severity
(Critical/High/Medium/Low: impact if the behavior fails) are independent.
Pass = matches expected; Fail = differs; Blocked = started but cannot finish;
Not Run = not executed.

### Authentication

| TC ID | Scenario | Preconditions | Steps | Expected | Actual | Priority / Severity | Status |
|---|---|---|---|---|---|---|---|
| TC-AUTH-01 | Register a new account | A's email is unused. | Enter email, password, and confirmation at `/register`; select Create Account; wait for the dashboard. Verify registration through Swagger. | 201; dashboard identifies A. | UI opens `/` with A's identity; a separate new registration through Swagger returns 201 and tokens. | P0 / High | Pass |
| TC-AUTH-02 | Duplicate email | A exists; logged out. | Register A's email again through UI and Swagger. | 400 `Email already registered`; UI shows the error; no new session. | UI shows the expected error without a new session; Swagger returns the expected 400/detail. | P1 / Medium | Pass |
| TC-AUTH-03 | Valid logout/login | A is logged in; test password is known. | Logout → Sign In as A; check the dashboard and login/logout through Swagger. | Logout/login 200; dashboard identifies A. | UI returns to `/login`; signing in restores A and the existing todo. Swagger: login 200, logout 200 `Successfully logged out`. | P0 / High | Pass |
| TC-AUTH-04 | Login failure does not reveal email existence | A exists; another email is unregistered. | Submit A with a wrong password, then the unregistered email with the same wrong password; compare status/body and UI messages. | Both return 401 `Invalid email or password`; no tokens; UI shows the generic error. | Swagger: identical 401/body for both failures; valid login 200. After the frontend fix and rebuild, manual UI checks show `Invalid email or password` for both; form values remain. | P1 / High | Pass |
| TC-AUTH-05 | Tampered JWT signature | A's access token is unexpired; the original returns 200 from `/auth/me`. | Preserve header/payload; replace the first signature character with a different base64url character. Authorize the modified token → GET `/auth/me`; remove the invalid Bearer token. | 401 `Invalid authentication token`; no user data. | Original token: 200 identifying A. Modified token: expected 401/detail, no user data. | P0 / High | Pass |
| TC-AUTH-06 | Refresh token used as access token | A has an unexpired refresh token. | Replace Bearer with the refresh token → GET `/auth/me`; remove Bearer after testing. | 401 `Invalid authentication token`; no user data. | Swagger returns the expected 401/detail without user data. | P0 / High | Pass |
| TC-AUTH-07 | Logout clears tokens and cached UI data | A owns X; B exists; DevTools Application/Network open. | 1. Confirm A's email/X and `access_token`, `refresh_token` in frontend Local Storage.<br>2. Logout; verify both keys disappear; use Back/open `/`.<br>3. Login A → logout → login B in the same tab without F5, URL navigation, or closing the tab; inspect new requests and UI. | Both keys removed; protected route returns to login without A's data; new `/auth/me`, `/todos` requests return 200; UI identifies B without X. | Confirmed Back returns to login, both keys are removed, and accounts switch without F5. Network screenshots: logout/login 200, new `/me` and `/todos` 200; UI identifies B without X. | P0 / High | Pass |

### Authorization

| TC ID | Scenario | Preconditions | Steps | Expected | Actual | Priority / Severity | Status |
|---|---|---|---|---|---|---|---|
| TC-AUTHZ-01 | List isolation across sessions | A owns X; B uses an independent private window. | A confirms X; B logs in and waits for list 200; inspect UI/response and relevant pages if paginated. | B's list excludes X's ID/title; an empty list is not required. | A's X confirmed. Private-window screenshot identifies B with `items: [], total: 0`; manual verification confirms HTTP 200 and no X. | P0 / Critical | Pass |
| TC-AUTHZ-02 | B cannot read X | A GET X returns 200; B has a valid Bearer token. | B GETs `/todos/{X}`. | 404 `Todo not found`; no content disclosed. | Swagger returns the expected 404/detail without X's data. | P0 / Critical | Pass |
| TC-AUTHZ-03 | B cannot update X | X exists; baseline recorded; B has a valid Bearer token. | B PUTs `/todos/{X}` with `{"title":"Unauthorized change"}`; A GETs again and checks UI. | PUT 404 `Todo not found`; A GET 200; data unchanged. | Expected 404/detail; A GET 200; title/description/completed match baseline; UI retains the original todo. | P0 / Critical | Pass |
| TC-AUTHZ-04 | B cannot delete X | A GET X returns 200; B has a valid Bearer token. | B DELETEs `/todos/{X}`; A GETs again and reloads UI. | DELETE 404 `Todo not found`; A GET 200; X still exists. | Expected 404/detail; A GET 200; X remains visible after UI reload. | P0 / Critical | Pass |
| TC-AUTHZ-05 | Switch A → B in the same tab | A is logged in and sees X; B exists; Network open. | Logout A → login B through the form in the same tab, without F5/URL navigation; observe the transition and loaded list. | UI identifies B without A's identity/todos; no F5 needed. | UI identifies B and shows `No todos yet`; Swagger returns B's list with 200 and no X. | P0 / Critical | Pass |

## 4. Defect Tracking & Known Limitations

### DEF-MANUAL-01 — Login reveals email existence

TC-AUTH-04 · **P1 / High · Fixed / Retest Passed (4 October 2026)**

| Stage | Evidence / Change |
|---|---|
| Fail | Swagger: wrong password → 401 `Incorrect password`; unknown email → 404 `User with this email not found`. Only the unknown-email message was observed in the UI. |
| Fix | `backend/app/api/v1/auth.py::login`: both failure branches return 401 `Invalid email or password`. |
| Retest | Swagger against the rebuilt backend: valid login 200; both failures return identical 401/body without tokens. Original expected result retained. |

Additional UI issue: failed login was confirmed to show no toast because the
401 interceptor reloaded the page. Login/register are now excluded from the
expired-session redirect flow. Manual checks after the frontend rebuild show
the generic error toast for both invalid-login scenarios and retain form values.

Logout regression: previously, `/todos` returned 403 after logout. The todo query
now requires a token and uses AbortSignal. E2E recorded no todo request without
Authorization during the transition. The post-fix manual Network screenshot
shows only `logout` 200, with no `/todos` request or 403 within the captured log
interval (Keep log enabled).

### Known Limitations

- The full 12-case manual suite has not been rerun on the new images; TC-AUTH-04 has been retested through API and UI.
- Cache verification covers token cleanup and UI behavior, not inspection of the entire in-memory React Query cache.
- Login timing differences and email enumeration through registration have not been assessed (duplicate registration still returns 400 by contract).
- Test data remains in the development database; no database reset or deletion of existing data was performed.
