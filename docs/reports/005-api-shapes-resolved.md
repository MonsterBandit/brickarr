# Report 005 — Resolutions for 001–004 (verified against official API docs)

Verified against the BrickLink API reference (`https://static.bricklink.com/alpha/default/api_wiki.html`)
and the Brickset API v3 documentation (`https://brickset.com/article/52664/api-version-3-documentation`)
plus a real `getSets` response sample. Apply the changes below and clear the
matching `# TODO(report:NNN)` markers.

Legend: ✅ assumption correct · ⚠️ correct but needs a tweak · ❌ wrong, must change.

---

## 001 — BrickLink OAuth1 + envelope

**✅ Envelope.** Confirmed `{"meta": {"code", "message", "description"}, "data": ...}`.
Extract `.data`. Treat success as `meta.code` in the 2xx range (not just 200 —
`201` is used for creates). Surface `meta.message`/`meta.description` on failure;
in particular `404 RESOURCE_NOT_FOUND` is what a bad set number returns, so map
that to the "set not found" validation on `POST /sets`.

**✅ Base URL / auth.** `https://api.bricklink.com/api/store/v1`. Two-legged
OAuth1 "simpler flow" with the four static credentials (consumer key/secret +
token value/secret), HMAC-SHA1, header or query param both accepted. No token
handshake, no expiry. Reminder for the Data Sources help text: **the token value
and token secret are bound to the server's registered outbound IP** — a token
issued for one IP won't sign from another.

