# Brickarr — Alpha-1 Build Brief

> **Read this first.** It scopes the build and points at the two companion specs:
> [`DATA_MODEL.md`](./DATA_MODEL.md) and [`API.md`](./API.md). Build **only** what
> is in scope here. The "Parked" list at the end is real — do not drift into it.

## What Brickarr is

A self-hosted, *arr-style web app for managing a personal LEGO collection —
Sonarr/Radarr, but for LEGO. You add a set; Brickarr pulls its parts manifest,
tracks owned vs. missing, fetches instructions, and exposes a clean,
API-key-authenticated REST API so a household assistant can query the collection
like it queries the media stack.

Alpha-1 is **the spine**, private. The arc after is: beta (functional) → make the
repo public → community decides v1.

## Repo & workflow

- Repo (private): `https://github.com/MonsterBandit/brickarr`
- You (Claude Code) have the credentials and repo access. Commit your work there.
- When you need a **real-world fact** the design can't supply — e.g. the exact
  shape of a BrickLink `subsets` response, an actual instruction-PDF URL pattern,
  or a run result — write a short report to `/docs/reports/NNN-topic.md` and tell
  the user to paste it back into the design chat. The design assistant cannot
  reach the repo or the APIs; this is the bridge.

## Reference posture (important — licensing)

- **Emulate the *arr stack; do not fork it.** Radarr/Sonarr are C#/.NET + React on
  SQLite/Postgres and their value is a media-acquisition engine LEGO discards.
  We keep the *shape*, not the code.
- Use **Radarr as a reference** for API conventions, settings layout, the dark UI
  look, and backend patterns — but **write originals.** Radarr is GPL-3.0; copying
  its code would impose copyleft on a repo we intend to open. Read it, don't paste it.
- Base model is **Radarr** (flat "one monitored thing = one Movie" → "one Set"),
  not Sonarr's Series→Season→Episode hierarchy.

## Stack & infrastructure

- **Backend:** Python + FastAPI. **DB:** MariaDB. **Cache/queue/budget:** Redis.
  **Frontend:** React (dark theme).
- **Port:** `5858`.
- **Docker:** mirror *arr conventions — `PUID`/`PGID`, `TZ`, a `/config` volume
  (app config + logs) and a library volume (instructions/images). Runs as its own
  Dockge stack behind Nginx Proxy Manager.
- First-run setup flow, rotating logs, auto DB backup, health/warning system,
  named scheduled tasks.

## Auth (mirror the *arr stack)

- Forms login (default/recommended), a "Disabled for Local Addresses" toggle, and
  an `External` mode for when NPM/Cloudflare/Authelia handle auth (no double login).
- A separate, auto-generated **API key** (`X-Api-Key` header or `?apikey=`),
  regenerable, shown at Settings → General. This is the machine door and works
  regardless of UI auth mode. See `API.md`.

## Credentials (public-safe handling)

- **Never** in code. Entered at Settings → Data Sources, stored in `setting`
  (encrypted at rest, kept out of logs), env-var overridable. Ship a **blank**
  `.env.example`.
- Each source has a **Test** button that validates before save.
- BrickLink: OAuth1, four values (consumer key, consumer secret, token value,
  token secret). Brickset: one API key.

## Alpha-1 scope (the spine)

1. **Add a set** (`POST /sets`): mirror the BrickLink catalog item + **Subsets**
   manifest (`break_minifigs=false`), enrich from Brickset (theme/subtheme, RRP,
   launch/exit dates, instruction URLs). Store per `DATA_MODEL.md`.
