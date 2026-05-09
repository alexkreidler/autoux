# 🎯 UserSim App Catalog

> Last checked: 2026-05-09 — **21 up, 4 down, 1 partially up**

26 web apps deployed at `*.usersim.alexkreidler.com` for synthetic persona testing. Each app represents a real-world product category that AI agents will navigate using browser automation.

---

## 🛒 E-Commerce

### PrestaShop
- **URL:** http://prestashop.usersim.alexkreidler.com
- **Login:** `demo@prestashop.com` / `prestashop_demo` (admin at `/admin`)
- **Status:** ✅ Live
- **What it is:** Full-featured online store with product catalog, cart, and multi-step checkout. Auto-installed with demo products, categories, and CMS pages via `PS_DEMO_MODE`.
- **Key agent flows:** Browse products → filter by category → add to cart → multi-step checkout (account, billing, shipping, payment, confirm) → order tracking
- **Seed data:** Excellent — complete demo shop with products, categories, customers
- **Stack:** PHP/Symfony, MySQL | **RAM:** 2 GB | **Disk:** ~3 GB

### Bagisto
- **URL:** http://bagisto.usersim.alexkreidler.com
- **Login:** `admin@example.com` / `admin123` (admin at `/admin/login`)
- **Status:** ✅ Live (setup wizard)
- **What it is:** Laravel-based e-commerce with multi-language, multi-currency, and multi-warehouse support. Six product types (simple, configurable, grouped, bundled, virtual, downloadable).
- **Key agent flows:** Browse multilingual storefront → search with filters → view product variants → add to cart → checkout → manage account
- **Seed data:** Partial — seeders run on boot; use `laravel-data-faker` for demo products
- **Stack:** PHP/Laravel, Vue.js, MySQL | **RAM:** 1-2 GB | **Disk:** ~3 GB

---

## 💼 CRM & Business

### Twenty CRM
- **URL:** http://twenty.usersim.alexkreidler.com
- **Login:** Sign up on first visit
- **Status:** ✅ Live
- **What it is:** Modern, Notion-inspired CRM. Contact/company management, deal pipeline (kanban), activity logging, task management, custom objects.
- **Key agent flows:** Create workspace → add contacts/companies → build deal pipeline → drag deals through stages → create custom views with filters → configure integrations
- **Seed data:** Yes — sample People, Companies, Opportunities created on workspace setup
- **Stack:** TypeScript, React, Node.js, PostgreSQL, Redis | **RAM:** 2 GB | **Disk:** ~3 GB

### ERPNext
- **URL:** http://erpnext.usersim.alexkreidler.com
- **Login:** (pending) / `admin123`
- **Status:** ❌ Down (500 Internal Server Error — `bench new-site` may have failed)
- **What it is:** Full ERP suite — accounting, inventory, CRM, HR, manufacturing. Hundreds of forms and workflows. Used by millions.
- **Key agent flows:** Setup wizard → create sales order → generate invoice → record payment → manage inventory → run payroll
- **Seed data:** Yes — setup wizard has "Demo Setup" option with sample company + transactions
- **Stack:** Python/Frappe, MariaDB, Redis | **RAM:** 4 GB | **Disk:** ~8 GB

### Invoice Ninja
- **URL:** http://invoiceninja.usersim.alexkreidler.com
- **Login:** `admin@example.com` / `changeme!`
- **Status:** ✅ Live
- **What it is:** Invoicing, quotes, expenses, and time tracking with 40+ payment gateways. Flutter web admin + React client portal.
- **Key agent flows:** Create client → create invoice (line items, taxes, discounts) → send invoice → record payment → create recurring invoice → view reports
- **Seed data:** Yes — run `ninja:create-test-data` for sample invoices, clients, payments
- **Stack:** PHP/Laravel (API), Flutter (admin), MySQL | **RAM:** 2 GB | **Disk:** ~3 GB

---

## 📋 Project Management

