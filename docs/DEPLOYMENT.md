# Brickarr — Deployment

> Captures what the alpha-1 scaffold ships and how the runtime stack is supposed
> to be put together. Not part of the three authoritative specs
> ([`ALPHA1_BRIEF`](./ALPHA1_BRIEF.md), [`DATA_MODEL`](./DATA_MODEL.md),
> [`API`](./API.md)) — this is the operational companion.

## Image

- **Registry:** `ghcr.io/monsterbandit/brickarr`
- **Visibility:** inherits the repository's (private during alpha).
- **Port:** `5858`. The container runs **a single process** — FastAPI serves the
  REST API at `/api/v1/*` and the built React SPA at `/`. Same as Radarr/Sonarr
  ship: one image, one container, one port.
- **Tags:**
  - `latest` — pushed only for `v*` tags (not on `main` pushes).
  - `vX.Y.Z` and `X.Y` (semver) — pushed for `v*` tags.
  - `main` — rolling tag for the tip of `main`.
  - `sha-<short>` — every build.

## Build

The image is built by `Dockerfile` at the repo root, in two stages:

1. `node:20-alpine` builds the React app (`npm ci && npm run build` inside
   `frontend/`).
2. `python:3.12-slim` installs the backend Python dependencies, copies
   `backend/` to `/app`, and copies the SPA bundle from stage 1 into
   `/app/app/static/` so FastAPI can serve it via `StaticFiles`.

The runtime image installs `tini`, `gosu`, `tzdata`, and `ca-certificates`. No
build tools survive into the final image.

## Volumes

| Container path | Purpose |
| --- | --- |
| `/config`  | App config, the per-instance secret key, rotating logs, the first-run plaintext API key (`initial_api_key.txt`). |
| `/storage` | Library: instruction PDFs, images, light-kit PDFs. |

`mariadb` and `redis` keep their own volumes (see `compose.example.yaml`).
Brickarr never writes the database files itself — that's the database
container's job.

## Environment contract

Connection and process variables only. Data-source credentials (BrickLink,
Brickset) are entered at runtime in **Settings → Data Sources** and stored
encrypted at rest. Never set them via environment.

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `BRICKARR_DB_HOST`     | yes | (compose) `mariadb`    | MariaDB host |
| `BRICKARR_DB_PORT`     | no  | `3306`                 | MariaDB port |
| `BRICKARR_DB_NAME`     | yes | `brickarr`             | Database name |
| `BRICKARR_DB_USER`     | yes | `brickarr`             | Database user |
| `BRICKARR_DB_PASSWORD` | yes | — (must be set)        | Database password |
| `BRICKARR_REDIS_URL`   | yes | `redis://redis:6379/0` | Redis URL |
| `PUID`                 | no  | `1000`                 | Run-as user id |
| `PGID`                 | no  | `1000`                 | Run-as group id |
| `TZ`                   | no  | `Etc/UTC`              | Container timezone |
| `BRICKARR_CONFIG_DIR`  | no  | `/config`              | Override the config mount (testing only) |
| `BRICKARR_STORAGE_DIR` | no  | `/storage`             | Override the storage mount (testing only) |

## Entrypoint behaviour

The entrypoint (`docker/entrypoint.sh`) does, in order:

1. Symlinks `/etc/localtime` to the requested `TZ`.
2. Rewrites the `brickarr` user/group uid/gid to match `PUID`/`PGID`.
3. Creates `/config`, `/config/logs`, and `/storage` and `chown`s them.
4. Runs `alembic upgrade head` (refuses to start if migrations fail — better to
   crash visibly than to serve against a stale schema).
5. `exec`s the CMD (`uvicorn app.main:app …`) as the `brickarr` user via
   `gosu`.

## First-run secrets

- The app generates a per-instance **Fernet key** on first start and persists
  it to `/config/secret.key` (mode `0600`). All encrypted settings (`setting`
  rows with `is_secret = TRUE`) are protected by this key. Lose the file → lose
  the ability to decrypt stored credentials.
- The app generates one default **API key** on first start, hashes it into the
  `api_key` table, and writes the plaintext **once** to
  `/config/initial_api_key.txt` (mode `0600`) along with a WARN-level log line
  pointing at the path. Read it, store it in your password manager, delete the
  file. The key can be regenerated at Settings → General.

## CI publish flow

`.github/workflows/publish.yml`:

- **Triggers:** pushes to `main`, pushes of `v*` tags, manual `workflow_dispatch`.
- **Auth:** `${{ secrets.GITHUB_TOKEN }}` — no PATs. Workflow permissions are
  set to `contents: read` and `packages: write`; the repo's *Actions → Workflow
  permissions* setting must allow the default token to write packages. If the
  first publish fails with HTTP 403, fix it there.
- **Build:** `linux/amd64` only for alpha. Uses `docker/build-push-action@v6`
  with GitHub Actions cache.
- **Tag policy:** `metadata-action` derives image tags from the git ref. A push
  to `main` produces `main` and `sha-…`; a `vX.Y.Z` tag produces `vX.Y.Z`,
  `X.Y`, `latest`, and `sha-…`.

## Running with `compose.example.yaml`

```bash
cp .env.example .env
# set BRICKARR_DB_PASSWORD (and PUID/PGID/TZ if you care)
docker compose -f compose.example.yaml --env-file .env up -d
docker compose -f compose.example.yaml logs -f brickarr
```

Brickarr will be at <http://localhost:5858>. The first-run logs include the
path to `initial_api_key.txt` in the `./config/` bind mount.

The compose file is a reference for new users. Production stacks live
elsewhere and should pin a specific `image:` tag rather than `:latest`.

## Health & probes

- `GET /api/v1/ping` — unauthenticated liveness.
- `GET /api/v1/health` — authenticated, *arr-style health array (missing
  credentials, BrickLink budget exhausted, etc.).
- `GET /api/v1/system/status` — version, DB up, data-source reachability,
  BrickLink budget remaining today vs. configured cap.

## API-shape reports

`docs/reports/` is the bridge for real-world API shapes that the design chat
can't supply. Each report names a specific assumption, what would verify it,
and (once resolved) the correction that landed in the code. Reports 001–004
are resolved by 005, which was reconciled against the official BrickLink and
Brickset v3 documentation; the BrickLink and Brickset clients now reflect the
corrected envelopes, field mappings, OAuth1 signing path, and colour seed.
