# Dev Cluster Feasibility Analysis

## Executive Summary

**All 26 apps can be developed inside Docker containers / Kubernetes pods.** Every single
repo already has either Dockerfiles, docker-compose files, or devcontainer configs. 10/26
have official `.devcontainer` setups. The proposed agent workflow (clone -> modify -> rebuild
with Depot -> test in K8s dev cluster) is feasible for all apps.

## Cluster Context

- **Current cluster**: `htech-prod-oidc` (K3s v1.33.0, 3 worker nodes on AWS)
- **Sandbox created**: `dev-sandbox` namespace with `dev-workbench` pod
- **All 26 repos cloned** at `/repos/` inside the pod (shallow, ~5GB total)

---

## Per-App Docker/Dev Analysis

### Tier 1: Excellent Docker Dev Support (purpose-built dev containers)

| App | Dockerfile | Compose | DevContainer | Dev Approach | Hot-Reload in Docker |
|-----|-----------|---------|-------------|-------------|---------------------|
| **Ghost** | `docker/ghost-dev/Dockerfile` | `compose.dev.yaml` (MySQL, Redis, Mailpit, Caddy) | Yes | Docker-first | Yes (Nodemon) |
| **Twenty CRM** | `Dockerfile` w/ `twenty-app-dev` target | `docker-compose.dev.yml` | No | Docker | Yes |
| **Chatwoot** | `docker/Dockerfile` (multi-stage) | `docker-compose.yaml` + `.devcontainer/` | Yes | Docker or devcontainer | Yes (Rails + Webpacker) |
| **OpenProject** | `docker/dev/backend/Dockerfile` (dev targets) | Root `docker-compose.yml` | No | Docker-first recommended | Yes (Rails + Angular live-reload) |
| **Plane** | `Dockerfile.dev` per app (web, api, admin, space, live) | `docker-compose-local.yml` | No | Docker with dev Dockerfiles | Yes (Next.js + Django) |
| **BookStack** | `dev/docker/Dockerfile` (PHP+Xdebug) | Root `docker-compose.yml` (dev-focused) | No | Docker recommended | Yes (PHP + Vite) |
| **EasyAppointments** | `docker/php-fpm/Dockerfile` (w/ Xdebug) | Root `docker-compose.yml` (8 services) | No | Docker recommended | Yes |
| **Listmonk** | `dev/app.Dockerfile` | `dev/docker-compose.yml` | Yes | Docker for dev | Yes (Go + JS watchers) |
| **PrestaShop** | `.docker/Dockerfile` (PHP+Apache+Node) | `docker-compose.yml` + MariaDB variant | No | Docker | Yes |
| **Huly** | Dockerfiles per pod (~15 services) | `dev/docker-compose.yaml` + variants | No | Docker + Rush build system | Partial (rebuild required) |

### Tier 2: Good Docker Support (devcontainer or compose, usable for dev)

| App | Dockerfile | Compose | DevContainer | Dev Approach | Hot-Reload in Docker |
|-----|-----------|---------|-------------|-------------|---------------------|
| **Mastodon** | Root `Dockerfile` (prod) + `.devcontainer/Dockerfile` | `.devcontainer/compose.yaml` | Yes | Devcontainer recommended | Yes (Rails + Webpack) |
| **Zammad** | `Dockerfile` (prod) | `.devcontainer/` (5 variants: default, LDAP, Ollama, mailserver, Selenium) | Yes | Devcontainer (rich variants) | Yes (Rails) |
| **Nextcloud** | `.devcontainer/Dockerfile` (PHP 8.4+Apache) | `.devcontainer/docker-compose.yml` (4 services) | Yes | VS Code devcontainer | Yes (PHP) |
| **Kanboard** | Root `Dockerfile` | Compose for mysql/sqlite/postgres | Yes | Devcontainer or Docker | Yes (PHP) |
| **Metabase** | Root `Dockerfile` + `dev/docker-compose.yml` | `dev/docker-compose.yml` | Yes | **Native preferred** (mise + bun) | Native hot-reload only |
| **Discourse** | No Dockerfile (uses `discourse/discourse_dev` image) | None (uses `bin/docker/boot_dev` script) | Yes | Docker via helper scripts | Yes |
| **Rocket.Chat** | `.devcontainer/Dockerfile` | `docker-compose-local.yml` | Yes | Devcontainer or native | Yes (Meteor) |
| **ERPNext** | In separate `frappe/frappe_docker` repo | `compose.yaml` + `devcontainer-example/` | Yes (separate repo) | Docker via frappe_docker | Yes (Bench + live-reload) |
| **Grafana** | Root `Dockerfile` + devenv Dockerfiles | `devenv/*/docker-compose.yaml` | No | **Native preferred** (Go + bun) | Native hot-reload |
| **OpenCart** | `docker/apache/Dockerfile`, `docker/php/Dockerfile` | Root `docker-compose.yml` | No | Docker + Makefile | Yes |