### Plane
- **URL:** http://plane.usersim.alexkreidler.com
- **Login:** Sign up on first visit
- **Status:** ✅ Live
- **What it is:** Jira/Linear alternative with multiple view types (list, board, calendar, spreadsheet, Gantt), cycles (sprints), and collaborative docs.
- **Key agent flows:** Create workspace → create project → add issues with priorities/labels → organize into sprint → switch between views → track burndown
- **Seed data:** No — create via UI or API
- **Stack:** Next.js, Python/Django, PostgreSQL, Redis, MinIO | **RAM:** 4 GB | **Disk:** ~6 GB

### OpenProject
- **URL:** http://openproject.usersim.alexkreidler.com
- **Login:** `admin` / `admin123admin123`
- **Status:** ✅ Live
- **What it is:** Enterprise PM with Gantt charts, agile boards, time tracking, cost reporting, meetings, and wiki. Auto-seeded with demo projects.
- **Key agent flows:** Browse demo projects → create work packages → link dependencies → drag Gantt bars → log time → create meeting agenda
- **Seed data:** Excellent — auto-seeded on first launch with demo projects, Gantt charts, boards
- **Stack:** Ruby on Rails, Angular, PostgreSQL, Memcached | **RAM:** 4 GB | **Disk:** ~5 GB

### Taiga
- **URL:** http://taiga.usersim.alexkreidler.com
- **Login:** `admin` / `123123`
- **Status:** ✅ Live
- **What it is:** Beautiful agile PM built for Scrum and Kanban. Backlog management, sprint planning, story points, burndown charts, WIP limits.
- **Key agent flows:** Create project (Scrum/Kanban) → manage backlog → plan sprint → estimate stories → run sprint board → review burndown
- **Seed data:** Yes — `manage.py sample_data` generates demo projects
- **Stack:** Python/Django, Angular, PostgreSQL, RabbitMQ | **RAM:** 4 GB | **Disk:** ~5 GB

### Huly
- **URL:** http://huly.usersim.alexkreidler.com
- **Login:** Sign up on first visit
- **Status:** ✅ Live
- **What it is:** All-in-one Linear/Jira/Slack/Notion alternative. Issues, docs, chat, HR, and virtual office in a single app.
- **Key agent flows:** Create workspace → track issues → write docs (Notion-like) → chat with team → manage HR profiles
- **Seed data:** No — use Import Tool or API
- **Stack:** TypeScript, Svelte, MongoDB, Elasticsearch, MinIO | **RAM:** 4-16 GB | **Disk:** ~10 GB

### Kanboard
- **URL:** http://kanboard.usersim.alexkreidler.com
- **Login:** `admin` / `admin`
- **Status:** ✅ Live
- **What it is:** Minimalist kanban board. Intentionally spartan — function over form. SQLite, no external DB.
- **Key agent flows:** Create project → add tasks → drag between columns → set due dates → add subtasks → configure automation
- **Seed data:** No — use JSON-RPC API to create sample data
- **Stack:** PHP, SQLite | **RAM:** 512 MB | **Disk:** ~500 MB

---

## 💬 Team Communication

### Rocket.Chat
- **URL:** http://rocketchat.usersim.alexkreidler.com
- **Login:** Setup wizard on first visit
- **Status:** ❌ Down (503 — OOM at 2 GiB, needs ~4 GiB for cold start)
- **What it is:** Slack alternative with channels, threads, DMs, video calls, and a marketplace for integrations.
- **Key agent flows:** Complete setup wizard → create channels → send messages → start threads → share files → configure integrations
- **Seed data:** No — setup wizard creates admin + `#general`
- **Stack:** TypeScript, Meteor.js, React, MongoDB | **RAM:** 2-4 GB | **Disk:** ~5 GB

### Mattermost
- **URL:** http://mattermost.usersim.alexkreidler.com
- **Login:** Setup wizard on first visit
- **Status:** ✅ Live
- **What it is:** Slack alternative with channels, threads, playbooks (incident response), and boards (Focalboard). Extensive System Console.
- **Key agent flows:** Create team → create channels → send messages → run playbooks → manage boards → configure dozens of System Console settings
- **Seed data:** No — setup wizard creates first team
- **Stack:** Go, React/TypeScript, PostgreSQL | **RAM:** 2 GB | **Disk:** ~3 GB

