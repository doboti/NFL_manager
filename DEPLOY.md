# Deployment

Push to `main` → GitHub Actions builds the backend and frontend Docker images,
pushes them to GitHub Container Registry (GHCR), then SSHes into the server
and runs `docker compose pull && up -d`. The backend container runs
`alembic upgrade head` on every start, so DB migrations ship automatically
with each deploy.

## One-time setup

### 1. Server: deploy directory and secrets

```bash
mkdir -p /opt/nfl-manager
cd /opt/nfl-manager
# copy docker-compose.prod.yml and .env.example from the repo here (scp or paste)
cp .env.example .env
# edit .env: set POSTGRES_PASSWORD and JWT_SECRET_KEY to real random values
# generate each with: openssl rand -hex 32
```

### 2. Server: dedicated SSH key for CI

On your own machine (not the server):

```bash
ssh-keygen -t ed25519 -f nfl_manager_deploy_key -N ""
```

Append `nfl_manager_deploy_key.pub` to `~/.ssh/authorized_keys` on the server
for the user that will run the deploy (needs docker permissions). Keep
`nfl_manager_deploy_key` (private half) for the GitHub secret below.

### 3. GitHub repo settings → Secrets and variables → Actions

**Secrets:**
| Name | Value |
|---|---|
| `SSH_HOST` | server's IP address |
| `SSH_USER` | the SSH user from step 2 |
| `SSH_PRIVATE_KEY` | contents of `nfl_manager_deploy_key` (private key) |
| `DEPLOY_PATH` | `/opt/nfl-manager` |

**Variables:**
| Name | Value |
|---|---|
| `API_BASE_URL` | `http://<server-ip>:8000` — baked into the frontend build so the browser knows where the API is. Update this and re-push once you have a domain. |

### 4. Make the GHCR images pullable from the server

After the first push to `main` triggers a build, two packages appear under
the GitHub account: `nfl-manager-backend` and `nfl-manager-frontend`. New
GHCR packages default to **private**, so the server needs access. Easiest
path: open each package → Package settings → Change visibility → Public.
(Alternative: `docker login ghcr.io` on the server with a personal access
token that has `read:packages`.)

### 5. First deploy

Either push to `main` and let the Action do it, or run it manually once from
`/opt/nfl-manager` on the server:

```bash
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

The app is then reachable at `http://<server-ip>` (frontend, port 80) and
`http://<server-ip>:8000` (API).

## After setup

Every push to `main` redeploys automatically — no manual server steps needed.

## Rollback

Images are also tagged with the commit SHA (`ghcr.io/.../nfl-manager-backend:<sha>`).
To roll back, SSH into the server, edit `docker-compose.prod.yml` to pin the
`image:` lines to a known-good SHA instead of `:latest`, then
`docker compose -f docker-compose.prod.yml up -d`.

## Later: adding a domain / HTTPS

Once you point a domain at the server, put a reverse proxy (Caddy or nginx +
certbot) in front of ports 80/8000 for TLS, and update the `API_BASE_URL`
GitHub Actions variable to the new `https://` URL, then re-push to rebuild
the frontend with the new API base.