### Tier 3: Basic Docker Support (prod Dockerfiles, needs adaptation for dev)

| App | Dockerfile | Compose | DevContainer | Notes |
|-----|-----------|---------|-------------|-------|
| **NocoDB** | No dev Dockerfile | `docker-compose/` (multiple backends) | No | Compose files for deployment; dev is native (Node.js) |
| **Plausible** | `Dockerfile` (prod) | None | No | Native Elixir/Phoenix dev; Docker for deployment only |
| **Mattermost** | Build env Dockerfiles only | `server/docker-compose.yaml` | No | Compose for deps; app runs native (Go + Node) |
| **Invoice Ninja** | Dockerfile (deployment) | None official | No | Laravel; Docker for self-hosting, dev is native |
| **Bagisto** | None (uses Laravel Sail images) | `docker-compose.yml` (Sail) | No | Laravel Sail provides dev containers |
| **Taiga** | None (pulls pre-built images) | `docker-compose.yml` | No | Docker Compose for deployment; dev in separate repos |
| **Zammad** | `Dockerfile` (prod/CI) | `.devcontainer/` variants | Yes | Multiple devcontainer flavors |

---

## Proposed Dev Cluster Architecture

```
                    +--------------------------+
                    |   Agent Orchestrator     |
                    |   (Claude CLI / coder)   |
                    +-----------+--------------+
                                |
                    +-----------v--------------+
                    |    K8s Dev Cluster (AWS)  |
                    |    Namespace: dev-agents  |
                    |                          |
  +-----------------+    +-----------------+   |
  | Agent Pod 1     |    | Agent Pod 2     |   |
  | - git clone     |    | - git clone     |   |
  | - code changes  |    | - code changes  |   |
  | - depot build   |    | - depot build   |   |
  +---------+-------+    +---------+-------+   |
            |                      |           |
  +---------v-------+    +---------v-------+   |
  | App Instance 1  |    | App Instance 2  |   |
  | (rebuilt image)  |    | (rebuilt image)  |   |
  | + deps (DB,etc) |    | + deps (DB,etc) |   |
  +-----------------+    +-----------------+   |
                    |                          |
                    | Namespace: dev-apps      |
                    +--------------------------+
```

### Workflow per Improvement Cycle

1. **Clone**: Agent pod clones the app's source repo
2. **Modify**: Agent (Claude CLI) edits source code to implement the improvement
3. **Build**: `depot build` rebuilds the Docker image (fast, cached, remote builders)
4. **Deploy**: `kubectl set image` swaps the running app to the new image tag
5. **Test**: UserSim browser agents verify the UX improvement was achieved
6. **Report**: Diff + before/after screenshots + UX scores

### Key Design Decisions

#### Why Depot for Image Builds
- Remote builders = no Docker-in-Docker / privileged pods needed
- Layer caching across builds = fast rebuilds (seconds for code-only changes)
- `depot build --push` directly to a registry from within K8s pods
- Works great in CI-like K8s pods (just needs `depot` CLI + auth token)

