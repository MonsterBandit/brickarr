# Brickarr — REST API

> Status: **alpha-1**. The API is a first-class surface, not an afterthought:
> it's how the household assistant ("Alice") queries the collection the same way
> it queries the *arr media stack. Endpoints/fields marked _(post-alpha)_ are
> defined now but return `null`/stub values in alpha-1.

Base URL: `/api/v1`
Dialect: *arr-style JSON — **camelCase** fields, list endpoints return a paged
envelope, validation errors return a property/message array.

---

## Authentication

Two doors, both valid for `/api/v1/*`:

1. **API key (machine / Alice).** Header `X-Api-Key: <key>` **or** query
   `?apikey=<key>`. Generated at Settings → General, regenerable, multiple keys
   supported (`api_key` table). The API key works **regardless** of the UI auth
   mode — it is the machine interface.
2. **Session cookie (UI).** Issued by forms login.

UI auth modes mirror the *arr stack (Settings → General):
`Forms (login page)` · `Disabled for Local Addresses` · `External` (auth handled
upstream by NPM / Cloudflare / Authelia — avoids a double login).

Unauthenticated: `GET /ping` only.

### Errors

```json
// 400 validation
[ { "propertyName": "setNumber", "errorMessage": "Set not found on BrickLink" } ]

// 401 / 404 / 5xx
{ "error": "Unauthorized", "message": "Missing or invalid API key" }
```

### Paged list envelope

```json
{
  "page": 1,
  "pageSize": 50,
  "sortKey": "name",
  "sortDirection": "ascending",
  "totalRecords": 137,
  "records": [ /* … */ ]
}
```

---

## Sets

### `GET /sets`
List owned sets (the collection grid).
Query: `status`, `theme`, `tag`, `search`, `sortKey`, `sortDirection`, `page`, `pageSize`.
Returns the paged envelope of set summaries.

### `GET /sets/lookup?term=`
Search the BrickLink / Brickset catalog for the Add flow (typeahead). Returns
candidate `catalog_item`s with an `owned` flag. No `owned_item` is created.

### `GET /sets/{id}`
One owned set (`id` = `owned_item.id`). Full detail — catalog + Brickset meta +
rolled-up stats.

```json
{
  "id": 12,
  "itemType": "SET",
  "setNumber": "43022-1",
  "name": "...",
  "status": "complete",
  "condition": "used",
  "copies": 1,
  "storageLocation": "Bin A3",
  "theme": "Disney",
  "subtheme": "...",
  "year": 2023,
  "pieces": 880,
  "minifigs": 1,
  "rrp": 99.99,
  "acquiredPrice": 65.00,
  "acquiredDate": "2024-02-10",
  "launchDate": "2023-08-01",
  "exitDate": null,
  "imageUrl": "...",
  "stats": { "owned": 870, "missing": 10, "pricePerPiece": 0.11 },
  "currentValue": null,          // (post-alpha)
  "gainLoss": null,              // (post-alpha)
  "links": { "bricklink": "https://www.bricklink.com/v2/catalog/catalogitem.page?S=43022-1" }
}
```

### `POST /sets`
Add a set to the collection. Enqueues a catalog mirror + manifest pull + Brickset
enrich (async — track in `/queue`).

```json
{ "setNumber": "43022-1", "status": "complete", "condition": "used",
  "copies": 1, "storageLocation": "Bin A3",
  "acquiredPrice": 65.00, "acquiredDate": "2024-02-10" }
```
Returns the created `owned_item` (`201`).

### `PATCH /sets/{id}`
Update `status`, `condition`, `copies`, `storageLocation`, `acquiredPrice`,
`acquiredDate`, `notes`.

### `DELETE /sets/{id}`
Remove from the collection. Catalog rows are retained (shared/cache).

---

## Parts manifest & ownership

### `GET /sets/{id}/parts`
The manifest with ownership rollup — the centerpiece.
Query: `filter=all|owned|missing`, `colorId`, `search`.

