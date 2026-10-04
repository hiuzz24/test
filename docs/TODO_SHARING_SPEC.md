# Technical Specification: Todo List Sharing

## 1. Overview & Objective

**Status:** proposed design only; no sharing feature is implemented by this document.

Allow a registered owner to collaborate on their existing todo list without exposing
other users' private data. Each account owns exactly one logical list. A grant covers
all current and future todos in that list. Target roles are owner, editor and viewer.

## 2. User Stories & Acceptance Criteria

### US-1: Grant access

As an owner, I want to share my list with an existing account so we can collaborate.

- A valid viewer/editor grant returns 201 and becomes usable after commit, without acceptance.
- Only the owner can list, create, change or revoke grants; collaborators cannot re-share.
- Self-sharing returns 400; duplicate grants return 409 without changing the existing role.
- Unknown recipient returns 404; malformed email/role returns 422. Recipient lookup is
  authenticated and rate-limited; its account-existence disclosure is an explicit product tradeoff.

### US-2: Read a shared list

As a viewer, I want to read shared todos without modifying them.

- A grant exposes only the specified owner's list, including later additions.
- Both list and individual-todo reads check authorization before serving cached data.
- Viewers' write attempts return 403 with no changes; outsiders receive 404.
- Pagination, total count and deterministic ordering are documented in the API below.

### US-3: Collaborate safely

As an editor, I want to create, update, complete and delete todos.

- Created todos belong to the list owner, not the acting editor.
- Partial updates preserve omitted fields; false is stored and explicit null clears description.
- Concurrent changes using the same version allow one successful update; stale versions return 409.
- Editors cannot change ownership, permissions or server-managed timestamps.

### US-4: Change or revoke access

As an owner, I want to change a role or revoke a grant at any time.

- Role changes require the current grant version and return the incremented version.
- Successful revocation returns 204 only after commit. New requests after that response cannot
  use the removed grant, even if Redis contains stale data or is unavailable.
- If edit obtains the list lock first, it may commit before revoke; revoke then completes.
  If revoke commits first, a waiting edit rechecks its grant and fails with 404.
- No write authorized by the removed grant may commit after successful revocation unless
  the owner explicitly issues a new grant.
- Reads authorized before revoke may finish. Previously downloaded data cannot be recalled.

## 3. Scope

**In scope:** one list per owner, existing-account grants, viewer/editor roles, grant management,
shared reads and CRUD, concurrency control, pagination and secure caching.

**Out of scope:** multiple named lists, individual-todo grants, anonymous/public links, invitation
emails or acceptance, ownership transfer, offline synchronization, WebSocket push, and UI design.
Account deletion is not a new API in this release, but any future/admin deletion must obey the
transaction protocol below. Existing personal API payloads remain compatible; sharing requires
future internal service changes, not changes implemented as part of this assessment document.

## 4. Database Design

All new timestamps are `timestamptz NOT NULL DEFAULT now()`; update timestamps are maintained
explicitly by application writes. Versions are `bigint NOT NULL DEFAULT 1 CHECK (version > 0)`.

### New table: `todo_lists`

| Column | Type / constraints | Purpose |
|---|---|---|
| owner_id | uuid PRIMARY KEY, REFERENCES users(id) ON DELETE CASCADE | Stable lock target; one list per account |
| data_version | bigint NOT NULL DEFAULT 1 CHECK (data_version > 0) | Cache generation, incremented on every list/grant mutation |
| created_at | timestamptz NOT NULL DEFAULT now() | Creation time |
| updated_at | timestamptz NOT NULL DEFAULT now() | Last mutation time |

The row exists even for an empty list and survives the removal of the last grant/todo.
Create it in the account-registration transaction. Backfill one row for every existing user
before enabling sharing; verify no missing owners, then attach the todo FK. Do not lazily
create the row during permission checks because that would undermine locking consistency.

### New table: `todo_list_grants`

| Column | Type / constraints |
|---|---|
| owner_id | uuid NOT NULL REFERENCES todo_lists(owner_id) ON DELETE CASCADE |
| recipient_id | uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE |
| role | varchar(6) NOT NULL CHECK (role IN ('viewer', 'editor')) |
| version | bigint NOT NULL DEFAULT 1 CHECK (version > 0) |
| created_at / updated_at | timestamptz NOT NULL DEFAULT now() |

