Here are the demo URLs. Let me present these results and then start on your infrastructure report.

**Fully open — no login needed:**

| App | Demo URL | Notes |
|-----|----------|-------|
| OpenCart | https://demo.opencart.com/ | Storefront browsable; admin at `/admin/` with `demo`/`demo` |
| Spree Commerce | https://demo.spreecommerce.org/ | Storefront open; admin at `/admin` with `spree@example.com`/`spree123` |
| PrestaShop | https://demo.prestashop.com/ | Auto-generates temp instance with full front+back office |
| Bagisto | https://commerce.bagisto.com/ | Storefront open; admin at `/admin/login` with `admin@example.com`/`admin123` |
| Invoice Ninja | https://react.invoicing.co/demo | Auto-logs into demo workspace |
| Grafana | https://play.grafana.org/ | Hundreds of sample dashboards, fully interactive |
| Plausible | https://plausible.io/plausible.io | Live analytics of their own site |
| Discourse | https://try.discourse.org/ | Browse freely, quick sign-up to post |
| Mastodon | https://mastodon.social/ | Browse public timelines freely |
| BookStack | https://demo.bookstackapp.com/ | Browse open; edit with `admin@example.com`/`password`. Resets every 30min |
| Easy!Appointments | https://demo.easyappointments.org/ | Public booking page works without login |

**Login with demo credentials:**

| App | Demo URL | Credentials |
|-----|----------|-------------|
| Twenty | https://demo.twenty.com/ | `noah@demo.dev` / `Applecar2025` |
| Ghost | https://play-with-ghost.com/ | `relations@firepress.org` / `firepress1` (third-party) |
| Listmonk | https://demo.listmonk.app/ | Public archive open; admin likely `listmonk`/`listmonk` |
| Nextcloud | https://try.nextcloud.com/ | Auto-generated account, 60-min session |
| Zammad | https://zammaddemo.agitos.de/ | Third-party demo |

**No public demo — requires sign-up or self-host:**
Plane, Huly, Taiga, ERPNext, Rocket.Chat, Mattermost, Metabase, Chatwoot, Cal.com, NocoDB, Kanboard

---

Now let me research the Docker/infra requirements for all of these.

Both reports are now saved. Here's the executive summary:

---

**Docker pull readiness — 18 of 28 have official images you can just pull:**
`prestashop/prestashop`, `webkul/bagisto`, `twentycrm/twenty`, `frappe/erpnext`, `invoiceninja/invoiceninja`, `rocket.chat`, `mattermost/mattermost-team-edition`, `ghost`, `metabase/metabase`, `grafana/grafana`, `plausible/analytics`, `chatwoot/chatwoot`, `calcom/cal.com`, `nextcloud`, `listmonk/listmonk`, `nocodb/nocodb`, `kanboard/kanboard`, `alextselegidis/easyappointments`

**Easiest single-command deploys:**
- `docker run metabase/metabase` — includes sample DB + dashboards
- `docker run nocodb/nocodb` — uses SQLite, no external DB
- `docker run kanboard/kanboard` — 200MB image, login admin/admin
- `docker run ghost` — up in seconds
- `docker run nextcloud` — with starter files

**Best seed data out of the box:**
| App | How | Quality |
|-----|-----|---------|
| Metabase | Built-in Sample Database + example dashboards | Excellent — populated on first launch |
| PrestaShop | `PS_DEMO_MODE=1` env var | Excellent — full demo shop |
| OpenProject | Auto-seeds demo projects on first launch | Excellent — Gantt charts, boards, work packages |
| Spree | `rake spree_sample:load` | Good — sample products + images |
| ERPNext | Setup wizard "Demo Setup" option | Good — sample company with transactions |
| Invoice Ninja | `artisan ninja:create-test-data` | Good — invoices, clients, payments |
| Cal.com | `yarn db-seed` | Good — test users + event types |
| Taiga | `manage.py sample_data` | Good — demo projects |

**No seed data (manual or API work needed):**
Plane, Huly, Rocket.Chat, Mattermost, Chatwoot, Zammad, Kanboard, BookStack, Plausible, Mastodon

**Resource tiers to run everything:**
| Tier | Apps | RAM | Est. Cost/mo |
|------|------|-----|---|
| Lightweight (12) | Kanboard, Easy!Appointments, BookStack, Listmonk, NocoDB, Ghost, Nextcloud, Grafana, Metabase, OpenCart, Plausible, Bagisto | 8 GB | ~$40-60 |
| Medium (10) | PrestaShop, Spree, Twenty, Invoice Ninja, Cal.com, Mattermost, Rocket.Chat, Mastodon, Chatwoot, Taiga | 16 GB | ~$80-120 |
| Heavy (6) | ERPNext, OpenProject, Plane, Huly, Discourse, Zammad | 32 GB | ~$120-180 |

Full details with docker-compose snippets and quick-start commands are in `/Users/al/comphack/docker-infrastructure-report.md`.