---

## 📰 CMS & Publishing

### Ghost
- **URL:** http://ghost.usersim.alexkreidler.com
- **Login:** Visit `/ghost` to create admin
- **Status:** ✅ Live
- **What it is:** Elegant publishing platform. Rich card-based editor, membership/newsletter system, theme management.
- **Key agent flows:** Create admin → write post with cards (images, embeds, HTML) → schedule publishing → configure membership tiers → send newsletter → manage themes
- **Seed data:** Partial — welcome post on first launch; import JSON for more
- **Stack:** Node.js, Ember.js, MySQL | **RAM:** 1 GB | **Disk:** ~2 GB

### Discourse
- **URL:** http://discourse.usersim.alexkreidler.com
- **Login:** `admin` / `admin12345`
- **Status:** ❌ Down (503 — SiteSetting init fails; needs full `discourse_docker` launcher, not K8s-friendly without Bitnami image)
- **What it is:** Modern community forum with progressive trust system, hundreds of admin settings, and plugin ecosystem.
- **Key agent flows:** Sign up → complete new user tutorial → create topic → reply with quotes/polls → navigate categories → configure site settings
- **Seed data:** Minimal — load SQL dump for rich content
- **Stack:** Ruby on Rails, Ember.js, PostgreSQL, Redis | **RAM:** 4 GB | **Disk:** ~5 GB

### BookStack
- **URL:** http://bookstack.usersim.alexkreidler.com
- **Login:** `admin@admin.com` / `password`
- **Status:** ✅ Live
- **What it is:** Hierarchical wiki: Shelves → Books → Chapters → Pages. WYSIWYG + Markdown editors, full-text search, granular permissions.
- **Key agent flows:** Create shelf → create book → add chapters → write pages → organize with drag-and-drop → search content → configure permissions
- **Seed data:** No — use API or replicate demo.bookstackapp.com content
- **Stack:** PHP/Laravel, MariaDB | **RAM:** 256 MB | **Disk:** ~1 GB

---

## 📊 Analytics & Dashboards

### Metabase
- **URL:** http://metabase.usersim.alexkreidler.com
- **Login:** Setup wizard on first visit
- **Status:** ✅ Live
- **What it is:** BI tool with visual query builder (no SQL needed), dashboard creation, and auto-generated questions. Ships with a sample database.
- **Key agent flows:** Connect to sample DB → build question (select table, add filters, choose viz) → create dashboard → add cards → set auto-refresh → subscribe to alerts
- **Seed data:** Excellent — built-in Sample Database (Orders, People, Products, Reviews) + example dashboards
- **Stack:** Clojure, React/TypeScript, H2 (sample DB) | **RAM:** 2 GB | **Disk:** ~2 GB

### Grafana
- **URL:** http://grafana.usersim.alexkreidler.com
- **Login:** `admin` / `admin`
- **Status:** ✅ Live
- **What it is:** Observability dashboards. Panel editing with query builders, transformation pipelines, threshold configuration, and alert rules.
- **Key agent flows:** Add data source → create dashboard → add panels → configure queries → select visualization → set time ranges → create alerts
- **Seed data:** Via provisioning (YAML + JSON). No built-in data source.
- **Stack:** Go, React/TypeScript | **RAM:** 512 MB | **Disk:** ~1 GB

### Plausible
- **URL:** http://plausible.usersim.alexkreidler.com
- **Login:** Register on first visit
- **Status:** ✅ Live
- **What it is:** Privacy-first web analytics (Google Analytics alternative). Clean dashboard, goals/funnels, email reports.
- **Key agent flows:** Create account → add website → install tracking script → view dashboard (visitors, sources, pages, countries) → set up goals → configure funnels
- **Seed data:** No — tracks real page views
- **Stack:** Elixir/Phoenix, React, PostgreSQL, ClickHouse | **RAM:** 2 GB | **Disk:** ~2 GB

---

## 🎧 Customer Support

