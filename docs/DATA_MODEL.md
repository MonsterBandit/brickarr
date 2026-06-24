# Brickarr — Data Model

> Status: **alpha-1**. This document defines the database schema for the spine.
> Tables and columns marked _(post-alpha)_ are part of the locked design but are
> created empty / stubbed in alpha-1 and populated in a later milestone.

## Principles

1. **BrickLink is the key.** Everything in the catalog is keyed on
   `(item_type, item_no)` exactly as BrickLink identifies it
   (e.g. `SET / 43022-1`, `PART / 3001`, `MINIFIG / sw0001a`).
2. **Mirror the catalog, link out for price.** Catalog data (item info, parts
   manifest, colors, IDs) is cheap and static — mirror it and cache effectively
   forever. Price data is expensive and volatile — in alpha we link out to
   BrickLink rather than store it.
3. **Sets-first, type-ready.** Alpha ships Sets only. Minifigs and Parts are
   **derived views** rolled up from owned sets' manifests, not separately added.
   The tracked entity is generalised to `owned_item` (with an `item_type`) so
   standalone minifig/part collecting can be added later without rearchitecting.
4. **Ownership is sparse.** We never write a row per part per set. A part's
   owned/missing state is *derived* from the set's status; a row exists in
   `ownership` only when a specific copy **deviates** from that default.
5. **A complete set page is a union of three sources:** BrickLink (identity,
   manifest, dimensions, images, price), Brickset (theme, RRP, launch/exit
   dates, instruction PDFs, rating), Rebrickable (cross-ref + MOCs, post-alpha).

---

## Entities

### `catalog_item`
The mirrored "thing that exists in the world." Holds all three item types.
Brickset enrichment columns are SET-only and nullable.

| Field | Type | Notes |
|---|---|---|
| `item_type` | ENUM('SET','MINIFIG','PART') | **PK**. BrickLink item type. |
| `item_no` | VARCHAR(32) | **PK**. BrickLink number incl. sequence (`43022-1`). |
| `name` | VARCHAR(512) | |
| `category_id` | INT | BrickLink category — **not** a theme. |
| `category_name` | VARCHAR(255) | |
| `year_released` | SMALLINT | |
| `image_url` | VARCHAR(512) | BrickLink CDN. |
| `thumbnail_url` | VARCHAR(512) | |
| `weight_g` | DECIMAL(10,2) | nullable |
| `dim_x_cm` / `dim_y_cm` / `dim_z_cm` | DECIMAL(8,2) | nullable |
| `rebrickable_id` | VARCHAR(32) | nullable, _(post-alpha cross-ref)_ |
| `theme` | VARCHAR(128) | _SET-only, Brickset._ |
| `subtheme` | VARCHAR(128) | _SET-only, Brickset._ |
| `rrp` | DECIMAL(10,2) | _SET-only, Brickset._ Retail price; currency in `setting`. |
| `launch_date` | DATE | _SET-only, Brickset._ |
| `exit_date` | DATE | _SET-only, Brickset._ Retirement. |
| `age_min` / `age_max` | SMALLINT | _SET-only, Brickset._ |
| `num_pieces` | INT | _SET-only._ |
| `num_minifigs` | INT | _SET-only._ |
| `rating` | DECIMAL(3,2) | _SET-only, Brickset._ |
| `brickset_id` | VARCHAR(32) | nullable; Brickset internal id for instruction lookups. |
| `catalog_synced_at` | DATETIME | When BrickLink data was mirrored. |
| `brickset_synced_at` | DATETIME | nullable |
| `created_at` / `updated_at` | DATETIME | |

### `color`
BrickLink colour reference, mirrored once.

| Field | Type | Notes |
|---|---|---|
| `color_id` | INT | **PK**, BrickLink colour id. |
| `name` | VARCHAR(128) | |
| `rgb` | CHAR(6) | hex, no `#` |
| `type` | VARCHAR(32) | Solid / Transparent / Chrome / etc. |

### `owned_item`
The tracked entity — a thing the user owns or wants. Type-ready; alpha only
ever creates `SET` rows.

