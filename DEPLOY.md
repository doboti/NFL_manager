# Deployment

Two separate GitHub Actions workflows:

- **`.github/workflows/ci.yml`** — runs on every push to `main`. Builds the
  backend and frontend Docker images and pushes them to GitHub Container
  Registry (GHCR), tagged both `:latest` and `:<commit-sha>`. It never
  touches the server.
- **`.github/workflows/deploy-prod.yml`** — runs only when you trigger it by
  hand (GitHub → Actions → "Deploy to production" → Run workflow). Copies the
  repo's current `docker-compose.prod.yml` onto the server (so the server
  never runs a stale, manually-edited copy), then runs
  `docker compose pull && up -d` for the image tag you choose (defaults to
  `latest`, or type a specific commit SHA to pin/roll back).

So the day-to-day flow is: develop and test locally with `docker-compose.yml`
(dev — hot reload, bind mounts) exactly as before. When you push to `main`,
fresh images get built and sit in GHCR ready to go, but production is
untouched. Once you're satisfied, go to the Actions tab and manually run
"Deploy to production" — that's the only thing that ever changes the server.

The backend container runs `alembic upgrade head` on every start, so DB
migrations ship automatically whenever a deploy happens.

## One-time setup

### 1. Server: deploy directory and secrets

```bash
mkdir -p /opt/nfl-manager
cd /opt/nfl-manager
# copy .env.example from the repo here (scp or paste) — docker-compose.prod.yml
# gets synced automatically by the deploy workflow, no need to copy it by hand
cp .env.example .env
# edit .env: set POSTGRES_PASSWORD and JWT_SECRET_KEY to real random values
# (generate each with: openssl rand -hex 32), and set FRONTEND_ORIGIN to
# wherever the frontend will actually be served from (must match exactly,
# including scheme and port, or the backend's CORS check rejects every
# request from the browser with a 400 on the preflight)
```

Before the first deploy has run, `docker-compose.prod.yml` won't exist here
yet — that's fine, the first deploy run creates it via the sync step.

### 2. Server: dedicated SSH key for CI

On your own machine (not the server):

```bash
ssh-keygen -t ed25519 -f nfl_manager_deploy_key -N ""
```

Append `nfl_manager_deploy_key.pub` to `~/.ssh/authorized_keys` on the server
for the user that will run the deploy (needs docker permissions). Keep
`nfl_manager_deploy_key` (private half) for the GitHub secret below.

### 3. Tailscale auth key (only if the server is behind Tailscale)

If `SSH_HOST` is a Tailscale IP (`100.x.x.x`) rather than a public IP, the
GitHub Actions runner — which lives on the public internet — can't reach it
directly. The deploy workflow first joins your tailnet as a temporary,
throwaway node (`tailscale/github-action`), then the SSH step can reach the
server over Tailscale exactly like your own machine does.

Generate a key at the
[Tailscale admin console](https://login.tailscale.com/admin/settings/keys) →
Generate auth key. A **reusable, ephemeral** key is the right choice here —
ephemeral so the throwaway CI node deregisters itself after each run instead
of piling up in your tailnet's device list, reusable so the same key works
for every deploy rather than a one-shot key you'd have to regenerate each
time. Save the generated key for the secret below (it's only shown once).

### 4. GitHub repo: create the `production` environment

Repo → Settings → Environments → New environment → name it `production`.
This is where the deploy workflow's secrets live, scoped so the build
workflow (`ci.yml`) never sees them. Optionally tick "Required reviewers" and
add yourself, so triggering the workflow still needs a manual approval click
— an extra confirmation before anything reaches the server.

Inside that environment, add **secrets**:

| Name | Value |
|---|---|
| `SSH_HOST` | server's Tailscale (or public) IP address |
| `SSH_USER` | the SSH user from step 2 |
| `SSH_PRIVATE_KEY` | contents of `nfl_manager_deploy_key` (private key) |
| `DEPLOY_PATH` | `/opt/nfl-manager` |
| `TAILSCALE_AUTHKEY` | the key from step 3 — skip if the server has a public IP instead |

### 5. GitHub repo: repository variable (used by `ci.yml`, not environment-scoped)

Repo → Settings → Secrets and variables → Actions → Variables tab:

| Name | Value |
|---|---|
| `API_BASE_URL` | the address *players' browsers* will use to reach the API — see the Tailscale note below before picking this. Update this and re-push once you have a domain. |

> **If the server only has a Tailscale IP (no public IP/port-forward):** the
> app is only reachable to devices on your tailnet, same as SSH is right
> now — `API_BASE_URL` should then be `http://100.78.45.17:8002`, and only
> people on your Tailscale network can play. That's fine for personal/private
> use. If you want it reachable from the open internet later, that needs a
> public IP or port-forward on the server (or Tailscale Funnel) in addition
> to what this doc sets up — the Tailscale step above only gets the *deploy*
> traffic in, not player traffic.

### 6. Make the GHCR images pullable from the server

After the first push to `main` triggers `ci.yml`, two packages appear under
the GitHub account: `nfl-manager-backend` and `nfl-manager-frontend`. New
GHCR packages default to **private**, so the server needs access. Easiest
path: open each package → Package settings → Change visibility → Public.
(Alternative: `docker login ghcr.io` on the server with a personal access
token that has `read:packages`.)

### 7. First deploy

Either trigger "Deploy to production" from the Actions tab, or run it
manually once from `/opt/nfl-manager` on the server:

```bash
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

The app is then reachable at `http://<server-ip>` (frontend, port 80) and
`http://<server-ip>:8002` (API). The backend listens on 8000 *inside* its
container, mapped to host port 8002 in `docker-compose.prod.yml` — plain
8000 was already taken on the server by another service (Portainer).

**Immediately after this first `up -d`, before anyone registers/plays**, run
the player import scripts:

```bash
docker compose -f docker-compose.prod.yml exec backend python -m app.scripts.import_nfl_players
docker compose -f docker-compose.prod.yml exec backend python -m app.scripts.import_college_players
```

This matters because the backend seeds every AI bot team **on its very
first startup**, and team creation only pulls real players from whatever's
already been imported — it never retroactively backfills a team that
missed out. Start the server before importing, and every bot team (and any
human team claimed before the import finishes) is permanently stuck with
an empty roster, because nothing re-checks an already-created team later.

If this was already missed and teams are showing up empty, it's still
fixable without losing any accounts/progress:

```bash
docker compose -f docker-compose.prod.yml exec backend python -m app.scripts.import_nfl_players
docker compose -f docker-compose.prod.yml exec backend python -m app.scripts.import_college_players
docker compose -f docker-compose.prod.yml exec backend python -m app.scripts.backfill_missing_rosters
```

`backfill_missing_rosters` only touches teams that currently have zero
players — it never deletes or reassigns anything from a team that already
has a roster, so it's safe to run any time, including on a server with real
registered users.

## After setup

- Push to `main` → images build automatically, server untouched.
- Happy with what you tested locally → Actions tab → "Deploy to production" →
  Run workflow (leave `latest`, or type a specific SHA) → that build goes
  live.

## Rollback

Images are also tagged with the commit SHA
(`ghcr.io/.../nfl-manager-backend:<sha>`). To roll back, run "Deploy to
production" again with that older SHA as the `image_tag` input — no server
access needed.

## Later: adding a domain / HTTPS

Once you point a domain at the server, put a reverse proxy (Caddy or nginx +
certbot) in front of ports 80/8002 for TLS, and update the `API_BASE_URL`
GitHub Actions variable to the new `https://` URL, then push to `main` and
redeploy to rebuild the frontend with the new API base.