Composite primary key `(owner_id, recipient_id)` also prevents duplicate grants.
`CHECK (owner_id <> recipient_id)` prevents self-sharing. Add an index on
`(recipient_id, owner_id)` for shared-list discovery; do not duplicate the primary-key index.
Owner is implicit, never a grant role. A role change increments `version`.

### Existing tables

- Keep `todos.user_id` as list owner. Replace its FK with a reference to
  `todo_lists(owner_id) ON DELETE CASCADE`; deleting an owner deletes the list, its todos and grants.
- Add `todos.version bigint NOT NULL DEFAULT 1 CHECK (version > 0)`; increment on every edit,
  including writes through the existing personal API. New shared endpoints require it for edit/delete.
- Keep existing todo fields and validation (title 1–200 characters, nullable description,
  boolean completed). Reject unknown input fields on new endpoints.
- The shared list query needs an index with leading `user_id`, followed by the sort columns
  `created_at DESC, id DESC`. Reuse a compatible index if one already exists.
- Recipient deletion removes incoming grants, not the owners' todos. No ownership reassignment.

Backfill/constraint validation is a staged deployment, not an automatic large-table rewrite.
Validate referential integrity before enabling routes. Legacy personal clients need not send
versions; their writes still use the same locks and increment versions, so stale shared writes
are detected. Concurrent legacy writes retain their existing last-write-wins behavior.

## 5. API Contracts & Endpoints

All paths below start with `/api/v1`. All require a valid access token; missing, expired,
tampered or wrong-type tokens return 401 on these proposed endpoints.

| Method | Endpoint | Success | Authorization |
|---|---|---|---|
| GET | `/shared-lists?page=1&size=20` | 200: accessible lists and roles | Authenticated recipient |
| GET | `/lists/{owner_id}/grants?page=1&size=20` | 200: paginated grants | Owner only |
| POST | `/lists/{owner_id}/grants` | 201: grant | Owner only |
| PUT | `/lists/{owner_id}/grants/{recipient_id}` | 200: updated grant | Owner only |
| DELETE | `/lists/{owner_id}/grants/{recipient_id}?version=1` | 204, no body | Owner only |
| GET | `/lists/{owner_id}/todos?page=1&size=20` | 200: paginated todos | Owner/editor/viewer |
| GET | `/lists/{owner_id}/todos/{todo_id}` | 200: todo | Owner/editor/viewer |
| POST | `/lists/{owner_id}/todos` | 201: todo | Owner/editor |
| PUT | `/lists/{owner_id}/todos/{todo_id}` | 200: updated todo | Owner/editor |
| DELETE | `/lists/{owner_id}/todos/{todo_id}?version=1` | 204, no body | Owner/editor |

UUID path parameters; `page >= 1`, `1 <= size <= 100`, version positive integer. Invalid
parameters return 422. Lists/todos use `created_at DESC, id DESC` (lists use owner_id as tie-breaker;
grants use recipient_id). Pagination envelope: `{ "items": [...], "total": 1, "page": 1, "size": 20 }`.
List summaries expose `{owner_id, role, created_at}`; grant items expose
`{owner_id, recipient_id, role, version, created_at, updated_at}`. Todo items retain current response
fields and add `version`; ownership is always derived from the route after authorization.

### Request schemas

```json
{"recipient_email": "collaborator@example.com", "role": "viewer"}
```

Grant creation requires both fields; use existing email normalization rules consistently with
account registration. Do not silently change email case semantics only in the sharing feature.

```json
{"role": "editor", "version": 1}
```

Grant update requires both fields. Concurrent duplicate creation is resolved by the unique
constraint as 409, not an uncaught database error.

```json
{"title": "Shared task", "description": null, "completed": false}
```

Todo creation requires title; description defaults to null and completed to false.

```json
{"version": 2, "completed": false}
```

Todo update requires version and at least one of title/description/completed. Omitted fields are
preserved. Title/completed cannot be null. The server never accepts user_id or timestamps.

### Errors

New endpoints return a stable envelope (including custom validation handling):

```json
{"detail": {"code": "version_conflict", "message": "Resource changed; reload and retry."}}
```

