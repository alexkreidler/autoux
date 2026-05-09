# Infrastructure Report: Self-Hosting 32 Real-World Sector Apps via Docker

> Generated 2026-05-09. Requirements marked **(est.)** are estimates based on tech stack; all others come from official documentation or community-validated sources.

---

## Table of Contents

1. [E-Commerce](#e-commerce)
2. [Booking / Scheduling](#booking--scheduling)
3. [Travel / Hospitality](#travel--hospitality)
4. [Healthcare](#healthcare)
5. [Education / LMS](#education--lms)
6. [Job Boards / Recruiting](#job-boards--recruiting)
7. [Food / Restaurant](#food--restaurant)
8. [Event Ticketing](#event-ticketing)
9. [Personal Finance](#personal-finance)
10. [Government / Civic](#government--civic)
11. [Classifieds / Marketplace](#classifieds--marketplace)
12. [Real Estate](#real-estate)
13. [Logistics / Shipping](#logistics--shipping)
14. [Nonprofit / Fundraising](#nonprofit--fundraising)
15. [Fitness / Wellness](#fitness--wellness)
16. [Library / Media](#library--media)
17. [Insurance](#insurance)
18. [Design / Creative](#design--creative)
19. [Automotive](#automotive)
20. [Social / Community](#social--community)
21. [Energy / Home Automation](#energy--home-automation)
22. [Customer Support](#customer-support)
23. [Summary Table](#summary-table)
24. [Aggregate Resource Estimates](#aggregate-resource-estimates)

---

## E-Commerce

### 1. Saleor (Python/React/Next.js)

| Aspect | Details |
|---|---|
| **Docker Image** | `ghcr.io/saleor/saleor:3.22` (API/worker), `ghcr.io/saleor/saleor-dashboard:latest` (Dashboard). On GHCR, not Docker Hub. |
| **Compose File** | Yes -- `docker-compose.yml` in [saleor-platform](https://github.com/saleor/saleor-platform). Services: api (8000), dashboard (9000), postgres:15-alpine, redis:7.0-alpine, worker, jaeger, mailpit. |
| **Min RAM** | 5 GB dedicated to Docker (official recommendation). |
| **Disk** | ~3-4 GB for all images + demo data. |
| **Seed Data** | Yes -- `docker compose run --rm api python3 manage.py populatedb --createsuperuser`. Creates sample products, categories. Default: `admin@example.com` / `admin`. |

**Quick Start:**
```bash
git clone https://github.com/saleor/saleor-platform.git && cd saleor-platform
docker compose run --rm api python3 manage.py migrate
docker compose run --rm api python3 manage.py populatedb --createsuperuser
docker compose up
# API: localhost:8000 | Dashboard: localhost:9000
```

---

### 2. Medusa (TypeScript/Node.js)

| Aspect | Details |
|---|---|
| **Docker Image** | No official Docker Hub image. Built locally from `node:20-alpine`. Community: `hassansalem/docker-medusa-testing`. |
| **Compose File** | Yes -- `docker-compose.yml` in main repo. Services: medusa (9000/5173), postgres:15-alpine, redis:7-alpine. |
| **Min RAM** | 2 GB (official hosting docs). |
| **Disk** | ~1.5-2 GB **(est.)** |
| **Seed Data** | Yes -- `start.sh` runs `yarn seed` automatically on startup. Create admin: `docker compose run --rm medusa yarn medusa user -e admin@example.com -p supersecret`. |

**Quick Start:**
```bash
npx create-medusa-app@latest
# Or: clone repo, then docker compose up
# Server: localhost:9000 | Admin: localhost:9000/app
```

---

## Booking / Scheduling

### 3. LibreBooking (PHP)

| Aspect | Details |
|---|---|
| **Docker Image** | `librebooking/librebooking:develop` on Docker Hub. |
| **Compose File** | Yes -- in [LibreBooking/docker](https://github.com/LibreBooking/docker) repo under `.examples/docker/`. Services: app (8080), MariaDB 10.6, cron. |
| **Min RAM** | 512 MB **(est.)** |
| **Disk** | ~1-2 GB |
| **Seed Data** | No -- web installer creates schema on first launch. Admin set during install. |

**Quick Start:**
```bash
git clone https://github.com/LibreBooking/docker.git && cd docker/.examples/docker
# Configure db.env and lb.env
docker compose -f docker-compose-local.yml up -d
# Visit http://localhost:8080, complete installer
```

---

## Travel / Hospitality

### 4. QloApps (PHP/PrestaShop-based)

| Aspect | Details |
|---|---|
| **Docker Image** | `webkul/qloapps_docker:latest` on Docker Hub. All-in-one (Apache + PHP + MySQL). |
| **Compose File** | Not in main repo. Self-contained image. Simple compose: one service with ports 80, 3306. |
| **Min RAM** | 1 GB **(est.)** -- all-in-one LAMP container. |
| **Disk** | ~1-1.5 GB |
| **Seed Data** | Yes -- choose "Full installation" in wizard for demo hotel data (rooms, booking types, testimonials). Default: `demo@demo.com` / `demodemo`. |

**Quick Start:**
```bash
docker run -tidp 80:80 -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=myrootpassword \
  -e MYSQL_DATABASE=qloapps \
  webkul/qloapps_docker:latest
# Visit http://localhost, complete install wizard
```

---

## Healthcare

### 5. OpenEMR (PHP)

| Aspect | Details |
|---|---|
| **Docker Image** | `openemr/openemr:flex` (dev), `openemr/openemr:7.0.4` (prod). On Docker Hub. |
| **Compose File** | Yes -- `docker/development-easy/docker-compose.yml`. Services: openemr, mariadb:11.8, phpmyadmin, couchdb, openldap, mailpit, selenium. Also `docker/production/` (lean: openemr + mysql). |
| **Min RAM** | 4 GB **(est.)** -- 7 containers in easy dev setup. |
| **Disk** | ~3-5 GB |
| **Seed Data** | Yes -- `docker compose exec openemr /root/devtools dev-reset-install-demodata`. Loads patients, users, portal logins. Default: `admin` / `pass`. |

**Quick Start:**
```bash
cd docker/development-easy
docker compose up --detach --wait
# Access at http://localhost:8300 or https://localhost:9300
# Patient portal at http://localhost:8300/portal
```

---

### 6. Bahmni (Java/React)

| Aspect | Details |
|---|---|
| **Docker Image** | Multiple `bahmni/*` images on Docker Hub: openmrs, proxy, openmrs-db, openelis, odoo-16, etc. |
| **Compose File** | Yes -- [bahmni-docker](https://github.com/Bahmni/bahmni-docker). Two variants: `bahmni-lite/` (~20 services) and `bahmni-standard/` (adds OpenELIS, Odoo, PACS). |
| **Min RAM** | 8 GB minimum (official). 16 GB recommended for Standard. |
| **Disk** | ~5-10 GB |
| **Seed Data** | Partial -- DB dumps loadable via `.env` paths. OpenMRS ships reference data. Default: `admin` / `Admin123`. Odoo: `odoo` / `odoo`. |

**Quick Start:**
```bash
git clone https://github.com/Bahmni/bahmni-docker.git && cd bahmni-docker/bahmni-lite
./run-bahmni.sh
# Or: docker compose --env-file .env up
```

---

## Education / LMS

### 7. Moodle (PHP)

| Aspect | Details |
|---|---|
| **Docker Image** | `moodlehq/moodle-php-apache` (webserver). Standard DB images (postgres, mariadb). On Docker Hub. |
| **Compose File** | Yes -- modular system in [moodle-docker](https://github.com/moodlehq/moodle-docker). `base.yml` + `db.pgsql.yml` + optional services. Uses `bin/moodle-docker-compose` wrapper. |
| **Min RAM** | 2 GB **(est.)** with PostgreSQL. 3.25 GB with MSSQL. |
| **Disk** | ~2-3 GB for images. Moodle source cloned separately (~500 MB). |
| **Seed Data** | Yes via CLI install: `php admin/cli/install_database.php --agree-license --adminpass="test"`. Default: `admin` / `test`. |

**Quick Start:**
```bash
export MOODLE_DOCKER_WWWROOT=./moodle && export MOODLE_DOCKER_DB=pgsql
git clone -b MOODLE_405_STABLE git://git.moodle.org/moodle.git $MOODLE_DOCKER_WWWROOT
cp config.docker-template.php $MOODLE_DOCKER_WWWROOT/config.php
bin/moodle-docker-compose up -d && bin/moodle-docker-wait-for-db
bin/moodle-docker-compose exec webserver php admin/cli/install_database.php \
  --agree-license --fullname="Docker moodle" --shortname="docker_moodle" \
  --adminpass="test" --adminemail="admin@example.com"
# Access at http://localhost:8000
```

---

### 8. Open edX via Tutor (Python/React)

| Aspect | Details |
|---|---|
| **Docker Image** | `docker.io/overhangio/openedx:<version>` (LMS/CMS), plus mysql:8.4, mongo:7.0, redis:7.4.5, caddy:2.7.4, meilisearch, exim-relay. |
| **Compose File** | Generated dynamically by Tutor CLI. Services: LMS, CMS, MySQL, MongoDB, Redis, Meilisearch, Caddy, SMTP. |
| **Min RAM** | 4 GB minimum, 8 GB recommended. |
| **Disk** | 8 GB minimum, 25 GB recommended. OpenEdx image alone ~2 GB. |
| **Seed Data** | Yes -- `tutor local do importdemocourse` imports official demo course. Default: `admin` / `admin`, `student` / `student`. |

**Quick Start:**
```bash
pip install tutor
tutor local launch
# Interactive config, pulls images, starts services, runs migrations
# LMS at http://local.edly.io
```

---

## Job Boards / Recruiting

### 9. OpenCATS (PHP)

| Aspect | Details |
|---|---|
| **Docker Image** | `opencats/php-base:7.2-fpm-alpine`, `prooph/nginx:www`. Community: `dmitriiageev/opencats`. |
| **Compose File** | Yes -- `docker/docker-compose.yml`. Services: nginx, php-fpm, mariadb, phpmyadmin. |
| **Min RAM** | 512 MB **(est.)** -- lightweight PHP app. |
| **Disk** | ~500 MB - 1 GB |
| **Seed Data** | Yes -- SQL seed data from `test/data/`. Also `db/cats_testdata.bak` via install wizard. Default: admin password `cats`. Test user: `john@mycompany.net` / `john99`. |

**Quick Start:**
```bash
git clone https://github.com/opencats/OpenCATS.git && cd OpenCATS/docker
docker-compose up -d
# App: http://localhost | PHPMyAdmin: http://localhost:8080
```

---

### 10. PeelJobs (Python/Django)

| Aspect | Details |
|---|---|
| **Docker Image** | **None.** No Dockerfile in repo. Django app with manual setup. |
| **Compose File** | **No.** Elasticsearch only via `docker run`. Django, PostgreSQL, Redis, Memcached run on host. |
| **Min RAM** | 1-2 GB **(est.)** |
| **Disk** | ~1-2 GB. Elasticsearch image alone ~800 MB. |
| **Seed Data** | Not documented. No default credentials. |

**Quick Start:**
```bash
git clone https://github.com/MicroPyramid/opensource-job-portal.git && cd opensource-job-portal
virtualenv venv && source venv/bin/activate && pip install -r requirements.txt
# Create PostgreSQL DB, configure .env per env.md
python manage.py migrate
docker run -d --name elasticsearch -p 9200:9200 -e "discovery.type=single-node" \
  docker.elastic.co/elasticsearch/elasticsearch:7.17.6
python manage.py update_index && python manage.py runserver
```

---

## Food / Restaurant

### 11. TastyIgniter (PHP/Laravel)

| Aspect | Details |
|---|---|
| **Docker Image** | No official image. Community: `thisisqasim/tastyigniter:3.4.0` on Docker Hub. |
| **Compose File** | Not in official repo. Community: [ThisIsQasim/TastyIgniter](https://github.com/ThisIsQasim/TastyIgniter) provides compose with app (8001), mariadb:10.7, redis:6. |
| **Min RAM** | 1 GB **(est.)** |
| **Disk** | ~1-1.5 GB |
| **Seed Data** | Partial -- setup wizard creates initial admin. `fakerphp/faker` available for test data. |

**Quick Start:**
```bash
mkdir tastyigniter && cd tastyigniter
curl -LO https://github.com/ThisIsQasim/TastyIgniter/raw/master/docker-compose.yml
docker compose up -d
docker compose exec app php artisan igniter:passwd admin
# Access at http://localhost:8001
```

---

## Event Ticketing

### 12. Hi.Events (PHP/Laravel + React)

| Aspect | Details |
|---|---|
| **Docker Image** | `daveearley/hi.events-all-in-one` on Docker Hub (Nginx + PHP-FPM + Node SSR + queue + scheduler via Supervisord). |
| **Compose File** | Yes -- `docker/all-in-one/docker-compose.yml`. Services: all-in-one (8123), postgres:17-alpine, redis:7-alpine. Dev variant has 9 services. |
| **Min RAM** | 4 GB (official: 2 CPU, 4 GB RAM, 20 GB storage). |
| **Disk** | ~2-3 GB images. 20 GB total recommended. |
| **Seed Data** | No -- register new account at first launch. |

**Quick Start:**
```bash
git clone https://github.com/HiEventsDev/hi.events.git && cd hi.events/docker/all-in-one
cp .env.example .env
# Generate APP_KEY and JWT_SECRET, update .env
docker compose up -d
# Access at http://localhost:8123, register at /auth/register
```

---

### 13. Eventyay (Python/JavaScript)

| Aspect | Details |
|---|---|
| **Docker Image** | `eventyay/eventyay-next:enext` (ticketing), `eventyay/standalone:stable` (all-in-one), `eventyay/eventyay-video:stable` (video). |
| **Compose File** | Yes -- multiple. Root `docker-compose.yml` (dev): web, worker, redis, postgres:15. `deployment/docker-compose.yml` (prod). |
| **Min RAM** | 1 GB minimum (512 MB insufficient per official guide). |
| **Disk** | ~2-3 GB |
| **Seed Data** | Partial. Standalone default: `admin@localhost` / `admin`. Video: `import_config sample/worlds/sample.json`. |

**Quick Start:**
```bash
# Standalone (simplest):
docker run -d -p 80:80 eventyay/standalone:stable
# Login: admin@localhost / admin

# Dev:
git clone https://github.com/fossasia/eventyay.git && cd eventyay
cp .env.dev-sample .env.dev && docker compose up -d --build
```

---

### 14. alf.io (Java/Spring Boot)

| Aspect | Details |
|---|---|
| **Docker Image** | `alfio/alf.io` on Docker Hub. |
| **Compose File** | Yes -- `docker-compose.yml` at repo root. Services: postgres:10, alfio (8080, commented out by default). |
| **Min RAM** | 2 GB **(est.)** -- JVM + PostgreSQL. |
| **Disk** | ~1.5-2 GB |
| **Seed Data** | Partial -- `demo` Spring profile creates admin on the fly. Password printed to console. No pre-populated events. |

**Quick Start:**
```bash
git clone https://github.com/alfio-event/alf.io.git && cd alf.io
docker-compose up
# Check logs for admin password: docker logs alfio
# Access at https://<DOCKER_IP>/admin
```

---

## Personal Finance

### 15. Firefly III (PHP/Laravel)

| Aspect | Details |
|---|---|
| **Docker Image** | `fireflyiii/core:latest` on Docker Hub. |
| **Compose File** | Yes -- in separate [firefly-iii/docker](https://github.com/firefly-iii/docker) repo. Services: app (80:8080), mariadb:lts, cron. Optional Data Importer via `docker-compose-importer.yml`. |
| **Min RAM** | 512 MB minimum. 1-2 GB recommended with DB + cron. |
| **Disk** | ~1-1.5 GB |
| **Seed Data** | No built-in demo data. Account created at first launch. `DEMO_USERNAME` / `DEMO_PASSWORD` env vars available for demo mode. |

**Quick Start:**
```bash
# Download docker-compose.yml, .env, .db.env from firefly-iii/docker repo
# Set DB_PASSWORD, APP_KEY (32 chars), STATIC_CRON_TOKEN
docker compose up -d
# Visit http://localhost, create account
```

---

### 16. Ghostfolio (TypeScript/Angular)

| Aspect | Details |
|---|---|
| **Docker Image** | `ghostfolio/ghostfolio:latest` on Docker Hub. Multi-arch (amd64, arm/v7, arm64). |
| **Compose File** | Yes -- `docker/docker-compose.yml`. Services: ghostfolio (3333), postgres:15-alpine, valkey:8.1 (Redis-compatible). Security hardened: `cap_drop: ALL`, `no-new-privileges`. |
| **Min RAM** | 1 GB **(est.)** -- runs on Raspberry Pi. |
| **Disk** | ~1-1.5 GB |
| **Seed Data** | Yes -- `npx prisma db seed` runs automatically on startup. First registered user gets ADMIN role. |

**Quick Start:**
```bash
git clone https://github.com/ghostfolio/ghostfolio.git && cd ghostfolio
cp .env.example .env  # fill in random secrets
docker compose -f docker/docker-compose.yml up -d
# Access at http://localhost:3333
```

---

## Government / Civic

### 17. Decidim (Ruby on Rails)

| Aspect | Details |
|---|---|
| **Docker Image** | `decidim/decidim:latest` on Docker Hub and `ghcr.io/decidim/decidim:latest`. |
| **Compose File** | Yes -- in [decidim/docker](https://github.com/decidim/docker) repo. Services: decidim (3000), postgres:14, redis. |
| **Min RAM** | 4 GB **(est.)** -- Rails + Postgres + Redis. |
| **Disk** | ~2-3 GB |
| **Seed Data** | Yes -- seeds run automatically with `docker-compose up`. Default: `admin@example.org` / `decidim123456789` (admin), `user@example.org` / `decidim123456789` (user), `system@example.org` / `decidim123456789` (system admin at `/system`). |

**Quick Start:**
```bash
git clone https://github.com/decidim/docker.git decidim-docker && cd decidim-docker
docker-compose up
# Wait for migrations + seeds, then visit http://localhost:3000
```

---

### 18. CKAN (Python)

| Aspect | Details |
|---|---|
| **Docker Image** | `ckan/ckan-base:2.10` (official). Dev variant: `ckan/ckan-dev`. Deployed via [ckan-docker](https://github.com/ckan/ckan-docker) repo. |
| **Compose File** | Yes -- in [ckan/ckan-docker](https://github.com/ckan/ckan-docker). Services: CKAN app, PostgreSQL, Solr (`ckan/ckan-solr:2.10-solr9`), Redis:6, DataPusher, NGINX (SSL). |
| **Min RAM** | 4 GB **(est.)** -- Solr + PostgreSQL are hungry. |
| **Disk** | ~3-4 GB |
| **Seed Data** | No built-in demo datasets. Default: `ckan_admin` / `test1234`. |

**Quick Start:**
```bash
git clone https://github.com/ckan/ckan-docker.git && cd ckan-docker
cp .env.example .env
docker compose build && docker compose up -d
# Access at https://localhost:8443
```

---

### 19. OpnForm (PHP/Laravel + Vue/Nuxt)

| Aspect | Details |
|---|---|
| **Docker Image** | `jhumanj/opnform-api` (API), `jhumanj/opnform-client` (Frontend) on Docker Hub. |
| **Compose File** | Yes -- `docker-compose.yml` at repo root. Services: NGINX proxy, Nuxt SSR frontend, Laravel API backend, PostgreSQL, Redis, API worker, API scheduler. |
| **Min RAM** | 2 GB **(est.)** |
| **Disk** | ~2-3 GB |
| **Seed Data** | No. First user created via admin setup after launch. |

**Quick Start:**
```bash
git clone https://github.com/OpnForm/OpnForm.git && cd OpnForm
chmod +x scripts/docker-setup.sh
./scripts/docker-setup.sh
# Access at http://localhost
```

---

## Classifieds / Marketplace

### 20. Osclass (PHP)

| Aspect | Details |
|---|---|
| **Docker Image** | No official pre-built image. Builds from local Dockerfiles (PHP-FPM). |
| **Compose File** | Yes -- `docker-compose.yml` at repo root. Services: PHP-FPM, nginx:alpine, MySQL 8.0, memcached:alpine, mailhog, phpmyadmin. |
| **Min RAM** | 1 GB **(est.)** |
| **Disk** | ~2 GB |
| **Seed Data** | No. Web installer creates schema. Admin set during install. |

**Quick Start:**
```bash
git clone --recursive https://github.com/mindstellar/Osclass.git && cd Osclass
docker compose up -d
# Webserver: localhost:5080 | phpMyAdmin: localhost:5800 | Mailhog: localhost:5025
```

---

## Real Estate

### 21. MicroRealEstate (Node.js)

| Aspect | Details |
|---|---|
| **Docker Image** | Multiple microservice images on GHCR: `ghcr.io/microrealestate/microrealestate/gateway`, `authenticator`, `api`, `tenantapi`, `pdfgenerator`, `emailer`, `landlord-frontend`, `tenant-frontend`. |
| **Compose File** | Yes -- `docker-compose.yml` at repo root. 11 services: Caddy, Gateway, Authenticator, API, TenantAPI, PDF Generator, Emailer, Landlord Frontend, Tenant Frontend, MongoDB 7, Redis 7.4. |
| **Min RAM** | 2 GB **(est.)** -- 11 lightweight Node.js containers. |
| **Disk** | ~3-4 GB |
| **Seed Data** | No built-in demo data. |

**Quick Start:**
```bash
mkdir mre && cd mre
curl -O https://raw.githubusercontent.com/microrealestate/microrealestate/master/docker-compose.yml
curl https://raw.githubusercontent.com/microrealestate/microrealestate/master/.env.domain > .env
# Edit .env to set secrets
APP_PORT=8080 docker compose --profile local up
# Landlord: localhost:8080/landlord | Tenant: localhost:8080/tenant
```

---

## Logistics / Shipping

### 22. Fleetbase (PHP/Ember.js)

| Aspect | Details |
|---|---|
| **Docker Image** | `fleetbase/fleetbase-api:latest` on Docker Hub. Console built from local Dockerfile. |
| **Compose File** | Yes -- `docker-compose.yml` at repo root. 8 services: Application (API), Console (Ember), MySQL 8.0, Redis 4, SocketCluster, Scheduler, Queue worker, HTTPD (Apache proxy). |
| **Min RAM** | 4 GB **(est.)** |
| **Disk** | ~4-5 GB |
| **Seed Data** | No. Admin created during first setup. |

**Quick Start:**
```bash
git clone https://github.com/fleetbase/fleetbase.git && cd fleetbase
./scripts/docker-install.sh
# Console: localhost:4200 | API: localhost:8000
```

---

### 23. Karrio (Python)

| Aspect | Details |
|---|---|
| **Docker Image** | `karrio/server` on Docker Hub (also `karrio.docker.scarf.sh/karrio/server`, `karrio/dashboard`). |
| **Compose File** | Yes -- `docker/docker-compose.yml`. 6 services: API server, Worker, Dashboard, PostgreSQL 16, Redis, Maildev. Also `docker-compose.hobby.yml` for production with Caddy. |
| **Min RAM** | 4 GB (recommended). |
| **Disk** | ~3-4 GB |
| **Seed Data** | Yes -- admin created on startup. Default: `admin@example.com` / `demo`. |

**Quick Start:**
```bash
git clone --depth 1 https://github.com/karrioapi/karrio && cd karrio
git submodule update --init community
cd docker && docker compose up
# Dashboard: localhost:3002 | API: localhost:5002
```

---

## Nonprofit / Fundraising

### 24. CiviCRM (PHP)

| Aspect | Details |
|---|---|
| **Docker Image** | `civicrm/civicrm` on Docker Hub. Versioned: `civicrm/civicrm:6.0-php8.3`. |
| **Compose File** | Yes -- in [civicrm/civicrm-docker](https://github.com/civicrm/civicrm-docker) at `example/civicrm/compose.yaml`. Services: CiviCRM (Apache + PHP), MySQL. |
| **Min RAM** | 2 GB **(est.)** |
| **Disk** | ~2-3 GB |
| **Seed Data** | Yes -- `civicrm-docker-install` script loads schema + sample data. Default: `admin` / `password`. |

**Quick Start:**
```bash
git clone https://github.com/civicrm/civicrm-docker && cd civicrm-docker/example/civicrm
docker compose up -d
docker compose exec -u www-data -e CIVICRM_ADMIN_USER=admin \
  -e CIVICRM_ADMIN_PASS=password app civicrm-docker-install
# Access at http://localhost:8760
```

---

## Fitness / Wellness

### 25. wger (Python/Django)

| Aspect | Details |
|---|---|
| **Docker Image** | `wger/server:latest` on Docker Hub. |
| **Compose File** | Yes -- in [wger-project/docker](https://github.com/wger-project/docker) (separate repo). 7 services: Web (Django/Gunicorn), PostgreSQL, Redis, NGINX, Celery worker, Celery beat, optional Celery Flower. |
| **Min RAM** | 2 GB **(est.)** |
| **Disk** | ~2-3 GB. Ingredient dataset adds ~1 GB to DB. |
| **Seed Data** | Yes -- extensive. Default: `admin` / `adminadmin`. Seed commands: `sync-exercises`, `download-exercise-images`, `download-exercise-videos`, `load-online-fixtures`, `sync-ingredients-bulk`. |

**Quick Start:**
```bash
git clone https://github.com/wger-project/docker.git && cd docker
docker compose up -d
# Access at http://localhost
```

---

## Library / Media

### 26. Calibre-Web (Python/Flask)

| Aspect | Details |
|---|---|
| **Docker Image** | `linuxserver/calibre-web` on Docker Hub (LinuxServer.io community, de facto standard). No official image from project. |
| **Compose File** | No compose in main repo. LinuxServer.io provides examples. Single container + bring your own Calibre library. |
| **Min RAM** | 512 MB **(est.)** |
| **Disk** | ~1 GB for image. Library size depends on ebook collection. |
| **Seed Data** | Sample `metadata.db` available in repo at `library/metadata.db`. Default: `admin` / `admin123`. |

**Quick Start:**
```bash
docker run -d --name=calibre-web \
  -e PUID=1000 -e PGID=1000 -e TZ=Etc/UTC \
  -p 8083:8083 \
  -v /path/to/data:/config \
  -v /path/to/calibre/library:/books \
  linuxserver/calibre-web:latest
# Access at http://localhost:8083 | admin / admin123
```

---

### 27. Koha (Perl)

| Aspect | Details |
|---|---|
| **Docker Image** | `koha/koha-testing` on Docker Hub (dev/testing). No official production image; traditionally via Debian packages. Maintained via [koha-testing-docker](https://gitlab.com/koha-community/koha-testing-docker) on GitLab. |
| **Compose File** | Yes -- in koha-testing-docker repo. Services: Koha app, MySQL, Memcached, Mailpit, optional Elasticsearch, Selenium, Keycloak. |
| **Min RAM** | 2.6 GB without Elasticsearch; ~4.6 GB with Elasticsearch. |
| **Disk** | ~4-5 GB **(est.)** |
| **Seed Data** | Credentials generated from `koha-conf.xml`. Retrieve with `koha-user` / `koha-pass` in container. |

**Quick Start:**
```bash
# Uses ktd (koha-testing-docker) CLI wrapper
ktd up
ktd --shell
ktd --wait-ready 100
```

---

## Insurance

### 28. openIMIS (Python/React)

| Aspect | Details |
|---|---|
| **Docker Image** | `ghcr.io/openimis/openimis-fe` (frontend), `ghcr.io/openimis/openimis-be` (backend). On GHCR. |
| **Compose File** | Yes -- `compose.yml` in [openimis-dist_dkr](https://github.com/openimis/openimis-dist_dkr). Modular: base, postgresql, openSearch, cache. Services: Frontend, Backend, Migrations, Worker (x3), RabbitMQ, PostgreSQL, OpenSearch, Cache. |
| **Min RAM** | 4 GB **(est.)** -- OpenSearch + RabbitMQ + DB. |
| **Disk** | ~5-6 GB **(est.)** |
| **Seed Data** | Yes -- set `DEMO_DATASET=true` in `.env`. Default DB: `IMISuser` / `IMISuserP@s`. |

**Quick Start:**
```bash
git clone https://github.com/openimis/openimis-dist_dkr.git && cd openimis-dist_dkr
git checkout develop
cp .env.example .env
# Edit .env, set SECRET_KEY, optionally DEMO_DATASET=true
docker compose up -d
# Access at http://localhost
```

---

## Design / Creative

### 29. Penpot (Clojure/ClojureScript)

| Aspect | Details |
|---|---|
| **Docker Image** | `penpotapp/frontend`, `penpotapp/backend`, `penpotapp/exporter` on Docker Hub. |
| **Compose File** | Yes -- `docker/images/docker-compose.yaml`. 6 services: frontend (9001:8080), backend, exporter, postgres:15, valkey:8.1, mailcatcher. |
| **Min RAM** | 4 GB **(est.)** -- exporter (headless browser) is memory-intensive. |
| **Disk** | ~3-4 GB |
| **Seed Data** | No demo data. Registration configurable. No default credentials. |

**Quick Start:**
```bash
wget https://raw.githubusercontent.com/penpot/penpot/main/docker/images/docker-compose.yaml
docker compose -p penpot -f docker-compose.yaml up -d
# Access at http://localhost:9001
```

---

## Automotive

### 30. LubeLogger (C#/.NET)

| Aspect | Details |
|---|---|
| **Docker Image** | `ghcr.io/hargata/lubelogger:latest` (primary, GHCR). Mirror: `hargata/lubelogger` on Docker Hub. |
| **Compose File** | Yes -- `docker-compose.yml` at repo root. Single `app` service. Optional: `docker-compose.postgresql.yml`, `docker-compose.traefik.yml`. |
| **Min RAM** | 256 MB **(est.)** -- very lightweight .NET app. |
| **Disk** | ~500 MB |
| **Seed Data** | No. Demo at demo.lubelogger.com uses `test` / `1234`. Self-hosted credentials set at first setup. |

**Quick Start:**
```bash
docker pull ghcr.io/hargata/lubelogger:latest
# Download docker-compose.yml from repo
docker compose up -d
# Access at http://localhost:8080
```

---

## Social / Community

### 31. Lemmy (Rust/TypeScript)

| Aspect | Details |
|---|---|
| **Docker Image** | `dessalines/lemmy` (backend), `dessalines/lemmy-ui` (frontend), `asonix/pictrs` (images). On Docker Hub. |
| **Compose File** | Yes -- in [lemmy-docs](https://github.com/LemmyNet/lemmy-docs) at `assets/docker-compose.yml`. 6 services: nginx:1-alpine (10633), lemmy, lemmy-ui, pictrs, postgres (1 GB shm), postfix-relay. |
| **Min RAM** | 2 GB **(est.)** |
| **Disk** | ~3-4 GB |
| **Seed Data** | No. Must replace `{{ placeholders }}` in config files before deploy. |

**Quick Start:**
```bash
mkdir lemmy && cd lemmy
wget https://raw.githubusercontent.com/LemmyNet/lemmy-docs/main/assets/docker-compose.yml
wget https://raw.githubusercontent.com/LemmyNet/lemmy-docs/main/assets/lemmy.hjson
wget https://raw.githubusercontent.com/LemmyNet/lemmy-docs/main/assets/nginx.conf
# Edit all files to replace {{ placeholders }}
docker compose up -d
# Access at http://localhost:10633
```

---

## Energy / Home Automation

### 32. Home Assistant (Python)

| Aspect | Details |
|---|---|
| **Docker Image** | `ghcr.io/home-assistant/home-assistant:stable` (official, GHCR). Also `homeassistant/home-assistant` on Docker Hub. |
| **Compose File** | No compose in core repo. Docs provide example. Single container, built-in SQLite. |
| **Min RAM** | 2 GB (recommended). |
| **Disk** | ~1.5-2 GB for image. DB grows over time. |
| **Seed Data** | No. Onboarding wizard on first launch creates admin. |

**Quick Start:**
```bash
docker run -d --name homeassistant --privileged --restart=unless-stopped \
  -e TZ=America/New_York \
  -v /path/to/config:/config \
  -v /run/dbus:/run/dbus:ro \
  --network=host \
  ghcr.io/home-assistant/home-assistant:stable
# Access at http://localhost:8123
```

---

## Customer Support

*Note: Chatwoot and Zammad are covered in the original `docker-infrastructure-report.md`. Including here for completeness in the summary table.*

---

## Summary Table

| # | App | Category | Docker Image | Compose? | Min RAM | Disk (demo) | Seed Data? |
|---|-----|----------|-------------|----------|---------|-------------|------------|
| 1 | Saleor | E-commerce | `ghcr.io/saleor/saleor` | Yes (platform repo) | 5 GB | ~3-4 GB | Yes -- `populatedb` |
| 2 | Medusa | E-commerce | Build local | Yes (root) | 2 GB | ~1.5-2 GB | Yes -- auto-seed |
| 3 | LibreBooking | Booking | `librebooking/librebooking` | Yes (separate repo) | 512 MB (est.) | ~1-2 GB | No |
| 4 | QloApps | Hotel Booking | `webkul/qloapps_docker` | No (self-contained) | 1 GB (est.) | ~1-1.5 GB | Yes -- install wizard |
| 5 | OpenEMR | Healthcare | `openemr/openemr` | Yes (in repo) | 4 GB (est.) | ~3-5 GB | Yes -- `dev-reset-install-demodata` |
| 6 | Bahmni | Healthcare | `bahmni/*` (many) | Yes (2 variants) | 8 GB | ~5-10 GB | Partial (DB dumps) |
| 7 | Moodle | LMS | `moodlehq/moodle-php-apache` | Yes (modular) | 2 GB (est.) | ~2-3 GB | Yes -- CLI install |
| 8 | Open edX/Tutor | LMS | `overhangio/openedx` | Generated by Tutor | 4 GB (8 rec.) | 8-25 GB | Yes -- demo course |
| 9 | OpenCATS | Job Board | `opencats/php-base` | Yes (docker/) | 512 MB (est.) | ~500 MB-1 GB | Yes -- SQL scripts |
| 10 | PeelJobs | Job Board | **None** | **No** | 1-2 GB (est.) | ~1-2 GB | No |
| 11 | TastyIgniter | Restaurant | None (community) | No (community) | 1 GB (est.) | ~1-1.5 GB | Partial (wizard) |
| 12 | Hi.Events | Ticketing | `daveearley/hi.events-all-in-one` | Yes (docker/) | 4 GB | ~2-3 GB | No |
| 13 | Eventyay | Events | `eventyay/*` (several) | Yes (multiple) | 1 GB | ~2-3 GB | Partial |
| 14 | alf.io | Ticketing | `alfio/alf.io` | Yes (root) | 2 GB (est.) | ~1.5-2 GB | Partial (demo profile) |
| 15 | Firefly III | Finance | `fireflyiii/core` | Yes (separate repo) | 512 MB (1-2 rec.) | ~1-1.5 GB | No |
| 16 | Ghostfolio | Finance | `ghostfolio/ghostfolio` | Yes (docker/) | 1 GB (est.) | ~1-1.5 GB | Yes -- auto-seed |
| 17 | Decidim | Civic | `decidim/decidim` | Yes (separate repo) | 4 GB (est.) | ~2-3 GB | Yes -- auto with compose |
| 18 | CKAN | Data Portal | `ckan/ckan-base:2.10` | Yes (separate repo) | 4 GB (est.) | ~3-4 GB | No |
| 19 | OpnForm | Forms | `jhumanj/opnform-api` | Yes (root) | 2 GB (est.) | ~2-3 GB | No |
| 20 | Osclass | Classifieds | Built locally | Yes (root) | 1 GB (est.) | ~2 GB | No |
| 21 | MicroRealEstate | Real Estate | `ghcr.io/microrealestate/*` | Yes (root) | 2 GB (est.) | ~3-4 GB | No |
| 22 | Fleetbase | Logistics | `fleetbase/fleetbase-api` | Yes (root) | 4 GB (est.) | ~4-5 GB | No |
| 23 | Karrio | Shipping | `karrio/server` | Yes (docker/) | 4 GB | ~3-4 GB | Yes -- admin auto-created |
| 24 | CiviCRM | Nonprofit | `civicrm/civicrm` | Yes (separate repo) | 2 GB (est.) | ~2-3 GB | Yes -- install script |
| 25 | wger | Fitness | `wger/server` | Yes (separate repo) | 2 GB (est.) | ~2-3 GB | Yes -- extensive |
| 26 | Calibre-Web | Library | `linuxserver/calibre-web` | No (examples) | 512 MB (est.) | ~1 GB | Sample metadata.db |
| 27 | Koha | Library | `koha/koha-testing` | Yes (GitLab) | 2.6 GB | ~4-5 GB (est.) | Generated creds |
| 28 | openIMIS | Insurance | `ghcr.io/openimis/*` | Yes (modular) | 4 GB (est.) | ~5-6 GB (est.) | Yes -- `DEMO_DATASET=true` |
| 29 | Penpot | Design | `penpotapp/frontend` | Yes (docker/) | 4 GB (est.) | ~3-4 GB | No |
| 30 | LubeLogger | Automotive | `ghcr.io/hargata/lubelogger` | Yes (root) | 256 MB (est.) | ~500 MB | No |
| 31 | Lemmy | Social | `dessalines/lemmy` | Yes (docs repo) | 2 GB (est.) | ~3-4 GB | No |
| 32 | Home Assistant | Energy/Home | `ghcr.io/home-assistant/home-assistant:stable` | No (example in docs) | 2 GB | ~1.5-2 GB | No |

---

## Aggregate Resource Estimates

### Running All 32 Apps Simultaneously

| Resource | Estimate | Notes |
|----------|----------|-------|
| **Total RAM** | ~82-92 GB | Sum of all minimums. Each compose stack runs its own DB/Redis. |
| **Total Disk** | ~80-110 GB | All images + demo data + databases. Docker layer sharing helps. |
| **CPU Cores** | 8-16 cores | Most are I/O-bound. 8 for light demo; 16 for headroom. |

### Tiered Hosting Approach

| Tier | Apps | Server Spec | Monthly Cost (est.) |
|------|------|-------------|---------------------|
| **Lightweight** (9 apps) | LubeLogger, Calibre-Web, LibreBooking, OpenCATS, Firefly III, Ghostfolio, Eventyay, TastyIgniter, QloApps | 8 GB RAM, 4 cores, 80 GB SSD | ~$40-60 |
| **Medium** (13 apps) | Saleor, Medusa, Moodle, Osclass, OpnForm, MicroRealEstate, CiviCRM, wger, Lemmy, Home Assistant, alf.io, PeelJobs, Koha | 24 GB RAM, 8 cores, 200 GB SSD | ~$100-140 |
| **Heavy** (10 apps) | OpenEMR, Bahmni, Open edX, Hi.Events, Decidim, CKAN, Fleetbase, Karrio, openIMIS, Penpot | 48 GB RAM, 16 cores, 300 GB SSD | ~$180-250 |

### Key Observations

1. **Easiest to deploy** (single `docker run` or minimal compose): LubeLogger, Calibre-Web, Home Assistant, QloApps, Eventyay (standalone), Firefly III
2. **Best demo/seed data out of the box**: Saleor (`populatedb`), OpenEMR (`demodata`), Decidim (auto-seeds), wger (exercises + ingredients), Open edX (`importdemocourse`), CiviCRM (install script), QloApps (full install)
3. **Most resource-intensive**: Bahmni (8-16 GB), Open edX (4-8 GB + 25 GB disk), openIMIS (4 GB + OpenSearch), CKAN (4 GB + Solr), Penpot (4 GB headless browser)
4. **Most lightweight**: LubeLogger (~256 MB, single container), Calibre-Web (~512 MB), LibreBooking (~512 MB), OpenCATS (~512 MB)
5. **No Docker support**: PeelJobs (manual Django setup only)
6. **Non-standard Docker**: Koha (GitLab-hosted, uses `ktd` wrapper), Open edX (Tutor generates compose dynamically)