#### Registry Strategy
- Use **ECR** (already on AWS) or **GHCR** for built images
- Tag convention: `<app>-dev:<git-sha-short>` (e.g., `chatwoot-dev:a1b2c3d`)
- Agent pods push images; app pods pull them

#### Dev App Namespacing
- Each app improvement attempt gets its own namespace: `dev-<app>-<run-id>`
- Includes the app + all dependencies (DB, Redis, etc.) from existing K8s manifests
- Torn down after testing completes

---

## Docker Dev Readiness Summary

| Category | Count | Apps |
|----------|-------|------|
| **Ready for Docker dev** (Dockerfile.dev or dev compose) | 10 | Ghost, Twenty, Chatwoot, OpenProject, Plane, BookStack, EasyAppointments, Listmonk, PrestaShop, Huly |
| **Devcontainer available** | 10 | Ghost, Mastodon, Zammad, Nextcloud, Kanboard, Metabase, Discourse, Rocket.Chat, Chatwoot, Listmonk |
| **Compose available** (deploy or dev) | 24 | All except Invoice Ninja, Plausible |
| **Needs custom dev Dockerfile** | 4 | NocoDB, Plausible, Invoice Ninja, Taiga |
| **Native dev recommended by project** | 4 | Metabase, Grafana, Mattermost, Plausible |

### Bottom Line

- **22/26 apps** can be developed in Docker with their existing Dockerfiles/compose files
- **4 apps** (NocoDB, Plausible, Invoice Ninja, Taiga) need a simple dev Dockerfile written
  (but their prod images can serve as a starting point)
- **All 26** can work in the proposed K8s dev cluster with Depot builds -- for the "native
  dev preferred" apps, the agent just needs to modify source, build the prod Dockerfile, and
  deploy (no hot-reload needed since agents work in batch, not interactively)

## Detailed Per-App DeepWiki Findings

### Ghost (TryGhost/Ghost)
- **Dev Dockerfile**: `docker/ghost-dev/Dockerfile` (with hot-reload via Nodemon)
- **Compose**: `compose.dev.yaml` (MySQL, Redis, Mailpit, Caddy gateway)
- **Dev mode**: Hybrid recommended -- backend in Docker with bind-mounted source, frontend native with HMR through Caddy proxy. Full Docker Mode also works.
- **Deps**: Node.js 22.18.0, Yarn, Docker

### Twenty CRM (twentyhq/twenty)
- **Dev Dockerfile**: `packages/twenty-docker/twenty/Dockerfile` with `twenty-app-dev` build target (bundles PostgreSQL + Redis)
- **Compose**: `packages/twenty-docker/docker-compose.yml`
- **Dev mode**: Docker is the officially recommended method. `yarn twenty dev` watches source files.
- **Deps**: Node.js 24+, PostgreSQL 16, Redis

### Chatwoot (chatwoot/chatwoot)
- **Dev Dockerfile**: `docker/Dockerfile` (multi-stage), `.devcontainer/Dockerfile`
- **Compose**: `docker-compose.yaml` (Rails, Sidekiq, Vite, Postgres, Redis, Mailhog)
- **Dev mode**: Docker Compose primary. Vite HMR on port 3036 for frontend.
- **Deps**: Ruby 3.4.4, Node.js 24.13.0, PNPM 10.2.0, PostgreSQL 16 with pgvector

### OpenProject (opf/openproject)
- **Dev Dockerfile**: `docker/dev/backend/Dockerfile` with `develop` and `test` targets
- **Compose**: Root `docker-compose.yml` (backend, frontend, Postgres, Memcached, Selenium)
- **Dev mode**: Docker-first. Rails auto-reloads via volume mounts; Angular `ng serve` with live-reload.
- **Deps**: Ruby 3.4.7, Node.js, PostgreSQL, Memcached

