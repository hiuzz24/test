"""Index owner-scoped todo reads and ordered pagination.

Revision ID: b3180d4e92af
Revises: a0790c76a129
"""

from alembic import op
import sqlalchemy as sa

revision = "b3180d4e92af"
down_revision = "a0790c76a129"
branch_labels = None
depends_on = None

INDEX_NAME = "ix_todos_user_created_id"


def upgrade() -> None:
    # PostgreSQL concurrent DDL cannot run inside Alembic's normal transaction.
    # Do not use IF NOT EXISTS: an invalid or mismatched index needs inspection.
    with op.get_context().autocommit_block():
        op.execute("SET lock_timeout = '5s'")
        try:
            op.create_index(
                INDEX_NAME,
                "todos",
                ["user_id", sa.text("created_at DESC"), sa.text("id DESC")],
                postgresql_concurrently=True,
            )
        finally:
            op.execute("RESET lock_timeout")


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("SET lock_timeout = '5s'")
        try:
            op.drop_index(INDEX_NAME, table_name="todos", postgresql_concurrently=True)
        finally:
            op.execute("RESET lock_timeout")