### Chatwoot
- **URL:** http://chatwoot.usersim.alexkreidler.com
- **Login:** Sign up on first visit
- **Status:** ✅ Live
- **What it is:** Omni-channel support (Intercom/Zendesk alternative). Live chat widget, email, social media integration, knowledge base, CSAT surveys.
- **Key agent flows:** Create account → configure inbox (website widget) → reply to conversations → use canned responses → create knowledge base articles → view reports
- **Seed data:** No — use API for sample conversations
- **Stack:** Ruby on Rails, Vue.js, PostgreSQL, Redis | **RAM:** 4 GB | **Disk:** ~4 GB

### Zammad
- **URL:** http://zammad.usersim.alexkreidler.com
- **Login:** (pending setup)
- **Status:** ❌ Down (503 — all-in-one image entrypoint exits after setup; needs docker-compose multi-role approach)
- **What it is:** Helpdesk with multi-channel ticketing (email, chat, phone, social), knowledge base, SLA management, and extensive admin wizard.
- **Key agent flows:** Complete setup wizard → create tickets → assign agents → write knowledge base → configure triggers/automations → set SLAs
- **Seed data:** No — use REST API
- **Stack:** Ruby on Rails, PostgreSQL, Elasticsearch, Redis, Memcached | **RAM:** 4 GB | **Disk:** ~6 GB

---

## 📧 Email & Newsletters

### Listmonk
- **URL:** http://listmonk.usersim.alexkreidler.com
- **Login:** `admin` / `admin`
- **Status:** ✅ Live
- **What it is:** High-performance newsletter manager. Single Go binary. Campaign creation, subscriber management, template builder, analytics.
- **Key agent flows:** Configure SMTP → create mailing list → import subscribers (CSV) → create campaign → write content (WYSIWYG/Markdown/HTML) → schedule/send → view stats
- **Seed data:** No — import CSV or use API
- **Stack:** Go, Vue.js, PostgreSQL | **RAM:** 512 MB | **Disk:** ~1 GB

---

## 📅 Scheduling & Booking

### Easy!Appointments
- **URL:** http://appointments.usersim.alexkreidler.com
- **Login:** Setup wizard on first visit
- **Status:** ✅ Live
- **What it is:** Appointment scheduler for service businesses (clinics, salons, consultants). Customers select service → provider → date/time → book.
- **Key agent flows:** Select service → choose provider → navigate date picker → select time slot → fill customer details (name, phone, email) → confirm booking
- **Seed data:** Yes — CLI seed adds initial providers, services, admin
- **Stack:** PHP, MySQL | **RAM:** 512 MB | **Disk:** ~500 MB

---

## ☁️ Cloud & Collaboration

### Nextcloud
- **URL:** http://nextcloud.usersim.alexkreidler.com
- **Login:** `admin` / `admin123`
- **Status:** ✅ Live
- **What it is:** Self-hosted Google Workspace alternative. Files, calendar, contacts, collaborative editing, Talk (chat/video), and 200+ apps.
- **Key agent flows:** Upload/download files → create share links (password, expiration) → create calendar events → edit documents collaboratively → install apps → manage users
- **Seed data:** Partial — starter files for new users
- **Stack:** PHP, Vue.js, SQLite (demo mode) | **RAM:** 512 MB | **Disk:** ~2 GB

---

## 🗃️ Low-Code & Databases

### NocoDB
- **URL:** http://nocodb.usersim.alexkreidler.com
- **Login:** Sign up on first visit
- **Status:** ✅ Live
- **What it is:** Airtable alternative. 25+ field types, grid/kanban/gallery/form/calendar views, auto-generated REST API.
- **Key agent flows:** Create base → add table → define fields → enter records → switch to kanban view → build form view → share form link → filter/sort/group records
- **Seed data:** Partial — `nocodb-seed` repo + templates gallery
- **Stack:** TypeScript, Vue.js, Node.js, SQLite | **RAM:** 1 GB | **Disk:** ~1 GB

---

## 🐘 Social Networks