| Status | Code | Conditions |
|---|---|---|
| 400 | self_sharing | Owner is recipient |
| 401 | not_authenticated | Invalid or missing access token |
| 403 | insufficient_permission | Known collaborator lacks required role |
| 404 | resource_not_found | Unknown list/todo/grant, or caller has no list access |
| 404 | recipient_not_found | Owner names an unregistered recipient |
| 409 | duplicate_grant / version_conflict | Existing grant or stale version |
| 422 | validation_error | Invalid fields/path/query; sanitized field errors may be included |
| 429 | rate_limited | Authenticated recipient-lookup rate limit exceeded |
| 503 | temporarily_unavailable | Database unavailable or bounded lock/retry budget exhausted |

Do not expose SQL, credentials, other users' todo contents or tokens in errors/logs. Authorize
before reporting version/resource details. Repeated DELETE of an absent grant returns 404.
Unauthorized attempts must not change data, versions or cache generations.

## 6. Business Logic & Security Considerations

| Operation | Owner | Editor | Viewer | Outsider |
|---|---|---|---|---|
| Read list/todo | Allow | Allow | Allow | 404 |
| Create/edit/delete todo | Allow | Allow | 403 | 404 |
| Manage/list grants | Allow | 403 | 403 | 404 |

### Transaction and lock protocol

Use PostgreSQL READ COMMITTED. All mutations affecting a list (personal API writes included)
must lock `todo_lists` first using `SELECT ... FOR UPDATE`, then check authorization again in a
new statement after acquiring the lock, then lock/read the grant or todo, validate its version,
mutate it, increment data_version and commit. No cached permission decision may authorize a write.
Check todo ownership in addition to its ID. All locks remain held until commit/rollback.

If edit locks first, revoke waits until edit commits; revoke then deletes the grant and commits.
If revoke locks first, edit waits and its subsequent READ COMMITTED statement observes the
deleted grant and rejects the edit. Role downgrade uses the identical protocol. Returning a
success response before commit is forbidden. All write paths, jobs and administrative tools must
follow the protocol; a bypass would invalidate the guarantee.

Acquire multiple list locks in ascending owner UUID order, then child locks in stable primary-key
order. To prevent account deletion racing with new incoming grants, grant creation and account
deletion additionally acquire account-row `FOR UPDATE` locks in ascending user UUID order BEFORE
any list locks. Other list writes must not acquire account write locks after list locks.
Deletion holds the account lock, discovers all owned/received lists, locks those lists in order,
increments surviving lists' generations, then deletes the account and cascades in one transaction.
Do not issue raw user deletes outside this protocol. Database FK integrity remains a final guard.

Set a finite lock timeout (initial target 2 seconds). On deadlock/lock timeout, roll back; retry
only a definitely aborted transaction at most twice with jitter, then return 503. Do not retry an
ambiguous commit or transparently replay a successful POST. Clients reload after version conflict.

**Tradeoff:** writes within one list are serialized, including owner writes and grant changes.
Large collaborative lists may experience contention. Keep transactions short, perform no Redis,
email or other network calls while holding locks, and monitor lock waits/timeouts before choosing
more complex concurrency strategies. Different owners' ordinary todo edits remain independent.

## 7. Caching & Invalidation Strategy

Key: `shared-todos:{owner_id}:v:{data_version}:page:{page}:size:{size}`, TTL 300 seconds.
Cache only list contents, never authorization or recipient-specific role information.

For each read, fetch current permission and generation from PostgreSQL in a single statement.
Only then consult Redis. A miss reads todos and total from one consistent database snapshot;
associate the cache entry with the generation read in that snapshot. Never store older contents
under a newer generation. If snapshot authorization differs, recheck and reject as appropriate.
This avoids races where a slow reader repopulates the current cache with stale data.

Every committed content/grant mutation increases data_version while holding the list lock.
After commit, invalidate owner-related list entries using SCAN (not KEYS); invalidate any
shared-list discovery cache for affected recipients if such a cache is later introduced.
Initial release does not cache discovery or grants. Versioned keys make old content unreachable
even when deletion fails or an in-flight reader writes an old generation after cleanup.

Redis errors fall back to PostgreSQL; log sanitized invalidation failures and allow old entries
to expire. Database authorization failures fail closed. Do not turn a committed write into an
apparent failed write merely because post-commit cache cleanup failed.

A read authorized before revoke may return its snapshot afterward. Requests beginning after
revoke succeeds must observe the revoked grant and fail, regardless of Redis state. The browser
clears denied shared views on 403/404 and refetches on navigation/focus; no push notification or
guarantee of erasing data already delivered is claimed.
