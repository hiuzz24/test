"""Todo tests."""

from unittest.mock import MagicMock

import pytest
from httpx import AsyncClient


async def get_auth_token(client: AsyncClient, email: str = "todo@example.com") -> str:
    """Helper to register and get auth token."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    return response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def create_todo_for_user(
    client: AsyncClient,
    token: str,
    title: str = "Private Todo",
    description: str | None = "Private description",
) -> dict:
    response = await client.post(
        "/api/v1/todos",
        json={"title": title, "description": description},
        headers=auth_headers(token),
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_create_todo(client: AsyncClient):
    """Test creating a new todo."""
    token = await get_auth_token(client, "create@example.com")

    response = await client.post(
        "/api/v1/todos",
        json={"title": "Test Todo", "description": "A test todo item"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Todo"
    assert data["description"] == "A test todo item"
    assert data["completed"] is False


@pytest.mark.asyncio
async def test_get_todos(client: AsyncClient):
    """Test getting todo list."""
    token = await get_auth_token(client, "list@example.com")

    # Create a todo first
    await client.post(
        "/api/v1/todos",
        json={"title": "List Todo"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Get todos
    response = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_update_todo(client: AsyncClient):
    """Test updating a todo."""
    token = await get_auth_token(client, "update@example.com")

    # Create a todo
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Update Me"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]

    # Update it
    response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Updated Title", "completed": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"


@pytest.mark.asyncio
async def test_delete_todo(client: AsyncClient):
    """Test deleting a todo."""
    token = await get_auth_token(client, "delete@example.com")

    # Create a todo
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Delete Me"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]

    # Delete it
    response = await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_get_single_todo(client: AsyncClient):
    """Test getting a single todo by ID."""
    token = await get_auth_token(client, "single@example.com")

    # Create a todo
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Single Todo", "description": "Get me"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]

    # Get it
    response = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Single Todo"


@pytest.mark.parametrize(
    ("method", "payload"),
    [
        ("GET", None),
        ("PUT", {"title": "Unauthorized update"}),
        ("DELETE", None),
    ],
)
@pytest.mark.asyncio
async def test_user_cannot_access_another_users_todo(
    client: AsyncClient,
    method: str,
    payload: dict | None,
):
    """A todo must be readable and mutable only by its owner."""
    user_a_token = await get_auth_token(client, "owner-boundary-a@example.com")
    user_b_token = await get_auth_token(client, "owner-boundary-b@example.com")
    user_b_todo = await create_todo_for_user(client, user_b_token)
    request_kwargs = {"json": payload} if payload is not None else {}

    response = await client.request(
        method,
        f"/api/v1/todos/{user_b_todo['id']}",
        headers=auth_headers(user_a_token),
        **request_kwargs,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_completed_can_toggle_from_true_back_to_false(client: AsyncClient):
    """False is a meaningful update value and must be persisted."""
    token = await get_auth_token(client, "toggle@example.com")
    todo = await create_todo_for_user(client, token)

    completed_response = await client.put(
        f"/api/v1/todos/{todo['id']}",
        json={"completed": True},
        headers=auth_headers(token),
    )
    active_response = await client.put(
        f"/api/v1/todos/{todo['id']}",
        json={"completed": False},
        headers=auth_headers(token),
    )
    persisted_response = await client.get(
        f"/api/v1/todos/{todo['id']}",
        headers=auth_headers(token),
    )

    assert completed_response.json()["completed"] is True
    assert active_response.json()["completed"] is False
    assert persisted_response.json()["completed"] is False


@pytest.mark.parametrize(
    ("update_payload", "expected_title", "expected_completed"),
    [
        ({"title": "Renamed Todo"}, "Renamed Todo", False),
        ({"completed": True}, "Original Todo", True),
    ],
)
@pytest.mark.asyncio
async def test_partial_update_preserves_omitted_fields(
    client: AsyncClient,
    update_payload: dict,
    expected_title: str,
    expected_completed: bool,
):
    """Updating one field must not erase fields omitted from the request."""
    token = await get_auth_token(client, "partial-update@example.com")
    todo = await create_todo_for_user(
        client,
        token,
        title="Original Todo",
        description="Keep this description",
    )

    response = await client.put(
        f"/api/v1/todos/{todo['id']}",
        json=update_payload,
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["title"] == expected_title
    assert response.json()["description"] == "Keep this description"
    assert response.json()["completed"] is expected_completed


@pytest.mark.asyncio
async def test_todo_cache_keys_are_scoped_by_user_and_pagination(
    client: AsyncClient,
    redis_mock: MagicMock,
):
    """Cached list responses must not be shared across users or pages."""
    user_a_token = await get_auth_token(client, "cache-key-a@example.com")
    user_b_token = await get_auth_token(client, "cache-key-b@example.com")

    await client.get(
        "/api/v1/todos?page=1&size=10",
        headers=auth_headers(user_a_token),
    )
    await client.get(
        "/api/v1/todos?page=1&size=10",
        headers=auth_headers(user_b_token),
    )
    await client.get(
        "/api/v1/todos?page=2&size=5",
        headers=auth_headers(user_a_token),
    )

    cache_keys = [call.args[0] for call in redis_mock.set.await_args_list]
    assert len(cache_keys) == 3
    assert len(set(cache_keys)) == 3
    assert all(key.startswith("todos:") for key in cache_keys)


@pytest.mark.asyncio
async def test_mutations_invalidate_authenticated_users_todo_cache(
    client: AsyncClient,
    redis_mock: MagicMock,
):
    """Create, update, and delete must evict every cached list for the owner."""
    token = await get_auth_token(client, "cache-invalidation@example.com")
    current_user = await client.get(
        "/api/v1/auth/me",
        headers=auth_headers(token),
    )
    expected_pattern = f"todos:{current_user.json()['id']}:*"

    todo = await create_todo_for_user(client, token)
    redis_mock.delete_pattern.assert_awaited_once_with(expected_pattern)

    redis_mock.delete_pattern.reset_mock()
    update_response = await client.put(
        f"/api/v1/todos/{todo['id']}",
        json={"title": "Updated Todo"},
        headers=auth_headers(token),
    )
    assert update_response.status_code == 200
    redis_mock.delete_pattern.assert_awaited_once_with(expected_pattern)

    redis_mock.delete_pattern.reset_mock()
    delete_response = await client.delete(
        f"/api/v1/todos/{todo['id']}",
        headers=auth_headers(token),
    )
    assert delete_response.status_code == 204
    redis_mock.delete_pattern.assert_awaited_once_with(expected_pattern)
