# Demo URLs: Real-World Sector Apps (32 Applications)

> Generated 2026-05-09. Companion to `usersim-target-apps-v2.md` and `docker-infrastructure-report-v2.md`.

---

## Fully open -- no login needed

| App | Category | Demo URL | Notes |
|-----|----------|----------|-------|
| Saleor | E-commerce | https://demo.saleor.io | Storefront browsable; admin requires Saleor Cloud signup |
| Medusa | E-commerce | https://next.medusajs.com/us | Next.js storefront browsable; admin requires self-host |
| Home Assistant | Home Automation | https://demo.home-assistant.io | Fully interactive UI with simulated devices |
| CKAN | Data Portal | https://demo.ckan.org | Browse/search/download datasets freely; login only for publishing |
| Ghostfolio | Portfolio Tracking | https://ghostfol.io/en/demo | View demo portfolio; anonymous token signup for full access |
| Lemmy | Social / Reddit alt | https://lemmy.ml / https://lemmy.world | Browse posts/communities freely; account needed to post/vote |

---

## Login with demo credentials

| App | Category | Demo URL | Credentials | Resets |
|-----|----------|----------|-------------|--------|
| QloApps | Hotel Booking | https://demo.qloapps.com/ | Shown per-instance after generation | ~60 min |
| OpenEMR | Healthcare EHR | https://one.openemr.io/d/openemr | `admin` / `pass` | Daily 8:30 UTC |
| OpenEMR Patient Portal | Healthcare | https://one.openemr.io/d/openemr/portal | (patient logins in demo data) | Daily |
| Bahmni | Hospital System | https://www.bahmni.org/demo | `superman` / `Admin123` | Periodic |
| Moodle | LMS | https://sandbox.moodledemo.net/ | `teacher` / `moodle` (also `student`, `admin`) | Hourly |
| OpenCATS | Applicant Tracking | https://demo.opencats.org/ | `demo` / `demo` | -- |
| Firefly III | Personal Finance | https://demo.firefly-iii.org | `demo@firefly` / `demo` | -- |
| Decidim | Civic Participation | https://try.decidim.org | `admin@example.org` / `decidim123456789` | -- |
| CiviCRM | Nonprofit CRM | https://d10-master.demo.civicrm.org | `demo` / `demo` | Periodic |
| wger | Fitness Tracker | https://wger.de/ | Free registration; Docker: `admin` / `adminadmin` | -- |
| Koha (OPAC) | Library | https://staffdemo.kohasupport.com/ | Credentials on login page | Hourly |
| openIMIS | Insurance | https://demo.openimis.org | `Admin` / `admin123` | Daily |
| LubeLogger | Vehicle Maintenance | https://demo.lubelogger.com | `test` / `1234` | Every 20 min |
| alf.io | Conference Ticketing | https://demo.alf.io | Any email / any password (auto-creates admin) | -- |
| Osclass | Classifieds | https://osclass-classifieds.com/demo | Create on site | Weekly |
| LibreBooking | Resource Booking | https://librebooking-demo.fly.dev/Web/ | `admin` / `demoadmin` | Every 20 min |
| Calibre-Web | eBook Library | Cloudron demo (cloudron.io) | `cloudron` / `cloudron` | -- |
| TastyIgniter | Restaurant Ordering | https://demo.tastyigniter.com | Credentials on demo page | -- |
| Eventyay | Event Management | https://eventyay.com | Browse events freely; organizer requires signup | -- |

---

## Signup required (free account, no shared demo creds)

| App | Category | URL | Notes |
|-----|----------|-----|-------|
| Hi.Events | Event Ticketing | https://demo.hi.events | Create free account to access dashboard |
| Open edX | LMS | https://sandbox.openedx.org/ | Account creation required for full interaction |
| OpnForm | Form Builder | https://opnform.com | Free signup; homepage has embeddable interactive form |
| Penpot | Design Tool | https://design.penpot.app/ | Free signup required; no anonymous browse |

---

## No public demo -- self-host only

| App | Category | Notes |
|-----|----------|-------|
| PeelJobs | Job Board | Production site at peeljobs.com but no shared demo |
| MicroRealEstate | Property Mgmt | Docker compose only |
| Fleetbase | Logistics | Book guided demo or free cloud trial at fleetbase.io |
| Karrio | Shipping API | Cloud API requires auth; self-host for full access |

---

## Summary

**22 of 32 apps** have publicly accessible demos (no-login or with credentials).

**Best demos for hackathon testing (richest flows, easiest access):**

| App | Why it's great for live testing |
|-----|-------------------------------|
| QloApps | Fresh instance per session, full hotel booking flow |
| OpenEMR | Patient portal + EHR, rich multi-step forms |
| Moodle | Multiple role logins (student/teacher/admin), resets hourly |
| Firefly III | Pre-populated financial data, form-heavy |
| Decidim | Civic participation: proposals, voting, budgets |
| Home Assistant | Fully interactive with simulated smart devices |
| Saleor | Modern e-commerce storefront, multi-step checkout |
| LubeLogger | Clean CRUD forms, resets every 20 min (safe to experiment) |