**⚠️ The real edge case: sign exactly what httpx sends.** The "sign with
`requests`, forward the header to httpx" approach is fine *only if* the signature
base string matches the bytes httpx actually transmits. If the signer and httpx
order or percent-encode the query string differently, the signature breaks and
BrickLink returns `401 BAD_OAUTH_REQUEST`. Safest fix: build the final URL with
its query string once, OAuth1-sign **that exact URL**, and hand httpx the
pre-built URL with **no** separate `params=` kwarg (so httpx can't re-encode it).
Alternatively drop the `requests`→httpx hop and use an httpx-native OAuth1 auth
(e.g. Authlib's `OAuth1Auth`). GET-only in alpha means request-body signing is
moot, so the JSON-body assumption is irrelevant for now — leave it.

**⚠️ Better ping for the Test button.** `GET /items/set/1-1` works (it's a real
catalog item), but `GET /colors` is a stronger health check: it always exists,
needs no item to be valid, and you need the colour list anyway — so the Test
button can double as the colour-table seed.

---

## 002 — BrickLink Subsets

Endpoint and grouping ✅: `GET /items/{type}/{no}/subsets`, returns a nested list
grouped by `match_no`, each group `{ "match_no": int, "entries": [...] }`,
`match_no = 0` meaning no alternate matching. Per-entry fields confirmed:
`item{no,name,type,category_id}`, `color_id`, `quantity`, `extra_quantity`,
`is_alternate`.

**❌ `is_counterpart` does not exist on subset entries.** The documented subset
entry has only `quantity`, `extra_quantity`, and `is_alternate` — there is no
counterpart flag in this response (counterpart is an inventory concept BrickLink
surfaces via `appears_as` on the *superset* endpoint, not subsets). Action: read
it with `.get("is_counterpart", False)` so a missing key can't throw; expect it
to always be false in alpha. Keep the `set_part.is_counterpart` column (harmless),
but note in DATA_MODEL that it is **not populated from the subsets endpoint** in
alpha.

**⚠️ `is_alternate` comes back as a JSON boolean** (`true`/`false`) in real
responses even though the docs table labels it "String". Coerce defensively
(accept bool or `"true"`/`"false"`).

**⚠️ `categoryID`, not `category_id`, in the actual JSON.** BrickLink's live
responses serialize the nested item category as `categoryID` (camel) despite the
docs table. Only matters if you read it — use a fallback (`item.get("category_id")
or item.get("categoryID")`).

**⚠️ Filter non-part rows.** With `instruction`/`box` params (and in general) the
subset can include `INSTRUCTION`, `ORIGINAL_BOX`, or `BOOK` type entries. For the
parts manifest, keep only `item.type in ("PART","MINIFIG")` and ignore the rest.
Keep `break_minifigs=false` so minifigs stay whole (color_id 0 on those lines).

---

## 003 — Brickset getSets

Wrapper ✅: `{ "status": "success", "matches": <int>, "sets": [ ... ] }`.
Top-level fields confirmed: `setID`, `number`, `numberVariant`, `name`, `year`,
`theme`, `themeGroup`, `subtheme`, `category`, `released`, `pieces`, `minifigs`,
`rating`, `bricksetURL`, and a nested `image{thumbnailURL,imageURL}`.

**❌ Retail price is nested, not `USretailPrice`.** It lives at
`LEGOCom.US.retailPrice`. (Heads-up: older samples show the key capitalised as
`RetailPrice`; the v3 class definition uses `retailPrice`. Look it up
case-insensitively.) Other currencies sit beside it under `LEGOCom.UK/CA/DE`.
Map `catalog_item.rrp ← LEGOCom.US.retailPrice`.

**❌ Age range is nested, not `ageMin`/`ageMax`.** It's `ageRange: { min, max }`.
Map `age_min ← ageRange.min`, `age_max ← ageRange.max`.

**✅ `launchDate` / `exitDate` are top-level** (DateTime). Code's assumption holds.
Note there are *also* per-country `LEGOCom.US.dateFirstAvailable` /
`dateLastAvailable`; prefer the top-level `launchDate`/`exitDate` for the global
window and treat the US dates as a fallback.

**⚠️ `userHash` is not needed for getSets.** It only populates the user-specific
`collection` object. Brickarr tracks ownership itself, so call getSets with
`apiKey` + `params` only and omit userHash. `params` is a stringified JSON object
(Brickset quirk), e.g. `params={"setNumber":"43022-1"}` to fetch one set.

**⚠️ Key reconciliation.** Brickset's `number` excludes the variant (`numberVariant`
is separate). To match BrickLink's `(item_type, item_no)` key like `43022-1`,
compose `f"{number}-{numberVariant}"`. Map `brickset_id ← setID`,
`num_pieces ← pieces`, `num_minifigs ← minifigs`, `thumbnail_url ← image.thumbnailURL`.

---

## 004 — Brickset getInstructions

**✅ Mostly correct.** `GET /api/v3.asmx/getInstructions` keyed by **`setID`**
(the numeric Brickset id from getSets, *not* the set number) returns a list whose
entries carry the PDF link in `URL` (capitalised) and a `description`. The links
are plain lego.com CDN PDFs (`https://www.lego.com/cdn/product-assets/...pdf`),
directly fetchable with an unauthenticated GET — so the byte-progress download job
works as-is.

**⚠️ Two small things.** Drop the unnecessary `userHash` (apiKey + setID suffice).
And the two-step dependency is real: capture `setID` during the getSets enrich and
pass it to getInstructions — without it there's no instructions call.

---

## DATA_MODEL touch-ups implied above

- `set_part.is_counterpart` — keep column; document that alpha leaves it false
  (not available from the subsets endpoint).
- Brickset enrich mapping (correct sources):
  `rrp ← LEGOCom.US.retailPrice`, `age_min ← ageRange.min`,
  `age_max ← ageRange.max`, `launch_date ← launchDate`, `exit_date ← exitDate`,
  `brickset_id ← setID`, `thumbnail_url ← image.thumbnailURL`.
- Colour seed mapping (from `GET /colors`):
  `color.name ← color_name`, `color.rgb ← color_code`, `color.type ← color_type`.
- Price guide (for the post-alpha valuation): confirmed fields match price_cache —
  `min_price`, `max_price`, `avg_price`, `qty_avg_price`, `unit_quantity`,
  `total_quantity`, `currency_code`, with `guide_type` = `sold`|`stock` and
  `new_or_used` = `N`|`U`. Endpoint `GET /items/{type}/{no}/price`.
