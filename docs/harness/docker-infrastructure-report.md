# Infrastructure Report: Self-Hosting 28 Open Source Web Applications via Docker

> Generated 2026-05-09. Requirements marked **(est.)** are estimates based on tech stack; all others come from official documentation or community-validated sources.

---

## Table of Contents

1. [E-Commerce](#e-commerce)
2. [CRM & Business](#crm--business)
3. [Project Management](#project-management)
4. [Team Communication](#team-communication)
5. [CMS & Publishing](#cms--publishing)
6. [Analytics](#analytics)
7. [Customer Support](#customer-support)
8. [Other](#other)
9. [Summary Table](#summary-table)
10. [Aggregate Resource Estimates](#aggregate-resource-estimates)

---

## E-Commerce

### 1. OpenCart (PHP)

| Aspect | Details |
|---|---|
| **Docker Image** | No official Docker Hub image from `opencart/`. Community images: `byjg/opencart`, `aamservices/opencart`. The [official repo](https://github.com/opencart/opencart) includes a `docker-compose.yml` at the root. |
| **Compose File** | Yes -- `docker-compose.yml` in the [official GitHub repo](https://github.com/opencart/opencart/blob/master/docker-compose.yml). Uses MariaDB. |
| **Min RAM** | 512 MB **(est.)** -- PHP/Apache stack is lightweight. The installer + MariaDB together run comfortably in 512 MB. |
| **Disk** | ~500 MB base image + MariaDB. Budget ~2 GB for a demo with product images. |
| **Seed Data** | The OpenCart installer includes sample product data by default (demo categories, products, and manufacturers via the SQL install scripts). After `docker-compose up`, run the web installer at `http://localhost/install/` and sample data is loaded automatically. Default admin: `admin` / `admin`. |

**Quick Start:**
```bash
git clone https://github.com/opencart/opencart.git && cd opencart
docker-compose up -d
# Visit http://localhost and complete the install wizard
```

---

### 2. Spree Commerce (Ruby on Rails)

| Aspect | Details |
|---|---|
| **Docker Image** | `spreecommerce/spree` on Docker Hub (older 3.x). For modern Spree 5+, use the [spree_starter](https://github.com/spree/spree_starter) template which includes a production-ready `Dockerfile`. Build your own image. |
| **Compose File** | Not in the main `spree/spree` repo. The `spree_starter` repo has a Dockerfile; compose configs are available via community templates (e.g., `Vicky1239/docker-spree-app`). |
| **Min RAM** | 2 GB -- Rails apps with asset compilation need adequate memory; the official deployment guide recommends at least 2 GB. |
| **Disk** | ~1.5 GB for Ruby/Rails image + PostgreSQL. Budget ~3 GB for a demo with sample product images. |
| **Seed Data** | Yes -- excellent built-in seed data. Run `bundle exec rake spree_sample:load` (or `docker-compose run web bundle exec rake spree_sample:load`) to load sample products, categories, and images. `rails db:seed` creates the admin user. |

**Quick Start:**
```bash
git clone https://github.com/spree/spree_starter.git && cd spree_starter
# Build and run per spree_starter README
docker-compose run web rails db:create db:migrate db:seed
docker-compose run web bundle exec rake spree_sample:load
```

---

### 3. PrestaShop (PHP/Symfony)

| Aspect | Details |
|---|---|
| **Docker Image** | **`prestashop/prestashop`** on [Docker Hub](https://hub.docker.com/r/prestashop/prestashop/). Official. Tags: `latest`, `8`, `8-fpm`, `9`, etc. |
| **Compose File** | Yes -- reference `docker-compose.yml` in the [official Docker repo](https://github.com/PrestaShop/docker) and [PrestaShop developer docs](https://devdocs.prestashop-project.org/9/basics/installation/environments/docker/). |
| **Min RAM** | 2 GB -- officially recommended for PrestaShop + MySQL 8.0. |
| **Disk** | ~800 MB base image + MySQL. Budget ~3 GB with demo products and images. |
| **Seed Data** | Yes -- excellent. Set `PS_INSTALL_AUTO=1` and `PS_DEMO_MODE=1` as environment variables. PrestaShop auto-installs with a full demo shop (sample products, categories, CMS pages). Default admin: `demo@prestashop.com` / `prestashop_demo`. |

**Quick Start:**
```yaml
# docker-compose.yml excerpt
services:
  prestashop:
    image: prestashop/prestashop:latest
    environment:
      PS_INSTALL_AUTO: "1"
      PS_DEMO_MODE: "1"
      PS_DOMAIN: "localhost:8080"
      DB_SERVER: mysql
    ports:
      - "8080:80"
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: prestashop
      MYSQL_DATABASE: prestashop
```

---

### 4. Bagisto (PHP/Laravel)

| Aspect | Details |
|---|---|
| **Docker Image** | **`webkul/bagisto`** on [Docker Hub](https://hub.docker.com/r/webkul/bagisto). All-in-one image (Nginx + PHP 8.3 FPM + MySQL 8.0 + Supervisor). |
| **Compose File** | Yes -- in the [bagisto/bagisto-docker](https://github.com/bagisto/bagisto-docker) repo. Also a simpler approach: just `docker run -d -p 80:80 webkul/bagisto:latest`. |
| **Min RAM** | 1 GB **(est.)** -- PHP/Laravel with bundled MySQL. 2 GB recommended for comfortable operation. |
| **Disk** | ~1.5 GB for the all-in-one image. Budget ~3 GB with sample data and uploads. |
| **Seed Data** | Partial. Migrations + seeders run on boot (sample categories are included). For demo products, use the official [laravel-data-faker](https://github.com/bagisto/laravel-data-faker) package. Default admin: `admin@example.com` / `admin123`. |

**Quick Start:**
```bash
docker run -d -p 80:80 -p 3306:3306 webkul/bagisto:latest
# Visit http://localhost
```

---

## CRM & Business

### 5. Twenty (TypeScript/React/Node)

| Aspect | Details |
|---|---|
| **Docker Image** | **`twentycrm/twenty`** on [Docker Hub](https://hub.docker.com/r/twentycrm/twenty). Official. |
| **Compose File** | Yes -- official `docker-compose.yml` downloadable from [docs.twenty.com](https://docs.twenty.com/developers/self-host/capabilities/docker-compose). Also a one-line install script available. |
| **Min RAM** | 2 GB minimum (official docs). Some sources recommend 4-8 GB for all containers (server + worker + PostgreSQL + Redis). |
| **Disk** | ~1.5 GB for images. Budget ~3 GB with demo data and PostgreSQL. |
| **Seed Data** | Yes -- Twenty creates default sample data (People, Companies, Opportunities records) on first workspace creation. The codebase distinguishes "demo-objects" (as on demo.twenty.com) vs "standard objects" for self-hosted installs. CSV import is also supported for bulk data. |

**Quick Start:**
```bash
bash <(curl -sL https://raw.githubusercontent.com/twentyhq/twenty/main/packages/twenty-docker/scripts/install.sh)
# Or manually: download docker-compose.yml and .env from the repo, then docker compose up -d
```

---

### 6. ERPNext (Python/Frappe)

| Aspect | Details |
|---|---|
| **Docker Image** | **`frappe/erpnext`** on Docker Hub. Official images maintained via [frappe/frappe_docker](https://github.com/frappe/frappe_docker). |
| **Compose File** | Yes -- `compose.yaml` (production) and `pwd.yml` (quick disposable demo) in the [frappe_docker](https://github.com/frappe/frappe_docker) repo. |
| **Min RAM** | 4 GB minimum (with swap). 2 GB is the absolute floor for a demo (`pwd.yml`). 8 GB+ recommended for production. |
| **Disk** | ~3-4 GB for all images (multiple containers: frontend, backend, worker, scheduler, Redis, MariaDB). Budget ~8 GB total. |
| **Seed Data** | Yes -- ERPNext's setup wizard includes a "Demo Setup" feature that creates a sample company with transactions, journal entries, and master data. Can be cleared via a "Clear Demo Data" button. The `pwd.yml` compose file provides a quick disposable demo environment. |

**Quick Start (demo):**
```bash
git clone https://github.com/frappe/frappe_docker.git && cd frappe_docker
docker compose -f pwd.yml up -d
# Visit http://localhost:8080 -- setup wizard creates demo data
```

---

### 7. Invoice Ninja (PHP/Laravel + Flutter web)

| Aspect | Details |
|---|---|
| **Docker Image** | **`invoiceninja/invoiceninja`** on [Docker Hub](https://hub.docker.com/r/invoiceninja/invoiceninja/). Debian-based image with Chrome for PDF generation. |
| **Compose File** | Yes -- in the [invoiceninja/dockerfiles](https://github.com/invoiceninja/dockerfiles) repo (branch `debian`). |
| **Min RAM** | 1 GB **(est.)** -- PHP/Laravel app. 2 GB recommended due to Chrome for PDF rendering. |
| **Disk** | ~1.5 GB for images (app + MySQL + Nginx). Budget ~3 GB with data. |
| **Seed Data** | Yes -- run `docker compose exec app php artisan ninja:create-test-data` to generate sample invoices, clients, and payments. Default login after seeding: `admin@example.com` / `password`. Without seeding, default: `admin@example.com` / `changeme!`. |

**Quick Start:**
```bash
git clone https://github.com/invoiceninja/dockerfiles.git -b debian && cd dockerfiles/debian
# Edit .env with APP_URL and generate APP_KEY
docker compose up -d
docker compose exec app php artisan ninja:create-test-data
```

---

## Project Management

### 8. Plane (Next.js/Django)

| Aspect | Details |
|---|---|
| **Docker Image** | Official images: `makeplane/plane-*` on Docker Hub. Multiple containers (web, API, worker, space, admin, live). |
| **Compose File** | Yes -- official install via [developers.plane.so](https://developers.plane.so/self-hosting/methods/docker-compose). Uses a setup script that generates the compose file. |
| **Min RAM** | 4 GB **(est.)** -- Requires PostgreSQL, Redis, RabbitMQ, MinIO, and optionally OpenSearch. The full stack is substantial. |
| **Disk** | ~3-4 GB for all images + MinIO storage. Budget ~6 GB total. |
| **Seed Data** | No built-in seed data. Projects and work items must be created manually or via the REST API (OAuth 2.0, typed SDKs in Node.js/Python). The UI is intuitive for quickly setting up demo projects. |

**Quick Start:**
```bash
# Official installer
curl -fsSL https://raw.githubusercontent.com/makeplane/plane/master/deploy/selfhost/install.sh | bash
```

---

### 9. Huly (TypeScript/Svelte)

| Aspect | Details |
|---|---|
| **Docker Image** | `hardcoreeng/front`, `hardcoreeng/workspace`, `hardcoreeng/collaborator`, and others. Published by hcengineering. |
| **Compose File** | Yes -- in the [hcengineering/huly-selfhost](https://github.com/hcengineering/huly-selfhost) repo. Run `./setup.sh` then `docker compose up -d`. |
| **Min RAM** | 4 GB minimum (official). Recommended: 16 GB for good performance. Stack includes MongoDB/CockroachDB, Elasticsearch, MinIO, Redpanda. |
| **Disk** | ~35 GB for the full stack in Docker (official figure including all WSL virtual disk). Budget at least 10 GB for a lean demo. |
| **Seed Data** | No built-in seed data command. Use the [Huly Import Tool](https://docs.huly.io/) with the Unified Import Format, or the Huly API Client (`huly-examples` repo) to programmatically create issues, projects, etc. Test scripts exist in the `tests` directory. |

**Quick Start:**
```bash
git clone https://github.com/hcengineering/huly-selfhost.git && cd huly-selfhost
./setup.sh
docker compose up -d
```

---

### 10. Taiga (Python/Django + Angular)

| Aspect | Details |
|---|---|
| **Docker Image** | Official images: `taigaio/taiga-back`, `taigaio/taiga-front`, `taigaio/taiga-events`, etc. |
| **Compose File** | Yes -- in the [taigaio/taiga-docker](https://github.com/taigaio/taiga-docker) repo. Uses 7 services: gateway, front, back, PostgreSQL, RabbitMQ, events, async. |
| **Min RAM** | 4 GB -- PostgreSQL ~1 GB, RabbitMQ ~1 GB, remaining services ~2 GB combined. |
| **Disk** | ~2-3 GB for all images. Budget ~5 GB total with data. |
| **Seed Data** | Yes -- built-in `sample_data` Django management command: `python manage.py sample_data` generates demo projects. Also supports import/export of JSON project dumps (can import from Trello, Jira, Asana, GitHub). |

**Quick Start:**
```bash
git clone https://github.com/taigaio/taiga-docker.git && cd taiga-docker
git checkout stable
# Edit .env with TAIGA_SECRET_KEY, TAIGA_SITES_DOMAIN, etc.
docker compose up -d
docker compose -f docker-compose.yml -f docker-compose-inits.yml run --rm taiga-manage createsuperuser
```

---

### 11. OpenProject (Ruby on Rails + Angular)

| Aspect | Details |
|---|---|
| **Docker Image** | **`openproject/openproject`** on Docker Hub. Official all-in-one and compose-based images. |
| **Compose File** | Yes -- [opf/openproject-docker-compose](https://github.com/opf/openproject-docker-compose) repo. Also a `docker-compose.yml` in the main [opf/openproject](https://github.com/opf/openproject/blob/dev/docker-compose.yml) repo. |
| **Min RAM** | 4 GB (official minimum for up to 200 users). Docker Compose specifically needs 4 GB; on macOS increase Docker Desktop VM to 4 GB+. Exit code 137 = OOM. |
| **Disk** | ~2 GB for images. Official recommendation: 20 GB free disk. Budget ~5 GB for a demo. |
| **Seed Data** | Yes -- **automatic**. The `openproject_seeder` service runs on first launch, creating demo projects with work packages, Gantt charts, and boards. Seeder code: `app/seeders/demo_data/project_seeder.rb`. Default admin: `admin` / `admin`. |

**Quick Start:**
```bash
git clone https://github.com/opf/openproject-docker-compose.git --depth=1 --branch=stable/17 openproject
cd openproject
docker compose up -d
# Wait a few minutes for seeder, then visit http://localhost:8080
```

---

## Team Communication

### 12. Rocket.Chat (TypeScript/Meteor)

| Aspect | Details |
|---|---|
| **Docker Image** | **`rocket.chat`** (official Docker Hub image: `hub.docker.com/_/rocket.chat`). Also `rocketchat/rocket.chat` on Docker Hub. |
| **Compose File** | Yes -- in the [RocketChat/rocketchat-compose](https://github.com/RocketChat/rocketchat-compose) repo. Modular compose files: `compose.yml`, `compose.database.yml`, `compose.traefik.yml`, `compose.monitoring.yml`. |
| **Min RAM** | 2 GB (for up to 500 users, 100 concurrent). 4 GB for bare-metal up to 1,000 users. |
| **Disk** | ~1.5 GB for images + MongoDB. Budget ~5 GB with media uploads. |
| **Seed Data** | No built-in sample conversations. Setup wizard creates the admin user and a `#general` channel. Content must be generated manually or via the Rocket.Chat REST API. |

**Quick Start:**
```bash
git clone --depth 1 https://github.com/RocketChat/rocketchat-compose.git && cd rocketchat-compose
# Edit .env (RELEASE, ROOT_URL, DOMAIN, etc.)
docker compose -f compose.database.yml -f compose.yml -f docker.yml up -d
```

---

### 13. Mattermost (Go + React)

| Aspect | Details |
|---|---|
| **Docker Image** | **`mattermost/mattermost-team-edition`** on [Docker Hub](https://hub.docker.com/r/mattermost/mattermost-team-edition). Also enterprise: `mattermost/mattermost-enterprise-edition`. |
| **Compose File** | Yes -- in the [mattermost/docker](https://github.com/mattermost/docker) repo. Contains `docker-compose.yml` with PostgreSQL and optional Nginx. |
| **Min RAM** | 2 GB (small teams up to 100 users). 4-8 GB for larger deployments. |
| **Disk** | ~1 GB for images + PostgreSQL. Budget ~3 GB with media. |
| **Seed Data** | No built-in demo data. Setup wizard creates first admin and team on initial launch. Mattermost has a `mattermost` CLI tool and REST API for bulk data operations; `mmctl` can create channels and users programmatically. |

**Quick Start:**
```bash
git clone https://github.com/mattermost/docker && cd docker
cp env.example .env
# Edit .env (DOMAIN, etc.)
docker compose up -d
```

---

## CMS & Publishing

### 14. Ghost (Node.js/Ember)

| Aspect | Details |
|---|---|
| **Docker Image** | **`ghost`** -- official Docker Hub image (`hub.docker.com/_/ghost`). Maintained by the Docker community. Supports amd64, arm64, arm32v7. |
| **Compose File** | Not in the main Ghost repo. Community compose files are widely available. [Ghost 6.0+ Docker tooling](https://docs.ghost.org/install/docker) is being previewed with official compose support. |
| **Min RAM** | 1 GB minimum. 2 GB recommended for production with MySQL. |
| **Disk** | ~500 MB for Ghost image + MySQL. Budget ~2 GB with themes and content images. |
| **Seed Data** | Partial. Ghost creates a default welcome post on first launch. For richer demo content, import JSON files from the [Ghost Forum demo content](https://forum.ghost.org/t/demo-content-for-testing-and-development/30771) or [Ghost-O-Matic](https://ghost-o-matic.com/ghost-site-demo-content/) via Ghost Admin > Labs > Import. |

**Quick Start:**
```bash
docker run -d --name ghost -p 2368:2368 ghost:latest
# Visit http://localhost:2368 (front) and http://localhost:2368/ghost (admin setup)
```

---

### 15. Discourse (Ruby on Rails/Ember)

| Aspect | Details |
|---|---|
| **Docker Image** | **`discourse/discourse`** -- managed via [discourse/discourse_docker](https://github.com/discourse/discourse_docker). Not a simple `docker pull`; uses a launcher script (`./launcher rebuild app`). |
| **Compose File** | Non-standard. Discourse uses its own `discourse_docker` launcher with YAML templates in `containers/app.yml`. A community-driven [docker-compose approach](https://meta.discourse.org/t/discourse-self-hosting-with-docker-compose/348855) exists but is not the official method. |
| **Min RAM** | 1 GB with swap (absolute minimum). 4 GB recommended (2 CPU cores). 8 GB for high-traffic. Real-world: 2 GB causes 502 errors under load. |
| **Disk** | ~2-3 GB for images + PostgreSQL + Redis. Budget ~5 GB for a demo with posts and uploads. |
| **Seed Data** | Minimal built-in. `rake db:seed_fu` loads structural seed data only (post action types, etc.), not sample content. For full demo content: load the `development-image.sql` dump from `pg_dumps/` or use the Discourse API to create topics/posts programmatically. |

**Quick Start:**
```bash
git clone https://github.com/discourse/discourse_docker.git && cd discourse_docker
cp samples/standalone.yml containers/app.yml
# Edit containers/app.yml with your domain, email, etc.
./launcher rebuild app
```

---

## Analytics

### 16. Metabase (Clojure/React)

| Aspect | Details |
|---|---|
| **Docker Image** | **`metabase/metabase`** on [Docker Hub](https://hub.docker.com/r/metabase/metabase). Official. |
| **Compose File** | Yes -- example `docker-compose.yml` in the [official docs](https://www.metabase.com/docs/latest/installation-and-operation/running-metabase-on-docker) with PostgreSQL backend. |
| **Min RAM** | 1 GB baseline + 2 GB per 20 concurrent users. JVM-based; set `JAVA_OPTS=-Xmx2g` for a small team. Practical minimum: 2 GB. |
| **Disk** | ~500 MB for image. Budget ~2 GB with PostgreSQL backend. |
| **Seed Data** | Yes -- **excellent, built-in**. Ships with a Sample Database (H2) containing Orders, People, Products, and Reviews tables. Also includes an "Examples" collection with pre-built questions and dashboards (e-commerce dashboard, revenue charts, etc.). Available immediately on first launch. |

**Quick Start:**
```bash
docker run -d -p 3000:3000 --name metabase metabase/metabase
# Visit http://localhost:3000 -- sample database and example dashboards included
```

---

### 17. Grafana (Go/React)

| Aspect | Details |
|---|---|
| **Docker Image** | **`grafana/grafana`** on [Docker Hub](https://hub.docker.com/r/grafana/grafana). Official. Also `grafana/grafana-oss` and `grafana/grafana-enterprise`. |
| **Compose File** | Not in the main repo, but the [official docs](https://grafana.com/docs/grafana/latest/setup-grafana/installation/docker/) provide compose examples. Provisioning via YAML files is the standard approach. |
| **Min RAM** | 512 MB reservation, 1 GB limit (typical container config). Grafana itself is lightweight (Go binary). |
| **Disk** | ~300 MB for image. Budget ~1 GB with provisioned dashboards and SQLite/PostgreSQL. |
| **Seed Data** | Yes via provisioning. Grafana supports [auto-provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/) of data sources and dashboards via YAML + JSON files mounted into `/etc/grafana/provisioning/`. Thousands of community dashboards at [grafana.com/grafana/dashboards/](https://grafana.com/grafana/dashboards/). No data sources ship built-in (you must connect Prometheus, InfluxDB, etc.). |

**Quick Start:**
```bash
docker run -d -p 3000:3000 --name grafana grafana/grafana
# Visit http://localhost:3000 -- default login admin/admin
```

---

### 18. Plausible Analytics (Elixir/React)

| Aspect | Details |
|---|---|
| **Docker Image** | **`plausible/analytics`** on [Docker Hub](https://hub.docker.com/r/plausible/analytics). Official Community Edition image. Also `ghcr.io/plausible/community-edition`. |
| **Compose File** | Yes -- in the [plausible/community-edition](https://github.com/plausible/community-edition) repo. Three services: Plausible, PostgreSQL, ClickHouse. |
| **Min RAM** | 2 GB (ClickHouse is the main consumer). 1 GB idle. Add ~1 GB if using MaxMind GeoLite2-City. CPU must support SSE 4.2 or NEON. |
| **Disk** | ~1 GB for images. Analytics data grows ~1 GB per million page views stored. Budget ~2 GB for a demo. |
| **Seed Data** | No built-in demo data. Plausible tracks real page views; to get a populated-looking instance, add the tracking script to a website and generate traffic (or use the Plausible API to send custom events). Setup wizard creates the first site on launch. |

**Quick Start:**
```bash
git clone -b v3.2.0 --single-branch https://github.com/plausible/community-edition plausible-ce
cd plausible-ce
# Edit .env (BASE_URL, SECRET_KEY_BASE)
docker compose up -d
```

---

## Customer Support

### 19. Chatwoot (Ruby on Rails/Vue)

| Aspect | Details |
|---|---|
| **Docker Image** | **`chatwoot/chatwoot`** on [Docker Hub](https://hub.docker.com/r/chatwoot/chatwoot). Official. Tags: `latest`, `v*`, `latest-ce` (community edition). |
| **Compose File** | Yes -- `docker-compose.production.yaml` in the [main repo](https://github.com/chatwoot/chatwoot/blob/develop/docker-compose.production.yaml). Services: Rails, Sidekiq, PostgreSQL (pgvector), Redis. |
| **Min RAM** | 4 GB (official production recommendation). 2 GB absolute minimum per some guides. |
| **Disk** | ~2 GB for images. Budget ~4 GB with PostgreSQL and file uploads. |
| **Seed Data** | No official seed command for demo conversations (requested in [GitHub Issue #3429](https://github.com/chatwoot/chatwoot/issues/3429)). Setup wizard creates the admin account and first inbox. Use the Chatwoot API to programmatically create sample conversations, or use FactoryBot in development mode. |

**Quick Start:**
```bash
# Download files from the Chatwoot repo
wget https://raw.githubusercontent.com/chatwoot/chatwoot/develop/docker-compose.production.yaml
wget https://raw.githubusercontent.com/chatwoot/chatwoot/develop/.env.example -O .env
# Edit .env, then:
docker compose -f docker-compose.production.yaml run --rm rails bundle exec rails db:chatwoot_prepare
docker compose -f docker-compose.production.yaml up -d
```

---

### 20. Zammad (Ruby on Rails)

| Aspect | Details |
|---|---|
| **Docker Image** | **`zammad/zammad-docker-compose`** on [Docker Hub](https://hub.docker.com/r/zammad/zammad-docker-compose). Multiple service images: `zammad-railsserver`, `zammad-websocket`, `zammad-scheduler`. |
| **Compose File** | Yes -- in the [zammad/zammad-docker-compose](https://github.com/zammad/zammad-docker-compose) repo. Includes PostgreSQL, Elasticsearch, Memcached, Redis. Scenario files for resource limits. |
| **Min RAM** | 4 GB (official minimum). Elasticsearch alone can consume 1-2 GB+. Can run without Elasticsearch for very small teams. |
| **Disk** | ~3-4 GB for all images (many containers). Budget ~6 GB total. |
| **Seed Data** | No built-in demo ticket seeder. `rake db:seed` loads system configuration only. Use the [Zammad REST API](https://docs.zammad.org/en/latest/api/ticket/index.html) to create sample tickets programmatically. Ticket templates available for manual creation with pre-filled fields. |

**Quick Start:**
```bash
git clone https://github.com/zammad/zammad-docker-compose.git && cd zammad-docker-compose
# Follow README -- adjust .env, then:
docker compose up -d
# Visit http://localhost:8080 -- setup wizard creates admin
```

---

## Other

### 21. Cal.com (TypeScript/Next.js)

| Aspect | Details |
|---|---|
| **Docker Image** | **`calcom/cal.com`** on [Docker Hub](https://hub.docker.com/r/calcom/cal.com). Official (now maintained in the main monorepo). |
| **Compose File** | Yes -- in the [calcom/cal.com](https://github.com/calcom/cal.com) main repo (previously in `calcom/docker`). Services: Cal.com app, PostgreSQL, Redis, optionally Prisma Studio. |
| **Min RAM** | 2 GB **(est.)** -- Next.js app with PostgreSQL and Redis. Build step is memory-intensive. |
| **Disk** | ~1.5 GB for images. Budget ~3 GB total. |
| **Seed Data** | Yes -- the Docker setup includes seed data with test users (credentials logged to console, admin password: `admin2022!`). Run `yarn db-seed` or let Docker Compose handle it. Use `yarn db-studio` (Prisma Studio) at `http://localhost:5555` to view seeded data. Also: [readysettech/calcom-demo](https://github.com/readysettech/calcom-demo) has a full SQL dump with production-scale sample booking data. |

**Quick Start:**
```bash
git clone --recursive https://github.com/calcom/cal.com.git && cd cal.com
cp .env.example .env
# Generate NEXTAUTH_SECRET and CALENDSO_ENCRYPTION_KEY
docker compose up -d database
DOCKER_BUILDKIT=0 docker compose build calcom
docker compose up -d
```

---

### 22. Nextcloud (PHP/Vue)

| Aspect | Details |
|---|---|
| **Docker Image** | **`nextcloud`** -- official Docker Hub image (`hub.docker.com/_/nextcloud`). Tags: `latest` (Apache), `fpm`, `fpm-alpine`. |
| **Compose File** | Not in the main `nextcloud/server` repo, but extensive examples in the [nextcloud/docker](https://github.com/nextcloud/docker/tree/master/.examples) repo. Variants: with PostgreSQL, with MariaDB, with Nginx reverse proxy, etc. |
| **Min RAM** | 512 MB minimum (128 MB per PHP process). Official recommendation: 512 MB. PHP_MEMORY_LIMIT defaults to 512M. |
| **Disk** | ~500 MB for Apache image. Budget heavily depends on file storage use case. ~2 GB for base demo. |
| **Seed Data** | Partial. Nextcloud ships [example files](https://github.com/nextcloud/example-files) (documents, photos, etc.) for new users. Auto-configure via env vars: `NEXTCLOUD_ADMIN_USER`, `NEXTCLOUD_ADMIN_PASSWORD`, `SQLITE_DATABASE` (or MySQL/PostgreSQL vars). New users get starter files automatically. |

**Quick Start:**
```bash
docker run -d -p 8080:80 --name nextcloud nextcloud
# Visit http://localhost:8080 -- setup wizard, or auto-configure with env vars
```

---

### 23. Listmonk (Go/Vue)

| Aspect | Details |
|---|---|
| **Docker Image** | **`listmonk/listmonk`** on [Docker Hub](https://hub.docker.com/r/listmonk/listmonk). Official. Single Go binary. |
| **Compose File** | Yes -- `docker-compose.yml` in the [main repo](https://github.com/knadh/listmonk/blob/master/docker-compose.yml). Two services: Listmonk + PostgreSQL. |
| **Min RAM** | 256 MB **(est.)** -- Go binary is extremely lightweight. 512 MB with PostgreSQL. |
| **Disk** | ~100 MB for Listmonk image + ~300 MB PostgreSQL. Budget ~1 GB total. |
| **Seed Data** | No built-in sample subscribers/campaigns. A demo install script exists (`install-demo.sh`) for quick evaluation. Admin created via `LISTMONK_ADMIN_USER` / `LISTMONK_ADMIN_PASSWORD` env vars on first launch. Import subscribers via CSV through the UI or REST API. |

**Quick Start:**
```bash
mkdir listmonk-demo && cd listmonk-demo
sh -c "$(curl -fsSL https://raw.githubusercontent.com/knadh/listmonk/master/install-demo.sh)"
# Visit http://localhost:9000
```

---

### 24. Mastodon (Ruby on Rails/React)

| Aspect | Details |
|---|---|
| **Docker Image** | **`tootsuite/mastodon`** / **`ghcr.io/mastodon/mastodon`** -- official. Also `linuxserver/mastodon` community image. |
| **Compose File** | Yes -- `docker-compose.yml` in the [main repo](https://github.com/mastodon/mastodon/blob/main/docker-compose.yml). Services: web, streaming, sidekiq, PostgreSQL (with `shm_size: 256mb`), Redis, optionally Elasticsearch. |
| **Min RAM** | 2 GB minimum (for a small instance, up to ~10 users). 4 GB recommended for headroom during upgrades. Add 512 MB-1 GB if enabling Elasticsearch. |
| **Disk** | ~2 GB for images. 50 GB recommended (Mastodon caches federated media). Budget ~5 GB for a minimal demo with media cleanup enabled. |
| **Seed Data** | Minimal. `rails db:seed` creates the initial admin account. No sample posts ship by default. Use `tootctl` CLI to create accounts and the REST API (`POST /api/v1/statuses`) to generate sample posts. Federation will naturally populate the timeline if connected to other instances. |

**Quick Start:**
```bash
git clone https://github.com/mastodon/mastodon.git && cd mastodon
cp .env.production.sample .env.production
# Edit .env.production (domain, secrets, SMTP, etc.)
docker compose build
docker compose run --rm web bundle exec rake mastodon:setup
docker compose up -d
```

---

### 25. NocoDB (TypeScript/Vue)

| Aspect | Details |
|---|---|
| **Docker Image** | **`nocodb/nocodb`** on [Docker Hub](https://hub.docker.com/r/nocodb/nocodb). Official. |
| **Compose File** | Yes -- documented at [nocodb.com/docs/self-hosting/installation/docker-compose](https://nocodb.com/docs/self-hosting/installation/docker-compose). Also an auto-install script (`auto-upstall`) that generates a compose file with PostgreSQL, Redis, MinIO, and Traefik. |
| **Min RAM** | 256 MB (official minimum). 1 GB practical minimum (users report OOM at 500 MB). |
| **Disk** | ~200 MB for image (lightweight Node.js). Budget ~1 GB with PostgreSQL. |
| **Seed Data** | Partial. The [nocodb/nocodb-seed](https://github.com/nocodb/nocodb-seed) repo provides seed data. Also: [Templates gallery](https://nocodb.com/templates/) with pre-built schemas. Import CSV, Excel, or JSON files via the UI. |

**Quick Start:**
```bash
docker run -d --name nocodb -p 8080:8080 nocodb/nocodb
# Visit http://localhost:8080 -- uses SQLite by default
```

---

### 26. BookStack (PHP/Laravel)

| Aspect | Details |
|---|---|
| **Docker Image** | **`lscr.io/linuxserver/bookstack`** (LinuxServer.io community image, most popular). No official image from BookStack directly. Also: `solidnerd/bookstack`. |
| **Compose File** | Yes -- provided by [LinuxServer](https://docs.linuxserver.io/images/docker-bookstack/) and [community repos](https://github.com/linuxserver/docker-bookstack). Two services: BookStack + MariaDB. |
| **Min RAM** | 256 MB minimum. 1 GB recommended. PHP_MEMORY_LIMIT: at least 128M. |
| **Disk** | ~400 MB for images. Budget ~1 GB with database and uploaded content. |
| **Seed Data** | No built-in seed command. The [official demo](https://demo.bookstackapp.com/) (resets every 30 minutes) has rich sample content (shelves, books, chapters, pages). Use the BookStack REST API to programmatically create sample content, or replicate the demo content via API export/import. Default admin: `admin@admin.com` / `password`. |

**Quick Start:**
```yaml
# docker-compose.yml
services:
  bookstack:
    image: lscr.io/linuxserver/bookstack:latest
    environment:
      - APP_URL=http://localhost:6875
      - DB_HOST=db
      - DB_DATABASE=bookstack
      - DB_USERNAME=bookstack
      - DB_PASSWORD=secret
    ports:
      - "6875:80"
  db:
    image: mariadb:10
    environment:
      - MYSQL_ROOT_PASSWORD=secret
      - MYSQL_DATABASE=bookstack
      - MYSQL_USER=bookstack
      - MYSQL_PASSWORD=secret
```

---

### 27. Kanboard (PHP)

| Aspect | Details |
|---|---|
| **Docker Image** | **`kanboard/kanboard`** on [Docker Hub](https://hub.docker.com/r/kanboard/kanboard). Official. Also on GHCR: `ghcr.io/kanboard/kanboard`. Supports amd64, arm64, arm/v7, arm/v6. |
| **Compose File** | Yes -- in the [official docs](https://docs.kanboard.org/v1/admin/docker/). Separate compose files for SQLite (no external DB needed), PostgreSQL, and MariaDB. |
| **Min RAM** | 512 MB (officially recommended). Very lightweight PHP app with embedded Nginx. |
| **Disk** | ~200 MB for image. Budget ~500 MB with SQLite + attachments. |
| **Seed Data** | No built-in demo data. Default login: `admin` / `admin`. Use the [JSON-RPC API](https://docs.kanboard.org/v1/api/task_procedures/) to programmatically create projects, tasks, and subtasks. Project duplication/templating is available in the UI. |

**Quick Start:**
```bash
docker run -d --name kanboard -p 8080:80 kanboard/kanboard
# Visit http://localhost:8080 -- login admin/admin
```

---

### 28. Easy!Appointments (PHP)

| Aspect | Details |
|---|---|
| **Docker Image** | **`alextselegidis/easyappointments`** on [Docker Hub](https://hub.docker.com/r/alextselegidis/easyappointments). Official. |
| **Compose File** | Yes -- in the [easyappointments-docker](https://github.com/alextselegidis/easyappointments-docker) repo and [official docs](https://easyappointments.org/documentation/docker/). Two services: app + MySQL. |
| **Min RAM** | 256 MB **(est.)** -- Very lightweight PHP app. 512 MB with MySQL. |
| **Disk** | ~300 MB for images. Budget ~500 MB total. |
| **Seed Data** | Yes -- the CLI `seed` command (`php artisan seed` or the `install` command) adds initial sample records (admin, providers, services) demonstrating the app's usage. Setup wizard also available at first launch. The [official demo](https://demo.easyappointments.org/) resets daily. |

**Quick Start:**
```yaml
# docker-compose.yml
services:
  easyappointments:
    image: alextselegidis/easyappointments:latest
    environment:
      - BASE_URL=http://localhost
      - DB_HOST=mysql
      - DB_NAME=easyappointments
      - DB_USERNAME=root
      - DB_PASSWORD=secret
    ports:
      - "80:80"
  mysql:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=secret
      - MYSQL_DATABASE=easyappointments
```

---

## Summary Table

| # | App | Docker Image | Compose? | Min RAM | Disk (demo) | Seed Data? |
|---|-----|-------------|----------|---------|-------------|------------|
| 1 | OpenCart | `opencart/opencart` repo (build) / `byjg/opencart` | Yes (in repo) | 512 MB (est.) | ~2 GB | Yes -- installer includes sample products |
| 2 | Spree Commerce | `spreecommerce/spree` (old) / build from `spree_starter` | Community | 2 GB | ~3 GB | Yes -- `rake spree_sample:load` |
| 3 | PrestaShop | **`prestashop/prestashop`** | Yes (official) | 2 GB | ~3 GB | Yes -- `PS_DEMO_MODE=1` auto-installs demo shop |
| 4 | Bagisto | **`webkul/bagisto`** | Yes | 1 GB (est.) | ~3 GB | Partial -- seeders run; use `laravel-data-faker` for products |
| 5 | Twenty | **`twentycrm/twenty`** | Yes (official) | 2 GB | ~3 GB | Yes -- sample records on workspace creation |
| 6 | ERPNext | **`frappe/erpnext`** | Yes (official) | 4 GB | ~8 GB | Yes -- setup wizard "Demo Setup" feature |
| 7 | Invoice Ninja | **`invoiceninja/invoiceninja`** | Yes | 2 GB (est.) | ~3 GB | Yes -- `ninja:create-test-data` artisan command |
| 8 | Plane | `makeplane/plane-*` | Yes (official) | 4 GB (est.) | ~6 GB | No -- create via UI or API |
| 9 | Huly | `hardcoreeng/*` | Yes | 4 GB (min), 16 GB (rec.) | ~10 GB | No -- use Import Tool or API |
| 10 | Taiga | `taigaio/taiga-*` | Yes (official) | 4 GB | ~5 GB | Yes -- `manage.py sample_data` |
| 11 | OpenProject | **`openproject/openproject`** | Yes (official) | 4 GB | ~5 GB | Yes -- auto-seeded on first launch |
| 12 | Rocket.Chat | **`rocket.chat`** (official) | Yes | 2 GB | ~5 GB | No -- setup wizard only |
| 13 | Mattermost | **`mattermost/mattermost-team-edition`** | Yes (official) | 2 GB | ~3 GB | No -- setup wizard only |
| 14 | Ghost | **`ghost`** (official) | Community | 1 GB | ~2 GB | Partial -- welcome post; import JSON for more |
| 15 | Discourse | `discourse/discourse` (launcher) | Non-standard | 4 GB (rec.) | ~5 GB | Minimal -- load SQL dump for full content |
| 16 | Metabase | **`metabase/metabase`** | Yes | 2 GB | ~2 GB | Yes -- built-in Sample Database + example dashboards |
| 17 | Grafana | **`grafana/grafana`** | Community | 512 MB | ~1 GB | Via provisioning -- no built-in data source |
| 18 | Plausible | **`plausible/analytics`** | Yes (official) | 2 GB | ~2 GB | No -- tracks real page views |
| 19 | Chatwoot | **`chatwoot/chatwoot`** | Yes (in repo) | 4 GB | ~4 GB | No -- use API for sample conversations |
| 20 | Zammad | `zammad/zammad-docker-compose` | Yes (official) | 4 GB | ~6 GB | No -- use API for sample tickets |
| 21 | Cal.com | **`calcom/cal.com`** | Yes (in repo) | 2 GB (est.) | ~3 GB | Yes -- seed data with test users |
| 22 | Nextcloud | **`nextcloud`** (official) | Community examples | 512 MB | ~2 GB | Partial -- example files for new users |
| 23 | Listmonk | **`listmonk/listmonk`** | Yes (in repo) | 512 MB (est.) | ~1 GB | No -- demo install script; import CSV |
| 24 | Mastodon | `ghcr.io/mastodon/mastodon` | Yes (in repo) | 2 GB | ~5 GB | Minimal -- `db:seed` creates admin only |
| 25 | NocoDB | **`nocodb/nocodb`** | Yes | 1 GB | ~1 GB | Partial -- `nocodb-seed` repo + templates |
| 26 | BookStack | `lscr.io/linuxserver/bookstack` | Yes (LinuxServer) | 256 MB | ~1 GB | No -- use API or replicate demo site |
| 27 | Kanboard | **`kanboard/kanboard`** | Yes (official) | 512 MB | ~500 MB | No -- use JSON-RPC API |
| 28 | Easy!Appointments | **`alextselegidis/easyappointments`** | Yes | 256 MB (est.) | ~500 MB | Yes -- CLI seed command |

---

## Aggregate Resource Estimates

### Running All 28 Apps Simultaneously

| Resource | Estimate | Notes |
|----------|----------|-------|
| **Total RAM** | ~64-72 GB | Sum of all minimum RAMs. Many apps share similar dependencies (PostgreSQL, Redis) but each compose stack runs its own. |
| **Total Disk** | ~90-100 GB | All images + demo data + databases. Docker image layer sharing helps somewhat. |
| **CPU Cores** | 8-16 cores | Most apps are I/O-bound, not CPU-bound. 8 cores handles light demo loads; 16 for comfortable headroom. |

### Tiered Hosting Approach

| Tier | Apps | Server Spec | Monthly Cost (est.) |
|------|------|-------------|---------------------|
| **Lightweight** (12 apps) | Kanboard, Easy!Appointments, BookStack, Listmonk, NocoDB, Ghost, Nextcloud, Grafana, Metabase, OpenCart, Plausible, Bagisto | 8 GB RAM, 4 cores, 100 GB SSD | ~$40-60 |
| **Medium** (10 apps) | PrestaShop, Spree, Twenty, Invoice Ninja, Cal.com, Mattermost, Rocket.Chat, Mastodon, Chatwoot, Taiga | 16 GB RAM, 8 cores, 200 GB SSD | ~$80-120 |
| **Heavy** (6 apps) | ERPNext, OpenProject, Plane, Huly, Discourse, Zammad | 32 GB RAM, 8 cores, 200 GB SSD | ~$120-180 |

### Key Observations

1. **Easiest to deploy** (single `docker run`): Metabase, Grafana, NocoDB, Kanboard, Ghost, Nextcloud, Listmonk
2. **Best demo/seed data out of the box**: Metabase (sample DB + dashboards), PrestaShop (`PS_DEMO_MODE=1`), OpenProject (auto-seeder), Spree (`spree_sample:load`), ERPNext (setup wizard demo)
3. **Most resource-intensive**: Huly (4-16 GB), ERPNext (4-8 GB), OpenProject (4 GB), Discourse (4 GB), Zammad (4 GB + Elasticsearch)
4. **Most lightweight**: Kanboard (~200 MB image, SQLite), Easy!Appointments (~300 MB), Listmonk (~100 MB image), NocoDB (~200 MB image)
5. **Non-standard Docker deployment**: Discourse uses its own launcher (not standard docker-compose), OpenCart lacks an official Docker Hub image