2. **Set detail page** (modeled on Radarr's movie page): status toggle
   (Owned/Collecting/Wishlist) · stats row · metadata grid (incl. storage location
   + acquired price) · hero image · **parts manifest** (the centerpiece — filterable
   owned/own/missing) · instructions (download with **real byte progress**) ·
   minifig "cast" · light-kit panel.
3. **Collection grid** ("Sets"), **Themes** grouping, derived **Minifigs** and
   **Parts** views.
4. **Ownership**: sparse model from `DATA_MODEL.md`. Owned/missing computed from
   status defaults + `ownership` overrides.
5. **Buy-list export**: missing parts → BrickLink Wanted List XML
   (`GET /sets/{id}/buylist`).
6. **Pricing = link-out only.** A row of deep-link buttons (View Price Guide ·
   Items For Sale · Part-Out Value) built from the set number. **No computed
   valuation** — that's post-alpha.
7. **Wanted** (basic wishlist), **Calendar** (wishlist release dates only),
   **Activity** (queue + history).
8. **Settings (8 pages)** and **System (6 pages)** per the locked menu below.
9. **REST API** per `API.md`, secured by `X-Api-Key`.

## Locked navigation

```
Sets                 (clicking the label = the sets grid)
   Add New           (single set; no type picker in alpha)
   Import            (one unified Collection Import; type-routes mixed exports)
   Discover
   Themes            (group owned sets by Brickset theme/subtheme)
   Minifigs          (derived)
   Parts             (derived)
Calendar             (upcoming RELEASE dates of wishlist items only)
Activity             (Queue: live jobs w/ progress + History)
Wanted               (Wanted Sets = wishlist; Wanted Parts = buy-list)
Settings
System
```

**Settings (8):** General (incl. auto-gen API key) · UI · Tags · Connect
(notifications) · Media Management (library path, naming tokens, PUID/PGID,
optional watch-folder) · **Pricing** (currency, sold/stock, new/used basis, cache
TTL, daily BrickLink budget cap) · **Data Sources** (BrickLink/Brickset creds +
Test + budget readout) · Import Lists (recurring auto-sync).

**System (6):** Status (+ BrickLink budget remaining, source reachability) ·
Tasks · Backup · Updates · Events · Log Files.

## Data model & API

Authoritative specs — follow them exactly:
- [`DATA_MODEL.md`](./DATA_MODEL.md)
- [`API.md`](./API.md)

## BrickLink usage rules

- **Mirror the catalog, cache effectively forever.** Item info + subsets ≈ 2 calls
  per set, cached; needed for owned/missing and offline use.
- **Link out for price** in alpha (no price calls for valuation).
- Respect the **5000 requests/day** ceiling. Maintain a **Redis daily-budget
  counter**; check it before every BrickLink call; cap is configurable in Pricing
  settings. Surface "budget remaining" in System → Status and `/health`.
- Confirm exact request/response shapes at the server and report any surprises to
  `/docs/reports/`.

## Suggested build order

1. Scaffold (FastAPI app, React shell, Docker stack, port 5858, volumes, first-run).
2. DB + migrations for `DATA_MODEL.md`; seed `color` from BrickLink.
3. Auth (forms + modes) and `api_key` / `X-Api-Key` dependency.
4. Data Sources settings + Test buttons (BrickLink OAuth1, Brickset).
5. Catalog mirror service + Add-set flow (`POST /sets` → async job → `/queue`).
6. Manifest (`set_part`) + sparse `ownership` + owned/missing rollup.
7. Set detail page (parts manifest first), collection grid, Themes/Minifigs/Parts.
8. Instructions download (byte progress) + buy-list XML export.
9. Remaining API surface, Settings/System pages, health checks, scheduled tasks.
10. Polish, logs, backup, docs.

## Parked — do NOT build in alpha-1

Computed valuation / price-cache population · standalone minifig or loose-part
adds · wishlist price-drop history (time-series) · MOC discovery / Rebrickable
cross-ref · light-kit scraping (manual upload only in alpha) · multi-user.

## Definition of done (alpha-1)

Add a real set → its manifest pulls and renders with correct owned/missing →
instructions download with visible progress → a buy-list XML imports cleanly into
BrickLink → the deep-link price buttons work → the whole collection is queryable
over the REST API with an `X-Api-Key`, behind working auth, in a Docker stack on
port 5858.