### Plane (makeplane/plane)
- **Dev Dockerfiles**: `apps/*/Dockerfile.dev` for each service (api, web, admin, space, live)
- **Compose**: `docker-compose-local.yml` (Postgres 15.7, Valkey/Redis, RabbitMQ, MinIO, Django API, Celery)
- **Dev mode**: Hybrid -- Docker for backend + infra, native `pnpm dev` for frontends. API hot-reloads via volume mounts. 12GB RAM minimum.
- **Deps**: Docker, Node.js 22.18+, pnpm 10.32+

### BookStack (BookStackApp/BookStack)
- **Dev Dockerfile**: `dev/docker/Dockerfile` (PHP 8.3-apache + Xdebug)
- **Compose**: Root `docker-compose.yml` (PHP, Node 22-alpine, MySQL 8.4)
- **Dev mode**: Docker Compose. Node service runs `npm run watch` (Sass + esbuild watcher).
- **Deps**: PHP 8.2+, Node.js 22+, MySQL 8.4

### EasyAppointments (alextselegidis/easyappointments)
- **Dev Dockerfile**: `docker/php-fpm/Dockerfile` (PHP 8.4-fpm + Xdebug + Node)
- **Compose**: Root `docker-compose.yml` (8 services: php-fpm, nginx, mysql, phpmyadmin, mailpit, swagger-ui, baikal, openldap)
- **Dev mode**: Docker-only development environment. `npm start` runs Gulp file watcher.
- **Deps**: PHP 8.2+, MySQL 8.0, Node.js

### Listmonk (knadh/listmonk)
- **Dev Dockerfile**: `dev/app.Dockerfile`
- **Compose**: `dev/docker-compose.yml` (PostgreSQL, Mailhog, frontend, backend)
- **Dev mode**: Docker Compose. Frontend hot-reloads via Yarn watcher. Backend requires rebuild after Go changes.
- **Deps**: Go, Node.js, Yarn, PostgreSQL

### PrestaShop (PrestaShop/PrestaShop)
- **Dev Dockerfile**: `.docker/Dockerfile` (PHP 8.1 + Apache + Node.js 20)
- **Compose**: `docker-compose.yml` (PrestaShop, MySQL, MailDev), MariaDB variant available
- **Dev mode**: Docker via `make docker-start`. Webpack watch mode via `npm run watch`.
- **Deps**: PHP 8.1, Node.js 20, MySQL/MariaDB

### Huly (hcengineering/platform)
- **Dockerfiles**: Per-service Dockerfiles in `pods/*/Dockerfile` (~15 services)
- **Compose**: `dev/docker-compose.yaml` (40+ services), `dev/docker-compose.min.yaml` (minimal)
- **Dev mode**: Hybrid -- `rush docker:up` for backend services, native `rushx dev-server` for frontend with live-reload. `rush build:watch` for continuous recompilation.
- **Deps**: Node.js 20.11+, Rush.js, pnpm, Docker, GitHub Packages token

### Mastodon (mastodon/mastodon)
- **Dev Dockerfile**: `.devcontainer/Dockerfile` (Ruby devcontainer image)
- **Compose**: `.devcontainer/compose.yaml` (app, Postgres 14, Redis 7, Elasticsearch, LibreTranslate)
- **Dev mode**: VS Code DevContainer / Codespaces recommended. Puma auto-reloads Rails; Vite HMR on port 3036.
- **Deps**: Ruby 4.0.2, Node.js 24, PostgreSQL 14, Redis 7

### Zammad (zammad/zammad)
- **Dockerfile**: `Dockerfile` (production/CI)
- **DevContainers**: `.devcontainer/` with 5 variants (default, LDAP, Ollama, mailserver, Selenium)
- **Dev mode**: Native recommended (`forego start`), but devcontainers fully work. Hot-reload via `pnpm dev:https`.
- **Deps**: Ruby (RVM), Node.js (NVM), pnpm, PostgreSQL, Redis, Elasticsearch