| Field | Type | Notes |
|---|---|---|
| `id` | BIGINT | **PK**, auto. |
| `item_type` | ENUM('SET','MINIFIG','PART') | `SET` in alpha. |
| `item_no` | VARCHAR(32) | FK → `catalog_item(item_type, item_no)`. |
| `status` | ENUM('collecting','complete','wanted','dismantled') | See ownership defaults below. |
| `copies` | SMALLINT | default 1. |
| `condition` | ENUM('new','used') | nullable. |
| `storage_location` | VARCHAR(255) | nullable. |
| `acquired_price` | DECIMAL(10,2) | nullable. |
| `acquired_date` | DATE | nullable. |
| `date_added` | DATETIME | |
| `notes` | TEXT | nullable. |
| `created_at` / `updated_at` | DATETIME | |

`acquired_price` vs computed current value (post-alpha) gives per-set gain/loss.

### `set_part`
The parts manifest of a set, pulled from BrickLink **Subsets** with
`break_minifigs=false` (minifigs stay whole). Intrinsic to the catalog set and
shared across every owner/copy.

| Field | Type | Notes |
|---|---|---|
| `id` | BIGINT | **PK**, auto. |
| `set_no` | VARCHAR(32) | FK → `catalog_item.item_no` (type SET). |
| `part_item_type` | ENUM('PART','MINIFIG') | manifest line type. |
| `part_no` | VARCHAR(32) | FK → `catalog_item.item_no`. |
| `color_id` | INT | FK → `color`. 0/NA for minifig lines. |
| `quantity` | INT | regular quantity. |
| `extra_quantity` | INT | BrickLink "extra" (spares). |
| `is_alternate` | BOOL | alternate within a match group. |
| `is_counterpart` | BOOL | |
| `match_no` | INT | groups alternates; 0 = regular. |

Unique index on `(set_no, match_no, part_item_type, part_no, color_id, is_alternate, is_counterpart)`.
Captures BrickLink's Regular / Extra / Counterpart / Alternate semantics.

> **Alpha note on `is_counterpart`.** BrickLink's `/subsets` endpoint does not
> carry an `is_counterpart` flag — counterpart is an inventory concept exposed
> via the `/supersets` endpoint, not subsets. The column is preserved for
> forward compatibility but is left `false` for every row written by alpha
> from a Subsets mirror.

### `ownership` (sparse)
Records a part's actual owned count for one copy **only when it deviates from
the status default.**

| Field | Type | Notes |
|---|---|---|
| `id` | BIGINT | **PK**, auto. |
| `owned_item_id` | BIGINT | FK → `owned_item`. |
| `copy_index` | SMALLINT | default 1; which copy when `copies > 1`. |
| `set_part_id` | BIGINT | FK → `set_part`. |
| `quantity_owned` | INT | overrides the derived default. |
| `created_at` / `updated_at` | DATETIME | |

Unique `(owned_item_id, copy_index, set_part_id)`.

**Status → default owned quantity for each manifest line:**

| status | default owned | a row is written to record… |
|---|---|---|
| `complete` | `quantity` (all present) | a **missing** part |
| `collecting` | `0` | a part you **have** |
| `dismantled` | `quantity` (parts kept) | a **missing/lost** part |
| `wanted` | `0` (wishlist) | n/a — wishlist, not part-tracked |

Owned = override if a row exists, else the default. Missing = `quantity - owned`.
The collection buy-list is the sum of `missing` across all owned items.

### `price_cache` _(schema in alpha, populated post-alpha)_
TTL'd, shared across all sets that contain the same part/colour.

| Field | Type | Notes |
|---|---|---|
| `id` | BIGINT | **PK**, auto. |
| `item_type` / `item_no` | ENUM / VARCHAR(32) | FK → `catalog_item`. |
| `color_id` | INT | FK → `color`; NULL for set-level. |
| `guide_type` | ENUM('sold','stock') | sold = last-6-mo realised; stock = current asking. |
| `condition` | ENUM('new','used') | |
| `currency` | CHAR(3) | one base currency for the instance. |
| `min_price` / `max_price` / `avg_price` / `qty_avg_price` | DECIMAL(12,4) | |
| `unit_quantity` / `total_quantity` | INT | |
| `fetched_at` | DATETIME | |
| `ttl_expires_at` | DATETIME | TTL from Pricing settings. |

