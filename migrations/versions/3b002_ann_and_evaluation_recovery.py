"""Add ANN research index and recoverable evaluation state."""

from alembic import op
import sqlalchemy as sa

revision = "3b002"
down_revision = "2e046fb28692"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "evaluations",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.add_column("evaluations", sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"))
    op.execute("CREATE INDEX ix_chunks_embedding_hnsw ON chunks USING hnsw (embedding vector_cosine_ops)")


def downgrade():
    op.drop_index("ix_chunks_embedding_hnsw", table_name="chunks")
    op.drop_column("evaluations", "attempts")
    op.drop_column("evaluations", "updated_at")