```json
{
  "records": [
    { "setPartId": 4411, "partNo": "3001", "name": "Brick 2 x 4",
      "colorId": 5, "colorName": "Red", "thumbnailUrl": "...",
      "quantity": 6, "extraQuantity": 1,
      "owned": 6, "missing": 0,
      "isAlternate": false, "isCounterpart": false, "matchNo": 0 }
  ]
}
```

### `PATCH /sets/{id}/parts`
Set ownership (writes sparse `ownership` rows). Body is an array:

```json
[ { "setPartId": 4411, "quantityOwned": 4 },
  { "partNo": "3002", "colorId": 11, "quantityOwned": 0 } ]
```

### `GET /sets/{id}/minifigs`
The set's minifig "cast" — manifest lines where `partItemType = MINIFIG`.

---

## Value & pricing

### `GET /sets/{id}/value`
**Alpha: link-out only.** Built from the set number → near-zero API calls.

```json
{
  "rrp": 99.99,
  "links": {
    "priceGuide":   "https://www.bricklink.com/catalogPG.asp?S=43022-1",
    "itemsForSale": "https://www.bricklink.com/v2/catalog/catalogitem.page?S=43022-1#T=S",
    "partOutValue": "https://www.bricklink.com/catalogPOV.asp?itemType=S&itemNo=43022&itemSeq=1"
  },
  "computed": null              // (post-alpha) qty_avg value, part-out, etc.
}
```

### `GET /parts/{partNo}/price?colorId=&guideType=&condition=` _(optional in alpha)_
Single-part price. Returns from `price_cache` if fresh; otherwise may make **one**
budget-checked BrickLink call. If pricing is deferred at the instance level,
returns `{ "available": false }`. Never returns a silent `$0` for thin data.

---

## Buy-list

### `GET /sets/{id}/buylist?format=xml|csv|json`
Missing parts as a BrickLink Wanted List. Default `xml` (directly importable to
BrickLink). `colorId` and quantities come from the manifest minus ownership.

```xml
<INVENTORY>
  <ITEM><ITEMTYPE>P</ITEMTYPE><ITEMID>3001</ITEMID><COLOR>5</COLOR><MINQTY>2</MINQTY></ITEM>
</INVENTORY>
```

### `GET /buylist?format=` _(optional in alpha)_
Collection-wide buy-list — all missing parts across owned sets, consolidated.

---

## Instructions

### `GET /sets/{id}/instructions`
List booklets: `{ id, description, sourceUrl, downloaded, localPath, sizeBytes }`.

### `POST /sets/{id}/instructions/download`
Enqueue download of all/selected booklets. Async with **real byte progress**
surfaced in `/queue`. Body: `{ "instructionIds": [..] }` (omit = all).

### `GET /instructions/{id}/file`
Stream the stored PDF.

---

## Collection

### `GET /collection/value`
Aggregate dashboard numbers.

```json
{
  "counts": { "sets": 137, "minifigs": 642, "parts": 89231 },
  "rrpTotal": 14210.00,
  "acquiredTotal": 9880.00,
  "currentValueTotal": null,    // (post-alpha)
  "gainLossTotal": null         // (post-alpha)
}
```

---

## Activity

### `GET /queue`
Live jobs with progress (manifest pulls, PDF downloads w/ bytes, valuation runs).

### `GET /history`
Completed job history. Query: `eventType`, `page`, `pageSize`.

---

## System

### `GET /system/status`
Version, DB status, data-source reachability (BrickLink / Brickset), and
**BrickLink budget remaining today** (from the Redis counter vs the configured cap).

### `GET /system/tasks`
Scheduled tasks + last/next run: `refresh-prices`, `check-retirements`,
`check-price-drops`, `sync-import-lists`, `refresh-manifests`.

### `POST /command`
*arr-style command trigger. Body `{ "name": "RefreshManifests" }`. Alpha exposes
a small set mapping to the scheduled tasks above.

---

## Health

### `GET /health`
*arr-style health checks array — surfaces warnings: missing/invalid credentials,
unreachable data source, BrickLink budget exhausted.

```json
[ { "source": "BrickLink", "type": "warning",
    "message": "Daily request budget exhausted (5000/5000)" } ]
```

### `GET /ping`
Unauthenticated liveness probe. `{ "status": "ok" }`.