Unique `(item_type, item_no, color_id, guide_type, condition, currency)`.
Use `qty_avg_price` for fair value, `min_price` for buy-list cost. Thin data
must never silently render as `$0`.

### `instruction`
Instruction booklets (LEGO CDN / Brickset).

| Field | Type | Notes |
|---|---|---|
| `id` | BIGINT | **PK**, auto. |
| `set_no` | VARCHAR(32) | FK → `catalog_item.item_no`. |
| `description` | VARCHAR(255) | e.g. "Book 1". |
| `source_url` | VARCHAR(512) | |
| `local_path` | VARCHAR(512) | nullable until downloaded. |
| `file_size_bytes` | BIGINT | nullable. |
| `downloaded_at` | DATETIME | NULL = not yet downloaded. |
| `created_at` | DATETIME | |

### `light_kit`
Third-party light kits attached to a set (BriksMax, Lightailing, …). No vendor
API — product link + optional manual PDF upload.

| Field | Type | Notes |
|---|---|---|
| `id` | BIGINT | **PK**, auto. |
| `set_no` | VARCHAR(32) | FK → `catalog_item.item_no`. |
| `vendor` | VARCHAR(128) | |
| `name` | VARCHAR(255) | |
| `status` | ENUM('owned','wanted') | |
| `product_url` | VARCHAR(512) | nullable. |
| `local_pdf_path` | VARCHAR(512) | nullable; stored under `Light Kit - {vendor}/`. |
| `created_at` / `updated_at` | DATETIME | |

### `api_key`
Machine access — Alice's door, plus the UI's own key.

| Field | Type | Notes |
|---|---|---|
| `id` | BIGINT | **PK**, auto. |
| `name` | VARCHAR(128) | label, e.g. "Alice", "default". |
| `key_hash` | VARCHAR(255) | hashed; **never** store plaintext. |
| `key_prefix` | VARCHAR(12) | first chars, for display/identification. |
| `last_used_at` | DATETIME | nullable. |
| `created_at` | DATETIME | |

Settings → General auto-generates the default key on first run; regenerable.

### `setting`
Key/value config store.

| Field | Type | Notes |
|---|---|---|
| `key` | VARCHAR(128) | **PK**. |
| `value` | TEXT | |
| `is_secret` | BOOL | secrets encrypted at rest, kept out of logs. |

Holds: data-source credentials (encrypted), base currency, pricing basis +
cache TTL + daily budget cap, library path, naming tokens, PUID/PGID, auth mode.

---

## Not in the database

- **Daily BrickLink budget** — a Redis counter (`INCR` with a daily-expiring
  key), not a table. Checked before every BrickLink call; cap comes from
  `setting`.
- **Activity queue + live job progress** — Redis (PDF byte progress, manifest
  pulls, valuation runs). History is persisted; the live queue is Redis.

---

## Relationships

```
catalog_item (SET) 1───* owned_item
catalog_item (SET) 1───* set_part *───1 catalog_item (PART | MINIFIG)
set_part           *───1 color
owned_item         1───* ownership *───1 set_part        (sparse)
catalog_item (SET) 1───* instruction
catalog_item (SET) 1───* light_kit
catalog_item       *───* price_cache  (per color / guide_type / condition / currency)
```

Derived views (no own tables in alpha):
- **Minifigs** = `set_part` rows where `part_item_type = 'MINIFIG'`, rolled up
  across owned sets.
- **Parts** = `set_part` rows where `part_item_type = 'PART'`, rolled up across
  owned sets, joined to `ownership` for owned/missing.
- **Themes** = `owned_item` grouped by `catalog_item.theme` / `.subtheme`.

---

## Deferred (parked — do not build in alpha-1)

- Standalone minifig / loose-part `owned_item` adds.
- Computed valuation population of `price_cache`.
- Wishlist price-drop time-series (a separate snapshot store).
- Rebrickable cross-ref + MOC tables.
- Multi-user / `user` table.