### Mastodon
- **URL:** http://mastodon.usersim.alexkreidler.com (redirects to HTTPS)
- **Login:** Register at `/auth/sign_in`
- **Status:** ✅ Live
- **What it is:** Federated Twitter/X alternative. Posts, boosts, favorites, polls, content warnings, hashtags, lists, federation via ActivityPub.
- **Key agent flows:** Register → set up profile (avatar, bio) → compose post (media, poll, CW) → follow users → boost/favorite → browse timelines → manage lists → adjust preferences
- **Seed data:** Minimal — `db:seed` creates admin only
- **Stack:** Ruby on Rails, React/Redux, PostgreSQL, Redis | **RAM:** 2 GB | **Disk:** ~5 GB

---

## 📈 Status Overview

| Status | Count | Apps |
|--------|-------|------|
| ✅ Live | 21 | Metabase, Kanboard, NocoDB, Ghost, Listmonk, Grafana, BookStack, Easy!Appointments, Nextcloud, PrestaShop, Invoice Ninja, Twenty CRM, Plausible, Chatwoot, Bagisto, Mattermost, Mastodon, OpenProject, Taiga, Plane, Huly |
| ❌ Down | 4 | Rocket.Chat (503 — OOM), ERPNext (500 — install failed), Zammad (503 — entrypoint issue), Discourse (503 — needs discourse_docker launcher) |

---

## 🏃 Quickest Demos (best for first UserSim run)

These have the richest seed data and most interesting agent flows out of the box:

| App | Why | Persona idea |
|-----|-----|-------------|
| **PrestaShop** | Full demo shop, multi-step checkout | "Martha, 68, buying a birthday gift under $50" |
| **Metabase** | Sample DB + dashboards ready to explore | "Raj, 29, building a sales dashboard for his team" |
| **OpenProject** | Auto-seeded Gantt charts and boards | "Alex, PM, trying to reschedule a milestone" |
| **Easy!Appointments** | Clean booking flow, minimal setup | "Elderly patient booking a dentist appointment" |
| **BookStack** | Rich WYSIWYG editor + search | "New employee finding the onboarding docs" |
| **Taiga** | Sprint planning with story points | "Scrum master setting up a 2-week sprint" |

---

## 💻 Resource Summary

| Tier | Apps | RAM | Est. Cost/mo |
|------|------|-----|-------------|
| **Lightweight** (10) | Kanboard, Easy!Appointments, BookStack, Listmonk, NocoDB, Ghost, Nextcloud, Grafana, Plausible, Bagisto | 8 GB | ~$40-60 |
| **Medium** (9) | PrestaShop, Twenty, Invoice Ninja, Mattermost, Mastodon, Chatwoot, Metabase, Taiga, Plane | 20 GB | ~$80-120 |
| **Heavy** (3 live) | OpenProject, Huly + ❌ ERPNext, Discourse, Zammad, Rocket.Chat | 32 GB | ~$120-180 |

### ❌ Down apps — what's been done and what's left

| App | Resources bumped | What changed | Remaining issue |
|-----|-----------------|--------------|-----------------|
| **Rocket.Chat** | 768 Mi -> 3 Gi (app), 512 Mi -> 1 Gi (mongo) | Bumped memory limits | Mongo replica set init job can't connect — needs manual `rs.initiate()` |
| **ERPNext** | 1.5 Gi -> 3 Gi (app), 512 Mi -> 1 Gi (MariaDB), port fixed 8080->8000 | Gunicorn now running on :8000 | No Frappe site initialized — needs `bench new-site` run |
| **Zammad** | 768 Mi -> 1.5 Gi (rails), 512 Mi -> 1 Gi (ES), added scheduler+websocket containers | Switched to multi-container, fixed ES to `docker.elastic.co` image, fixed `command`->`args` for entrypoint | Init container still crashlooping — shared volume permission issue |
| **Discourse** | 1.5 Gi -> 3 Gi (app), 256 Mi -> 512 Mi (PG), added sidekiq container | Switched from Bitnami (paywalled) to official `discourse/discourse:2026.1.3` | `db:migrate` failing in init container — env var format mismatch |
