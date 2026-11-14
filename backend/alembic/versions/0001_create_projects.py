"""create projects table

Revision ID: 0001
Revises:
Create Date: 2026-09-23
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

json_type = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("calculator_version", sa.String(20), nullable=False),
        sa.Column("inputs", json_type, nullable=False),
        sa.Column("results", json_type, nullable=False),
        sa.Column("warnings", json_type, nullable=False),
    )
    op.create_index("ix_projects_updated_at", "projects", ["updated_at"])


def downgrade() -> None:
    op.drop_index("ix_projects_updated_at", table_name="projects")
    op.drop_table("projects")
