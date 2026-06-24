# Brickarr

A self-hosted, \*arr-style web app for managing a personal LEGO collection —
Sonarr/Radarr, but for LEGO. Add a set, Brickarr pulls the parts manifest from
BrickLink, enriches it from Brickset, tracks owned vs. missing, fetches
instruction PDFs, and exposes an API-key-authenticated REST surface.

> **Status: alpha-1, private.** The arc is alpha (spine) → beta (functional) →
> public.

## Stack

- **Backend:** Python + FastAPI
- **Database:** MariaDB
- **Cache / job queue / daily-budget counter:** Redis
- **Frontend:** React (dark theme), bundled and served by the FastAPI process
- **Port:** `5858` (single container, one image — *arr convention)

## Quick start (reference compose)

`compose.example.yaml` is a public-safe reference stack: the Brickarr image plus
bundled MariaDB and Redis. It is an example only — production deployments live
elsewhere.

```bash
cp .env.example .env
# fill BRICKARR_DB_PASSWORD and (optionally) PUID/PGID/TZ
docker compose -f compose.example.yaml --env-file .env up -d
```

Brickarr will be available at <http://localhost:5858>.

### First-run

1. On first start the API key is generated and written once to
   `/config/initial_api_key.txt` (mode 0600). Capture it and rotate at
   Settings → General.
2. Configure BrickLink (OAuth1: consumer key/secret + token value/secret) and
   Brickset (API key) at Settings → Data Sources. Each source has a **Test**
   button that validates before save.

## Volumes

Two mountpoints, fixed by the image:

| Path        | Purpose                                                  |
| ----------- | -------------------------------------------------------- |
| `/config`   | App config, the SQLite-free runtime state, rotating logs |
| `/storage`  | Library: instruction PDFs, images, light-kit PDFs        |

The MariaDB data volume belongs to the database container, not this image.

## Environment

Connection variables only — credentials for BrickLink/Brickset are runtime, not
env:

| Variable | Notes |
|---|---|
| `BRICKARR_DB_HOST`     | MariaDB host                                       |
| `BRICKARR_DB_PORT`     | MariaDB port (default `3306`)                      |
| `BRICKARR_DB_NAME`     | Database name                                      |
| `BRICKARR_DB_USER`     | Database user                                      |
| `BRICKARR_DB_PASSWORD` | Database password                                  |
| `BRICKARR_REDIS_URL`   | Redis URL, e.g. `redis://redis:6379/0`             |
| `PUID` / `PGID`        | Container process uid/gid (\*arr convention)        |
| `TZ`                   | Container timezone                                 |

## Documentation

- [`docs/ALPHA1_BRIEF.md`](docs/ALPHA1_BRIEF.md) — scope of alpha-1 (read first)
- [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) — database schema (authoritative)
- [`docs/API.md`](docs/API.md) — REST surface (authoritative)
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) — image, CI publish flow, volumes
- [`docs/reports/`](docs/reports/) — running notes on real-world unknowns
  (BrickLink/Brickset response shapes, PDF URL patterns) — populated as we hit
  them

## Container image

Images are published to
[`ghcr.io/monsterbandit/brickarr`](https://ghcr.io/monsterbandit/brickarr) on
every push to `main` and on `v*` tags. The package inherits the repository's
visibility — alpha images are private.

## License

**TBD** — no license file is present yet. Pending an explicit license decision
before the repo is made public. Until then, all rights reserved.

The codebase is original. Radarr/Sonarr have been read as a reference for \*arr
conventions only; no code has been copied from those (GPL-licensed) projects.