### Nextcloud (nextcloud/server)
- **Dev Dockerfile**: `.devcontainer/Dockerfile` (Ubuntu, PHP 8.4, Apache, Xdebug)
- **Compose**: `.devcontainer/docker-compose.yml` (app, PostgreSQL, Adminer, MailHog)
- **Dev mode**: VS Code DevContainer is the canonical path. Xdebug on port 9003.
- **Deps**: PHP 8.4 with many extensions, Composer, Node.js (via nvm)

### Kanboard (kanboard/kanboard)
- **Dockerfile**: Root `Dockerfile`
- **DevContainer**: `.devcontainer/`
- **Dev mode**: Docker or devcontainer. PHP is interpreted per-request, so volume mounts = instant changes.
- **Deps**: PHP, lightweight stack (no Node/Gulp -- removed in recent versions)

### Metabase (metabase/metabase)
- **Dockerfiles**: Root `Dockerfile` (prod), `.devcontainer/Dockerfile`
- **Compose**: `dev/docker-compose.yml`
- **Dev mode**: **Native preferred** -- `./bin/dev-install` (mise for JDK 21, Node 22, Clojure, Bun, Babashka). `bun run dev` for hot-reload. Devcontainer also works with HMR.
- **Deps**: JDK 21, Node.js 22, Clojure, Bun 1.3.7

### Discourse (discourse/discourse)
- **Dockerfile**: None in main repo; uses prebuilt `discourse/discourse_dev:release` image
- **DevContainer**: `.devcontainer/devcontainer.json`
- **Dev mode**: Docker via `bin/docker/boot_dev`. Source volume-mounted for instant reload. Ember live-reload via `d/ember-cli`.
- **Deps**: Ruby 3.4+, PostgreSQL 13+, Redis 7+, Node.js, pnpm

### Rocket.Chat (RocketChat/Rocket.Chat)
- **Dockerfiles**: Production only (`apps/meteor/.docker/Dockerfile.alpine`)
- **DevContainer**: `.devcontainer/Dockerfile`
- **Dev mode**: **Native preferred** -- `yarn dev` with Meteor hot-reload. Turbo monorepo orchestration.
- **Deps**: Node.js 22.16.0 (Volta), Yarn 4.12.0, MongoDB 4.4-8.0, Deno

### ERPNext (frappe/erpnext)
- **Dockerfiles**: In separate `frappe/frappe_docker` repo (cloned as `erpnext` in sandbox)
- **Compose**: `compose.yaml` in frappe_docker, `devcontainer-example/`
- **Dev mode**: `frappe-bench` CLI (native) or Docker via frappe_docker. `bench start` has built-in file watchers.
- **Deps**: Python, Node.js, MariaDB/PostgreSQL, Redis

### Grafana (grafana/grafana)
- **Dockerfiles**: Root `Dockerfile` (prod), `devenv/frontend-service/grafana-fs-dev.dockerfile`
- **Compose**: `devenv/frontend-service/docker-compose.yaml` (Grafana, Postgres, Nginx, Prometheus, Loki, Tempo)
- **Dev mode**: **Native preferred** -- `make run` (backend via `air`) + `yarn start` (frontend). Docker via Tilt also fully supported.
- **Deps**: Go ~1.25-1.26, Node.js 24, Yarn 4.x, Docker, Tilt

### OpenCart (opencart/opencart)
- **Dockerfiles**: `docker/apache/Dockerfile`, `docker/php/Dockerfile`, `docker/nginx/Dockerfile`
- **Compose**: Root `docker-compose.yml` with Makefile (`make init`, `make build`, `make up`)
- **Dev mode**: Docker Compose recommended. PHP interpreted per-request = instant changes via volume mounts.
- **Deps**: PHP 8.2-8.4, MySQL, optional Redis/Memcached

