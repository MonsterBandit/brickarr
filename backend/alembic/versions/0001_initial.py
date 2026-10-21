"""initial schema (SQLite or MariaDB)

Revision ID: 0001
Revises:
Create Date: 2026-10-21

One migration that runs on both databases (BR.DK.02): enums are stored as
VARCHAR (non-native), and the mysql_* table options are dialect-prefixed, so
SQLite ignores them and only MariaDB applies them.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ITEM_TYPE = sa.Enum("SET", "MINIFIG", "PART", name="catalog_item_type", native_enum=False)
OWNED_ITEM_TYPE = sa.Enum("SET", "MINIFIG", "PART", name="owned_item_type", native_enum=False)
PART_ITEM_TYPE = sa.Enum("PART", "MINIFIG", name="part_item_type", native_enum=False)
OWNED_STATUS = sa.Enum("collecting", "complete", "wanted", "dismantled", name="owned_status", native_enum=False)
OWNED_CONDITION = sa.Enum("new", "used", name="owned_condition", native_enum=False)
PRICE_ITEM_TYPE = sa.Enum("SET", "MINIFIG", "PART", name="price_item_type", native_enum=False)
PRICE_GUIDE = sa.Enum("sold", "stock", name="price_guide_type", native_enum=False)
PRICE_COND = sa.Enum("new", "used", name="price_condition", native_enum=False)
LIGHT_STATUS = sa.Enum("owned", "wanted", name="light_kit_status", native_enum=False)

# SQLite only auto-numbers an INTEGER PRIMARY KEY; MariaDB keeps BIGINT.
BIGINT_PK = sa.BigInteger().with_variant(sa.Integer(), "sqlite")

TABLE_KW = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}


def upgrade() -> None:
    op.create_table(
        "catalog_item",
        sa.Column("item_type", ITEM_TYPE, nullable=False),
        sa.Column("item_no", sa.String(32), nullable=False),
        sa.Column("name", sa.String(512), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("category_name", sa.String(255), nullable=True),
        sa.Column("year_released", sa.SmallInteger(), nullable=True),
        sa.Column("image_url", sa.String(512), nullable=True),
        sa.Column("thumbnail_url", sa.String(512), nullable=True),
        sa.Column("weight_g", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("dim_x_cm", sa.DECIMAL(8, 2), nullable=True),
        sa.Column("dim_y_cm", sa.DECIMAL(8, 2), nullable=True),
        sa.Column("dim_z_cm", sa.DECIMAL(8, 2), nullable=True),
        sa.Column("rebrickable_id", sa.String(32), nullable=True),
        sa.Column("theme", sa.String(128), nullable=True),
        sa.Column("subtheme", sa.String(128), nullable=True),
        sa.Column("rrp", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("launch_date", sa.Date(), nullable=True),
        sa.Column("exit_date", sa.Date(), nullable=True),
        sa.Column("age_min", sa.SmallInteger(), nullable=True),
        sa.Column("age_max", sa.SmallInteger(), nullable=True),
        sa.Column("num_pieces", sa.Integer(), nullable=True),
        sa.Column("num_minifigs", sa.Integer(), nullable=True),
        sa.Column("rating", sa.DECIMAL(3, 2), nullable=True),
        sa.Column("brickset_id", sa.String(32), nullable=True),
        sa.Column("catalog_synced_at", sa.DateTime(), nullable=True),
        sa.Column("brickset_synced_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("item_type", "item_no"),
        **TABLE_KW,
    )

    op.create_table(
        "color",
        sa.Column("color_id", sa.Integer(), nullable=False, autoincrement=False),
        sa.Column("name", sa.String(128), nullable=True),
        sa.Column("rgb", sa.CHAR(6), nullable=True),
        sa.Column("type", sa.String(32), nullable=True),
        sa.PrimaryKeyConstraint("color_id"),
        **TABLE_KW,
    )

    op.create_table(
        "owned_item",
        sa.Column("id", BIGINT_PK, autoincrement=True, nullable=False),
        sa.Column("item_type", OWNED_ITEM_TYPE, nullable=False),
        sa.Column("item_no", sa.String(32), nullable=False),
        sa.Column("status", OWNED_STATUS, nullable=False),
        sa.Column("copies", sa.SmallInteger(), nullable=False),
        sa.Column("condition", OWNED_CONDITION, nullable=True),
        sa.Column("storage_location", sa.String(255), nullable=True),
        sa.Column("acquired_price", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("acquired_date", sa.Date(), nullable=True),
        sa.Column("date_added", sa.DateTime(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["item_type", "item_no"], ["catalog_item.item_type", "catalog_item.item_no"],
            name="fk_owned_item_catalog",
        ),
        **TABLE_KW,
    )

    op.create_table(
        "set_part",
        sa.Column("id", BIGINT_PK, autoincrement=True, nullable=False),
        sa.Column("set_no", sa.String(32), nullable=False),
        sa.Column("part_item_type", PART_ITEM_TYPE, nullable=False),
        sa.Column("part_no", sa.String(32), nullable=False),
        sa.Column("color_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("extra_quantity", sa.Integer(), nullable=False),
        sa.Column("is_alternate", sa.Boolean(), nullable=False),
        sa.Column("is_counterpart", sa.Boolean(), nullable=False),
        sa.Column("match_no", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["part_item_type", "part_no"], ["catalog_item.item_type", "catalog_item.item_no"],
            name="fk_set_part_catalog",
        ),
        sa.ForeignKeyConstraint(["color_id"], ["color.color_id"], name="fk_set_part_color"),
        sa.UniqueConstraint(
            "set_no", "match_no", "part_item_type", "part_no", "color_id", "is_alternate", "is_counterpart",
            name="uq_set_part_line",
        ),
        sa.Index("ix_set_part_set_no", "set_no"),
        **TABLE_KW,
    )

    op.create_table(
        "ownership",
        sa.Column("id", BIGINT_PK, autoincrement=True, nullable=False),
        sa.Column("owned_item_id", BIGINT_PK, nullable=False),
        sa.Column("copy_index", sa.SmallInteger(), nullable=False),
        sa.Column("set_part_id", BIGINT_PK, nullable=False),
        sa.Column("quantity_owned", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["owned_item_id"], ["owned_item.id"], name="fk_ownership_owned"),
        sa.ForeignKeyConstraint(["set_part_id"], ["set_part.id"], name="fk_ownership_set_part"),
        sa.UniqueConstraint("owned_item_id", "copy_index", "set_part_id", name="uq_ownership_row"),
        **TABLE_KW,
    )

    op.create_table(
        "price_cache",
        sa.Column("id", BIGINT_PK, autoincrement=True, nullable=False),
        sa.Column("item_type", PRICE_ITEM_TYPE, nullable=False),
        sa.Column("item_no", sa.String(32), nullable=False),
        sa.Column("color_id", sa.Integer(), nullable=True),
        sa.Column("guide_type", PRICE_GUIDE, nullable=False),
        sa.Column("condition", PRICE_COND, nullable=False),
        sa.Column("currency", sa.CHAR(3), nullable=False),
        sa.Column("min_price", sa.DECIMAL(12, 4), nullable=True),
        sa.Column("max_price", sa.DECIMAL(12, 4), nullable=True),
        sa.Column("avg_price", sa.DECIMAL(12, 4), nullable=True),
        sa.Column("qty_avg_price", sa.DECIMAL(12, 4), nullable=True),
        sa.Column("unit_quantity", sa.Integer(), nullable=True),
        sa.Column("total_quantity", sa.Integer(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
        sa.Column("ttl_expires_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["color_id"], ["color.color_id"], name="fk_price_color"),
        sa.UniqueConstraint(
            "item_type", "item_no", "color_id", "guide_type", "condition", "currency",
            name="uq_price_cache_row",
        ),
        **TABLE_KW,
    )

    op.create_table(
        "instruction",
        sa.Column("id", BIGINT_PK, autoincrement=True, nullable=False),
        sa.Column("set_no", sa.String(32), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("source_url", sa.String(512), nullable=True),
        sa.Column("local_path", sa.String(512), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("downloaded_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.Index("ix_instruction_set_no", "set_no"),
        **TABLE_KW,
    )

    op.create_table(
        "light_kit",
        sa.Column("id", BIGINT_PK, autoincrement=True, nullable=False),
        sa.Column("set_no", sa.String(32), nullable=False),
        sa.Column("vendor", sa.String(128), nullable=True),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("status", LIGHT_STATUS, nullable=False),
        sa.Column("product_url", sa.String(512), nullable=True),
        sa.Column("local_pdf_path", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.Index("ix_light_kit_set_no", "set_no"),
        **TABLE_KW,
    )

    op.create_table(
        "api_key",
        sa.Column("id", BIGINT_PK, autoincrement=True, nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("key_hash", sa.String(255), nullable=False),
        sa.Column("key_prefix", sa.String(12), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key_hash", name="uq_api_key_hash"),
        **TABLE_KW,
    )

    op.create_table(
        "setting",
        sa.Column("key", sa.String(128), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("is_secret", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("key"),
        **TABLE_KW,
    )

    op.create_table(
        "job",
        sa.Column("id", BIGINT_PK, autoincrement=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("progress", sa.BigInteger(), nullable=False),
        sa.Column("total", sa.BigInteger(), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.Index("ix_job_kind", "kind"),
        sa.Index("ix_job_status", "status"),
        **TABLE_KW,
    )


def downgrade() -> None:
    op.drop_table("job")
    op.drop_table("setting")
    op.drop_table("api_key")
    op.drop_table("light_kit")
    op.drop_table("instruction")
    op.drop_table("price_cache")
    op.drop_table("ownership")
    op.drop_table("set_part")
    op.drop_table("owned_item")
    op.drop_table("color")
    op.drop_table("catalog_item")
