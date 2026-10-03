### BUG-01 — Expired JWTs are accepted

- **Location:** `backend/app/core/security.py:49-58`, `verify_token`
- **Severity:** High
- **Reason:** JWT decoding explicitly disables expiration verification with
  `verify_exp=False`. A stolen access or refresh token remains usable after its
  intended expiry.
- **Fix Proposal:** Enable expiration verification and test both expired and
  tampered token rejection.

### BUG-02 — Refresh tokens can authenticate as access tokens

- **Location:** `backend/app/api/deps.py:14-49`, `get_current_user`
- **Severity:** High
- **Reason:** The authentication dependency verifies the signature but never
  requires `type == "access"`. A refresh token can therefore be sent as a Bearer
  token to protected endpoints.
- **Fix Proposal:** Make token verification enforce the expected token type.

### BUG-03 — Cross-user todo read, update, and delete (IDOR)

- **Location:** `backend/app/services/todo_service.py:42-44` and
  `backend/app/api/v1/todos.py:88-153`
- **Severity:** Critical
- **Reason:** Todo lookup filters only by todo ID. Any authenticated user who
  obtains another todo ID can read, modify, or delete that todo.
- **Fix Proposal:** Scope every todo lookup by both `todo_id` and the authenticated
  `user_id`, returning 404 for non-owned resources.

### BUG-04 — Redis list cache leaks data between users and pages

- **Location:** `backend/app/api/v1/todos.py:37`, `list_todos`
- **Severity:** Critical
- **Reason:** Every user and every pagination request uses the single cache key
  `todos:list`. A cached response for User A can be returned to User B; page 1 can
  also be returned for page 2.
- **Fix Proposal:** Include user ID, page, and size in the cache key.

### BUG-05 — Completed todos cannot be toggled back to active

- **Location:** `backend/app/api/v1/todos.py:121-124`, `update_existing_todo`
- **Severity:** High
- **Reason:** The assignment is guarded by `if todo_data.completed`, so the valid
  boolean value `false` is skipped.
- **Fix Proposal:** Apply fields based on whether they were supplied, not on their
  truthiness.

### BUG-06 — Partial update erases the description

- **Location:** `backend/app/api/v1/todos.py:121-130`, `update_existing_todo`
- **Severity:** High
- **Reason:** `model_dump()` includes unset optional fields as `None`. A request
  containing only `title` or `completed` therefore overwrites the existing
  description with null. This was reproduced by toggling completion on todos that
  already had descriptions.
- **Fix Proposal:** Use `model_dump(exclude_unset=True)` and update only supplied
  fields.

### BUG-07 — Todo mutations leave stale Redis list data

- **Location:** `backend/app/api/v1/todos.py:77-153`, create/update/delete handlers
- **Severity:** High
- **Reason:** Create, update, and delete never invalidate the cached todo lists.
  Clients may receive stale data for the full five-minute TTL. This was reproduced
  when newly created or updated todos did not appear correctly in the list.
- **Fix Proposal:** Invalidate all cached list variants for the authenticated user
  after every successful mutation.

### BUG-08 — Frontend server-state cache survives user changes

- **Location:** `frontend/src/features/auth/api/auth.ts:20-55` and
  `frontend/src/features/auth/hooks/useAuth.ts:26-32`
- **Severity:** High
- **Reason:** Logout removes tokens but does not clear React Query. A subsequent
  user in the same browser can temporarily receive the previous user's cached
  `currentUser` or todo data. This was reproduced by registering User B after
  viewing User A's list; User A's data remained visible until a full refresh.
- **Fix Proposal:** Clear user-scoped query data on logout, forced 401, login, and
  registration transitions.