### NocoDB (nocodb/nocodb)
- **Dockerfiles**: None for dev
- **Compose**: `docker-compose/` directory with multiple DB backend variants
- **Dev mode**: **Native** -- `pnpm run watch:run` (NestJS/rspack backend), `pnpm run dev` (Nuxt 3 frontend). Docker for deployment only.
- **Deps**: pnpm, Node.js

### Plausible (plausible/analytics)
- **Dockerfile**: `Dockerfile` (production only)
- **Compose**: None
- **Dev mode**: **Native Elixir/Phoenix** -- `mix phx.server` with `phoenix_live_reload`. Docker not supported for dev.
- **Deps**: Elixir, Erlang/OTP, Node.js, PostgreSQL, ClickHouse

### Mattermost (mattermost/mattermost)
- **Dockerfiles**: Build environment only (`server/build/Dockerfile.buildenv`)
- **Compose**: `server/docker-compose.yaml` (Postgres, MinIO, OpenSearch, LDAP -- deps only)
- **Dev mode**: **Native hybrid** -- Docker for deps, app runs native. `make run-server` + `make run-client` with webpack hot-reload.
- **Deps**: Go 1.24.13, Node.js 18+, Docker

### Invoice Ninja (invoiceninja/invoiceninja)
- **Dockerfile**: Yes (self-hosting focused)
- **Compose**: None official
- **Dev mode**: **Native Laravel** -- `git clone`, `composer install`, `.env`, `php artisan migrate`. No Docker dev workflow provided.
- **Deps**: PHP 8.1+, MySQL/PostgreSQL, Redis, Flutter Web (frontend)

### Bagisto (bagisto/bagisto)
- **Dockerfile**: None (uses Laravel Sail images)
- **Compose**: `docker-compose.yml` (Laravel Sail: MySQL 8, Redis, Elasticsearch, Kibana, Mailpit)
- **Dev mode**: Laravel Sail in Docker. `npm run dev` starts Vite HMR.
- **Deps**: PHP 8.3+, Node.js 18+, Composer 2.x

### Taiga (taigaio/taiga-docker)
- **Dockerfiles**: None (pulls pre-built images from Docker Hub)
- **Compose**: `docker-compose.yml` + `docker-compose-inits.yml`
- **Dev mode**: **Deployment only** -- no source mounts or hot-reload. Dev requires working in separate upstream repos (taiga-back, taiga-front).
- **Deps**: Docker 19.03+, Docker Compose

---

## Agent Build Strategy by App Type

For the proposed dev cluster, each app falls into one of three build strategies:

### Strategy A: Use existing dev Dockerfile (10 apps)
Ghost, Twenty, Chatwoot, OpenProject, Plane, BookStack, EasyAppointments, Listmonk, PrestaShop, Huly

Agent modifies source -> `depot build -f Dockerfile.dev --target dev` -> push to ECR -> deploy

### Strategy B: Use prod Dockerfile after code changes (12 apps)
Mastodon, Zammad, Nextcloud, Kanboard, Metabase, Discourse, Rocket.Chat, ERPNext, Grafana, OpenCart, Bagisto, Mattermost

Agent modifies source -> `depot build -f Dockerfile` -> push to ECR -> deploy
(Prod Dockerfiles already build the full app -- agent changes are included in the build)

### Strategy C: Write a thin dev Dockerfile (4 apps)
NocoDB, Plausible, Invoice Ninja, Taiga

Agent writes a simple Dockerfile based on the app's runtime (Node/Elixir/PHP/Python) ->
copies modified source -> `depot build` -> push -> deploy

---

## Repos Cloned in K8s Sandbox

All repos live at `/repos/<name>` in the `dev-workbench` pod (`dev-sandbox` namespace):

```
bagisto, bookstack, chatwoot, discourse, easyappointments, erpnext,
ghost, grafana, huly, invoiceninja, kanboard, listmonk, mastodon,
mattermost, metabase, nextcloud, nocodb, opencart, openproject,
plane, plausible, prestashop, rocketchat, taiga, twenty, zammad
```
