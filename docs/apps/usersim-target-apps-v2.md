# UserSim Target Applications: Real-World Sector Apps for AI-Powered UX Testing

A curated list of 32 open source web applications spanning 16 real-world economic sectors. These represent the kinds of tasks AI agents will actually perform using browser automation -- booking appointments, shopping online, enrolling in courses, filing forms, ordering food, etc.

Every app has a web UI with meaningful multi-step user flows that map naturally to UserSim's persona system.

---

## 1. E-Commerce

### 1.1 Saleor
- **GitHub:** https://github.com/saleor/saleor
- **Stars:** ~23k
- **Category:** Headless e-commerce with full Next.js storefront
- **Tech Stack:** Python/Django (API), React/Next.js (storefront), TypeScript (dashboard)
- **Key User Flows:**
  - Storefront: browse product catalog, use faceted search/filters, view product details, select variants (size/color), add to cart, multi-step checkout (address, shipping, payment), guest vs authenticated checkout
  - Account: registration, login, order history, address management
  - Dashboard: product management, order processing, discount creation
- **Demo/Setup:** Docker; storefront demo at demo.saleor.io
- **Why it's great for UserSim:** Modern e-commerce with country-aware international address forms, multi-step checkout, and complex filtering. Agents can simulate shopping across different personas (price-sensitive shopper, gift buyer, international customer).

### 1.2 Medusa
- **GitHub:** https://github.com/medusajs/medusa
- **Stars:** ~33k
- **Category:** Modular headless commerce with Next.js storefront
- **Tech Stack:** TypeScript/Node.js, Next.js (storefront)
- **Key User Flows:**
  - Storefront: browse products, filter by category/collection, view product page, select options, add to cart, one-page or multi-step checkout, enter shipping/billing, select payment
  - Account: registration, order tracking, address book
- **Demo/Setup:** Docker; storefront demo at next.medusajs.com/us
- **Why it's great for UserSim:** Clean modern checkout flow. Multi-region/multi-currency support creates locale-specific UX scenarios.

---

## 2. Booking / Scheduling

### 2.1 LibreBooking
- **GitHub:** https://github.com/LibreBooking/app
- **Stars:** ~715
- **Category:** Resource/room booking system
- **Tech Stack:** PHP, Bootstrap
- **Key User Flows:**
  - Browse available resources (rooms, desks, equipment), select date/time range, fill reservation form, confirm booking
  - Manage recurring reservations, view/cancel existing bookings
  - Admin: configure resources, manage users, set booking rules
- **Demo/Setup:** Docker; demo at librebooking-demo.fly.dev (resets every 20 min)
- **Why it's great for UserSim:** Calendar grid with drag-to-book interaction. Classic enterprise booking UX that many offices use -- agents can simulate "book a meeting room for Thursday afternoon."

---

## 3. Travel / Hospitality

### 3.1 QloApps
- **GitHub:** https://github.com/Qloapps/QloApps
- **Stars:** ~13k
- **Category:** Hotel management and reservation system
- **Tech Stack:** PHP (PrestaShop-based), jQuery
- **Key User Flows:**
  - Guest: search by dates/location/guests, browse available rooms with photos and pricing, select room type, fill guest details (name, address, phone), select payment, confirm reservation, view booking confirmation
  - Account: registration, booking history, profile management
  - Admin: room/rate management, booking processing, channel management
- **Demo/Setup:** Docker; demo at demo.qloapps.com (fresh instance per session, ~60 min)
- **Why it's great for UserSim:** Full hotel booking flow identical to real hotel websites. Date picker, room comparison, multi-step reservation form. Perfect for "Martha, 68, trying to book a room for her anniversary trip" persona.

---

## 4. Healthcare

### 4.1 OpenEMR
- **GitHub:** https://github.com/openemr/openemr
- **Stars:** ~5.1k
- **Category:** Electronic Health Records with patient portal
- **Tech Stack:** PHP, jQuery, Bootstrap
- **Key User Flows:**
  - Patient portal: register account, log in, view appointment schedule, book new appointment, send secure message to provider, view lab results, view/download prescriptions, update demographics, fill intake forms, make online payment
  - Clinical: patient chart, encounter documentation, e-prescribing, lab orders
  - Admin: user management, facility configuration, billing setup
- **Demo/Setup:** Docker (46 CI workflows); demo at one.openemr.io with `admin`/`pass`
- **Why it's great for UserSim:** High-stakes UX where confusion has real consequences. Dense medical forms, complex intake workflows, and a patient portal with multiple distinct tasks. Best CI pipeline of any candidate.

### 4.2 Bahmni
- **GitHub:** https://github.com/Bahmni/bahmni-docker
- **Stars:** ~350 (Docker repo)
- **Category:** Hospital Information System (OpenMRS + OpenELIS + Odoo)
- **Tech Stack:** Java (OpenMRS), React (patient portal), Python (Odoo)
- **Key User Flows:**
  - Patient portal: login via mobile OTP, view past visits, download prescriptions/lab reports as PDF
  - Registration: multi-step patient registration with demographics, ID verification
  - Appointments: schedule, view, cancel
  - Clinical: consultation, lab orders, pharmacy
- **Demo/Setup:** Docker; demo at bahmni.org/demo with `superman`/`Admin123`
- **Why it's great for UserSim:** Modern React + Carbon Design System patient portal. Multi-step registration is a realistic form-filling scenario for agents.

---

## 5. Education / LMS

### 5.1 Moodle
- **GitHub:** https://github.com/moodle/moodle
- **Stars:** ~7k
- **Category:** Learning Management System (world's most deployed)
- **Tech Stack:** PHP, JavaScript
- **Key User Flows:**
  - Student: create account, enroll in course, navigate course page, download materials, submit assignments (file upload, text entry), take timed quizzes (multiple choice, essay, matching), participate in forums, view grades, check calendar, send messages
  - Teacher: create course, add activities, grade submissions, manage enrollment
  - Admin: site configuration, plugin management, user management
- **Demo/Setup:** Docker; demo at sandbox.moodledemo.net (resets hourly, `teacher`/`moodle`)
- **Why it's great for UserSim:** Deeply nested navigation, extremely rich interactive forms. Quiz-taking flow (timed, multiple question types, navigation between questions) is a uniquely complex UX scenario.

### 5.2 Open edX (via Tutor)
- **GitHub:** https://github.com/openedx/openedx-platform
- **Stars:** ~8k
- **Category:** MOOC platform (Harvard/MIT, 70M+ users)
- **Tech Stack:** Python/Django, React, Node.js
- **Key User Flows:**
  - Learner: browse course catalog, read descriptions, enroll, watch video lectures, complete interactive exercises (drag-and-drop, multiple choice, code graders), post in forums, track progress, earn certificates
  - Instructor: create course content, manage grades, view analytics
- **Demo/Setup:** Docker via Tutor (`tutor local launch`); sandbox at sandbox.openedx.org
- **Why it's great for UserSim:** Production-grade MOOC used by major universities. Interactive exercise types (drag-and-drop, code grading) test complex UI interactions. Great scenario: "Non-English speaker enrolling in a data science course."

---

## 6. Job Boards / Recruiting

### 6.1 OpenCATS
- **GitHub:** https://github.com/opencats/OpenCATS
- **Stars:** ~674
- **Category:** Applicant Tracking System
- **Tech Stack:** PHP, jQuery
- **Key User Flows:**
  - Candidate: browse job listings, view descriptions, create account, upload resume, fill application form (personal info, work history, education), submit application, track status
  - Recruiter: post jobs, review applications, schedule interviews, manage pipeline
- **Demo/Setup:** Docker; demo at demo.opencats.org (`demo`/`demo`)
- **Why it's great for UserSim:** Multi-step job application form is a classic agent task. Resume upload + form filling + submission is a complete end-to-end flow.

### 6.2 PeelJobs
- **GitHub:** https://github.com/MicroPyramid/opensource-job-portal
- **Stars:** ~471
- **Category:** Job board with Elasticsearch search
- **Tech Stack:** Python/Django, Elasticsearch
- **Key User Flows:**
  - Candidate: search jobs with advanced filters (location, salary, skills, experience), view job details, create profile, upload resume, apply, set up alerts, track applications
  - Recruiter: post jobs, manage applications
- **Demo/Setup:** No Docker (manual Django setup); production site at peeljobs.com
- **Why it's great for UserSim:** Elasticsearch-powered job search with faceted filtering. Agent scenario: "Software engineer looking for remote Python jobs paying over $150k."

---

## 7. Food / Restaurant

### 7.1 TastyIgniter
- **GitHub:** https://github.com/tastyigniter/TastyIgniter
- **Stars:** ~3.6k
- **Category:** Restaurant online ordering and table reservation
- **Tech Stack:** PHP/Laravel
- **Key User Flows:**
  - Customer: browse menu (categories, items, modifiers), customize order (toppings, size, special instructions), add to cart, select delivery or pickup, enter delivery address, choose payment, place order, track status
  - Table reservation: select date/time, party size, special requests, confirm
  - Admin: menu management, order processing, delivery zone configuration
- **Demo/Setup:** Community Docker; demo at demo.tastyigniter.com
- **Why it's great for UserSim:** Restaurant ordering is a universally understood flow. Order customization (modifiers, special instructions) creates rich form interactions. Great for "impatient mobile user ordering lunch" persona.

---

## 8. Event Ticketing

### 8.1 Hi.Events
- **GitHub:** https://github.com/HiEventsDev/Hi.Events
- **Stars:** ~3.8k
- **Category:** Event management and ticket sales
- **Tech Stack:** PHP/Laravel (backend), React (frontend)
- **Key User Flows:**
  - Attendee: browse events, view details, select ticket type and quantity, fill attendee information, enter payment (Stripe), complete purchase, receive QR code
  - Organizer: create event, configure tickets (free/paid/donation/tiered), customize forms, view analytics, check in attendees
- **Demo/Setup:** Docker (all-in-one compose); demo at demo.hi.events
- **Why it's great for UserSim:** Clean ticket purchase flow with Stripe checkout. Embeddable widget tests embedded UI scenarios. Agent scenario: "Buy 2 tickets to a tech conference."

### 8.2 Eventyay
- **GitHub:** https://github.com/fossasia/eventyay
- **Stars:** ~1.6k
- **Category:** Event management with ticketing and video
- **Tech Stack:** Python (backend), JavaScript (frontend)
- **Key User Flows:**
  - Attendee: browse events, view schedule/speakers, select tickets, add to cart, fill details, checkout, view/download tickets
  - Speaker: submit talk proposals, manage submissions
  - Organizer: create events, manage schedule, configure ticketing
- **Demo/Setup:** Docker; standalone image available; eventyay.com for browsing
- **Why it's great for UserSim:** Based on Pretix (proven ticketing). Speaker submission flow adds a unique form-heavy scenario beyond just ticket buying.

### 8.3 alf.io
- **GitHub:** https://github.com/alfio-event/alf.io
- **Stars:** ~1.6k
- **Category:** Conference/event ticket reservation
- **Tech Stack:** Java/Spring Boot, Angular
- **Key User Flows:**
  - Attendee: browse events, choose ticket category, enter details, select payment (Stripe/PayPal/bank/on-site), complete purchase, receive email ticket
  - Organizer: create events, configure ticket categories, manage check-ins, view sales reports
- **Demo/Setup:** Docker; demo at demo.alf.io (any email/password creates temp admin)
- **Why it's great for UserSim:** PCI-compliant multi-payment checkout. Conference registration is a common real-world agent task.

---

## 9. Personal Finance

### 9.1 Firefly III
- **GitHub:** https://github.com/firefly-iii/firefly-iii
- **Stars:** ~23k
- **Category:** Personal finance manager
- **Tech Stack:** PHP/Laravel
- **Key User Flows:**
  - Setup: create account, configure bank accounts, set opening balances
  - Daily use: enter transactions (amount, category, description, date), create budgets with spending limits, set up recurring transactions, create rules for automatic categorization
  - Reporting: expense by category, income vs expense, net worth over time
  - Import: bank CSV import, mapping columns to fields
- **Demo/Setup:** Docker; demo at demo.firefly-iii.org (`demo@firefly`/`demo`)
- **Why it's great for UserSim:** Form-heavy workflow ideal for testing data entry UX. Budget creation and rule configuration involve complex conditional forms. Pre-populated demo data makes agent testing meaningful.

### 9.2 Ghostfolio
- **GitHub:** https://github.com/ghostfolio/ghostfolio
- **Stars:** ~8.4k
- **Category:** Wealth management / portfolio tracking
- **Tech Stack:** TypeScript, Angular, NestJS
- **Key User Flows:**
  - Setup: create account, add investment accounts
  - Daily use: record buy/sell transactions (ticker, quantity, price, date, fees), view portfolio dashboard, analyze performance by asset class/region/sector, track dividends
  - Import: transaction import from broker exports
- **Demo/Setup:** Docker; demo at ghostfol.io/en/demo (anonymous token signup)
- **Why it's great for UserSim:** Financial data entry with ticker symbol lookup, date pickers, and numeric precision. Dashboard with interactive charts. Agent scenario: "Record buying 50 shares of AAPL at $195."

---

## 10. Government / Civic

### 10.1 Decidim
- **GitHub:** https://github.com/decidim/decidim
- **Stars:** ~1.7k
- **Category:** Participatory democracy platform (used by Barcelona, Helsinki, etc.)
- **Tech Stack:** Ruby on Rails
- **Key User Flows:**
  - Citizen: register, browse active participation processes, submit proposals, vote on proposals, participate in budgets (allocate funds), fill consultation surveys, sign up for meetings, comment on proposals, verify identity
  - Admin: create participatory processes, manage phases, moderate content
- **Demo/Setup:** Docker (53 CI workflows); demo at try.decidim.org (`admin@example.org`/`decidim123456789`)
- **Why it's great for UserSim:** Unique civic participation flows (proposal submission, participatory budgeting) that no other app category offers. Multi-step civic forms are a great test for diverse personas.

### 10.2 CKAN
- **GitHub:** https://github.com/ckan/ckan
- **Stars:** ~5k
- **Category:** Open data portal (powers data.gov, open.canada.ca)
- **Tech Stack:** Python, JavaScript
- **Key User Flows:**
  - Public: search datasets by keyword/organization/format, browse organizations, filter by topic/license/format, preview data, download in multiple formats, view visualizations
  - Publisher: create account, submit dataset for publishing, add resources, set metadata
  - API: use API explorer
- **Demo/Setup:** Docker; demo at demo.ckan.org (browse freely)
- **Why it's great for UserSim:** Government data portal UX -- search, filter, download. Agent scenario: "Find and download the latest census data in CSV format." Tests search and filtering efficiency.

### 10.3 OpnForm
- **GitHub:** https://github.com/OpnForm/OpnForm
- **Stars:** ~3.3k
- **Category:** Form builder (Typeform/Google Forms alternative)
- **Tech Stack:** PHP/Laravel (API), Vue/Nuxt (frontend)
- **Key User Flows:**
  - Form filler: navigate to published form, complete multi-step form with various field types (text, dropdowns, checkboxes, file uploads, conditional logic), submit, view confirmation
  - Form creator: create form, add fields, set up conditional logic, configure validation, publish, review submissions
- **Demo/Setup:** Docker; cloud at opnform.com (free signup)
- **Why it's great for UserSim:** Simulates any government/intake form with conditional logic. The form-filling experience is the core agent task. Multi-step forms with branching logic test agent decision-making.

---

## 11. Classifieds / Marketplace

### 11.1 Osclass
- **GitHub:** https://github.com/mindstellar/Osclass
- **Stars:** ~1.2k (including original)
- **Category:** General-purpose classifieds platform
- **Tech Stack:** PHP, jQuery
- **Key User Flows:**
  - Buyer: browse categories, search with location/keyword filters, view ad details with photos, contact seller via form
  - Seller: create account, post new classified ad (multi-step: category, title, description, photos, price, location), manage listings
  - Admin: manage categories, moderate listings, configure site
- **Demo/Setup:** Docker; demo at osclass-classifieds.com/demo (resets weekly)
- **Why it's great for UserSim:** Multi-step ad posting with photo upload is a rich agent workflow. Search with location/category filtering tests discovery UX. Agent scenario: "Post a used bicycle for sale with 3 photos."

---

## 12. Real Estate

### 12.1 MicroRealEstate
- **GitHub:** https://github.com/microrealestate/microrealestate
- **Stars:** ~1k
- **Category:** Property management (landlord + tenant portals)
- **Tech Stack:** Node.js (microservices), React (frontends)
- **Key User Flows:**
  - Tenant portal: log in, view lease details, check rent history, view property info, submit maintenance requests
  - Landlord portal: add properties, create leases, track payments, manage tenants, generate PDF documents
- **Demo/Setup:** Docker (11-service compose); self-host only
- **Why it's great for UserSim:** Dual-portal system (tenant vs landlord) provides two distinct user perspectives. Maintenance request submission and lease management are realistic agent tasks.

---

## 13. Logistics / Shipping

### 13.1 Fleetbase
- **GitHub:** https://github.com/fleetbase/fleetbase
- **Stars:** ~1.9k
- **Category:** Logistics and supply chain operating system
- **Tech Stack:** PHP (API), Ember.js (console)
- **Key User Flows:**
  - Create shipments, assign drivers, track deliveries in real-time, manage warehouse inventory, create/update orders, configure routes, manage fleet vehicles, generate reports
- **Demo/Setup:** Docker (8-service compose); self-host or cloud trial at fleetbase.io
- **Why it's great for UserSim:** Professional logistics console with map views, tabbed management panels, and complex order creation forms. Tests agent interaction with data-heavy dashboards.

### 13.2 Karrio
- **GitHub:** https://github.com/karrioapi/karrio
- **Stars:** ~723
- **Category:** Multi-carrier shipping API with dashboard
- **Tech Stack:** Python (API), React (dashboard)
- **Key User Flows:**
  - Create shipping labels, compare rates across carriers (FedEx/UPS/DHL/USPS), track packages, manage carrier connections, generate documents, configure webhooks
- **Demo/Setup:** Docker; self-host only. Default: `admin@example.com`/`demo`
- **Why it's great for UserSim:** Rate comparison flow (enter package dimensions, see carrier options, select cheapest) is a clear decision-making task for agents.

---

## 14. Nonprofit / Fundraising

### 14.1 CiviCRM
- **GitHub:** https://github.com/civicrm/civicrm-core
- **Stars:** ~738
- **Category:** Constituent relationship management for nonprofits
- **Tech Stack:** PHP
- **Key User Flows:**
  - Donor: register for events, make donations (one-time/recurring), manage membership
  - Staff: create/manage contacts, record donations, process membership renewals, create campaigns, manage volunteers, send communications, generate reports
- **Demo/Setup:** Docker; demos at d10-master.demo.civicrm.org (`demo`/`demo`)
- **Why it's great for UserSim:** Donation forms, event registration, and membership renewals are real-world forms that agents will fill. 14,000+ nonprofits use this -- UX improvements have massive reach.

---

## 15. Fitness / Wellness

### 15.1 wger
- **GitHub:** https://github.com/wger-project/wger
- **Stars:** ~6k
- **Category:** Workout and nutrition tracker
- **Tech Stack:** Python/Django
- **Key User Flows:**
  - Create workout plans, log exercises with sets/reps/weight, track nutrition and calories, record body measurements, browse exercise database, create custom exercises, view progress charts
- **Demo/Setup:** Docker; public instance at wger.de (free registration). Docker default: `admin`/`adminadmin`
- **Why it's great for UserSim:** Workout logging involves repetitive form entry (sets, reps, weight for each exercise). Nutrition tracking requires food search + quantity entry. Good for testing efficiency of data entry UX.

---

## 16. Library / Media

### 16.1 Calibre-Web
- **GitHub:** https://github.com/janeczku/calibre-web
- **Stars:** ~17k
- **Category:** Web-based ebook library
- **Tech Stack:** Python/Flask
- **Key User Flows:**
  - Browse/search book catalog by title/author/tag, view book details with cover art, download books in various formats (EPUB, PDF, MOBI), read books in browser, send books to Kindle, manage shelves/categories
  - Admin: upload books, edit metadata, manage users
- **Demo/Setup:** Docker (`linuxserver/calibre-web`); Cloudron demo available
- **Why it's great for UserSim:** Library catalog search and book download is a clean, testable flow. Agent scenario: "Find a science fiction book published after 2020 and send it to my Kindle."

### 16.2 Koha
- **GitHub:** https://github.com/Koha-community/Koha
- **Stars:** ~562
- **Category:** Integrated library system (thousands of libraries worldwide)
- **Tech Stack:** Perl, JavaScript
- **Key User Flows:**
  - Patron (OPAC): search public catalog, view item availability, place holds, manage account, view checkout history, pay fines, submit purchase suggestions
  - Staff: check out/return items, manage patron accounts, catalog items, process acquisitions
- **Demo/Setup:** Docker (via koha-testing-docker); demo at staffdemo.kohasupport.com
- **Why it's great for UserSim:** Library catalog search with faceted filtering and hold placement is a distinct UX pattern. Agent scenario: "Find this book, check if it's available at my branch, and place a hold."

---

## 17. Insurance

### 17.1 openIMIS
- **GitHub:** https://github.com/openimis/openimis-dist_dkr
- **Stars:** ~16 (modular repos)
- **Category:** Social health insurance management (38.8M beneficiaries, 14 countries)
- **Tech Stack:** Python (backend), React (frontend)
- **Key User Flows:**
  - Enroll beneficiaries, manage insurance policies, submit/process claims, configure benefit packages, manage premium payments, generate reports, process renewals
- **Demo/Setup:** Docker (modular compose); demo at demo.openimis.org (`Admin`/`admin123`)
- **Why it's great for UserSim:** Insurance enrollment and claims processing are high-complexity form workflows. Agent scenario: "Enroll a new family in the health insurance plan and submit a claim for a hospital visit."

---

## 18. Design / Creative

### 18.1 Penpot
- **GitHub:** https://github.com/penpot/penpot
- **Stars:** ~47k
- **Category:** Design and prototyping (Figma alternative)
- **Tech Stack:** Clojure (backend), ClojureScript (frontend)
- **Key User Flows:**
  - Create projects/files, add/edit shapes and frames, manage layers, create/use components, set up interactive prototypes with transitions, export assets, manage design libraries, share for review
- **Demo/Setup:** Docker; cloud at design.penpot.app (free signup)
- **Why it's great for UserSim:** Browser-native design tool tests canvas-based interactions (drag, resize, property editing). Property panels are form-based and automatable. Agent scenario: "Create a wireframe with a header, navigation menu, and two-column layout."

---

## 19. Automotive

### 19.1 LubeLogger
- **GitHub:** https://github.com/hargata/lubelog
- **Stars:** ~2.5k
- **Category:** Vehicle service records and maintenance tracker
- **Tech Stack:** C#/.NET, JavaScript
- **Key User Flows:**
  - Add vehicles, log fuel fill-ups (mileage, cost, gallons), record service entries, record repair entries, set maintenance reminders, track expenses, generate cost reports, manage vehicle documents, configure recurring schedules
- **Demo/Setup:** Docker (single container, 256 MB); demo at demo.lubelogger.com (`test`/`1234`, resets every 20 min)
- **Why it's great for UserSim:** Straightforward CRUD forms with clear data entry patterns. Lightest app in the entire list. Agent scenario: "Log an oil change at 45,000 miles that cost $65."

---

## 20. Social / Community

### 20.1 Lemmy
- **GitHub:** https://github.com/LemmyNet/lemmy
- **Stars:** ~14k
- **Category:** Federated link aggregator (Reddit alternative)
- **Tech Stack:** Rust (backend), TypeScript/React (frontend)
- **Key User Flows:**
  - Register, create/join communities, submit posts (links/text/images), comment, upvote/downvote, search communities, manage profile, subscribe, sort/filter content
  - Moderation: manage community rules, handle reports
- **Demo/Setup:** Docker; live instances at lemmy.ml, lemmy.world (browse freely)
- **Why it's great for UserSim:** Reddit-like UX with community discovery, post creation, and comment threading. Agent scenario: "Find the programming community, create a post asking about Rust vs Go, and upvote the most helpful reply."

---

## 21. Energy / Home Automation

### 21.1 Home Assistant
- **GitHub:** https://github.com/home-assistant/core
- **Stars:** ~87k
- **Category:** Home automation platform
- **Tech Stack:** Python (backend), Lit/Polymer (frontend)
- **Key User Flows:**
  - Control smart devices (lights, thermostats, locks), create/edit automations (trigger + condition + action), monitor energy dashboards, configure integrations (2000+ devices), manage scenes, view device history, configure custom dashboards
- **Demo/Setup:** Docker; interactive demo at demo.home-assistant.io (no login needed)
- **Why it's great for UserSim:** Rich dashboard with customizable cards. Automation editor involves complex multi-step conditional logic. Energy dashboard with charts and statistics. Agent scenario: "Set up an automation that turns off all lights when no one is home."

---

## 22. Customer Support

*Chatwoot and Zammad are covered in the original `usersim-target-apps.md`. Key flows for reference:*
- **Chatwoot:** Submit tickets via chat widget, browse knowledge base, initiate live chat
- **Zammad:** Create support tickets, search knowledge base, track status

---

## Summary Table

| # | Name | Category | Stars | Demo Available | Complexity |
|---|------|----------|-------|----------------|------------|
| 1 | Saleor | E-commerce | ~23k | demo.saleor.io | High |
| 2 | Medusa | E-commerce | ~33k | next.medusajs.com | Medium-High |
| 3 | LibreBooking | Booking | ~715 | librebooking-demo.fly.dev | Low-Medium |
| 4 | QloApps | Hotel Booking | ~13k | demo.qloapps.com | High |
| 5 | OpenEMR | Healthcare | ~5.1k | one.openemr.io | Very High |
| 6 | Bahmni | Healthcare | ~350 | bahmni.org/demo | Very High |
| 7 | Moodle | LMS | ~7k | sandbox.moodledemo.net | Very High |
| 8 | Open edX | LMS | ~8k | sandbox.openedx.org | High |
| 9 | OpenCATS | Job Board | ~674 | demo.opencats.org | Medium |
| 10 | PeelJobs | Job Board | ~471 | peeljobs.com (prod) | Medium |
| 11 | TastyIgniter | Restaurant | ~3.6k | demo.tastyigniter.com | Medium-High |
| 12 | Hi.Events | Ticketing | ~3.8k | demo.hi.events | Medium |
| 13 | Eventyay | Events | ~1.6k | eventyay.com | Medium |
| 14 | alf.io | Ticketing | ~1.6k | demo.alf.io | Medium |
| 15 | Firefly III | Finance | ~23k | demo.firefly-iii.org | Medium-High |
| 16 | Ghostfolio | Finance | ~8.4k | ghostfol.io/en/demo | Medium |
| 17 | Decidim | Civic | ~1.7k | try.decidim.org | High |
| 18 | CKAN | Data Portal | ~5k | demo.ckan.org | Medium |
| 19 | OpnForm | Forms | ~3.3k | opnform.com | Medium |
| 20 | Osclass | Classifieds | ~1.2k | osclass-classifieds.com/demo | Medium |
| 21 | MicroRealEstate | Real Estate | ~1k | Self-host only | Medium |
| 22 | Fleetbase | Logistics | ~1.9k | Self-host only | High |
| 23 | Karrio | Shipping | ~723 | Self-host only | Medium-High |
| 24 | CiviCRM | Nonprofit | ~738 | d10-master.demo.civicrm.org | High |
| 25 | wger | Fitness | ~6k | wger.de | Medium |
| 26 | Calibre-Web | Library | ~17k | Cloudron demo | Low-Medium |
| 27 | Koha | Library | ~562 | staffdemo.kohasupport.com | High |
| 28 | openIMIS | Insurance | ~16+ | demo.openimis.org | High |
| 29 | Penpot | Design | ~47k | design.penpot.app | High |
| 30 | LubeLogger | Automotive | ~2.5k | demo.lubelogger.com | Low |
| 31 | Lemmy | Social | ~14k | lemmy.ml | Medium |
| 32 | Home Assistant | Energy/Home | ~87k | demo.home-assistant.io | High |

---

## Recommended Demo Scenarios for UserSim

These scenarios represent compelling, real-world agent tasks across diverse sectors:

1. **Hotel booking** (QloApps): "Find a room for 2 adults, July 15-18, under $200/night, and complete the reservation"
2. **E-commerce checkout** (Saleor): "Buy a medium blue t-shirt and have it shipped to a New York address"
3. **Course enrollment** (Moodle): "Enroll in the Introduction to Python course and submit the first assignment"
4. **Patient intake** (OpenEMR): "Log into the patient portal, fill out the new patient intake form, and book an appointment with Dr. Smith"
5. **Food ordering** (TastyIgniter): "Order a large pepperoni pizza with extra cheese, a side salad, and a Coke for delivery"
6. **Event tickets** (Hi.Events): "Buy 2 general admission tickets to the summer music festival"
7. **Job application** (OpenCATS): "Find a software engineering position, upload your resume, and complete the application"
8. **Budget setup** (Firefly III): "Create a monthly budget with categories for rent, groceries, and entertainment"
9. **Civic participation** (Decidim): "Submit a proposal for a new bike lane and vote on 3 other proposals"
10. **Vehicle maintenance** (LubeLogger): "Log today's oil change at 45,000 miles -- cost $65 at Jiffy Lube"
11. **Property management** (MicroRealEstate): "As a tenant, submit a maintenance request for a leaky faucet"
12. **Smart home** (Home Assistant): "Create an automation that dims the living room lights at 10 PM"

---

## Sector Coverage

| Sector | Apps | Best for Demo |
|--------|------|---------------|
| E-Commerce | Saleor, Medusa | Saleor (multi-step checkout) |
| Booking/Scheduling | LibreBooking | LibreBooking (calendar interaction) |
| Travel/Hospitality | QloApps | QloApps (hotel booking flow) |
| Healthcare | OpenEMR, Bahmni | OpenEMR (patient portal + intake) |
| Education | Moodle, Open edX | Moodle (quiz + assignment flows) |
| Jobs/Recruiting | OpenCATS, PeelJobs | OpenCATS (application form) |
| Food/Restaurant | TastyIgniter | TastyIgniter (order customization) |
| Events/Ticketing | Hi.Events, Eventyay, alf.io | Hi.Events (Stripe checkout) |
| Personal Finance | Firefly III, Ghostfolio | Firefly III (budget + transactions) |
| Government/Civic | Decidim, CKAN, OpnForm | Decidim (participation flows) |
| Classifieds | Osclass | Osclass (listing creation) |
| Real Estate | MicroRealEstate | MicroRealEstate (dual portals) |
| Logistics | Fleetbase, Karrio | Karrio (rate comparison) |
| Nonprofit | CiviCRM | CiviCRM (donation + event reg) |
| Fitness | wger | wger (workout logging) |
| Library/Media | Calibre-Web, Koha | Koha (catalog search + hold) |
| Insurance | openIMIS | openIMIS (enrollment + claims) |
| Design | Penpot | Penpot (canvas interaction) |
| Automotive | LubeLogger | LubeLogger (CRUD forms) |
| Social | Lemmy | Lemmy (post + comment) |
| Energy/Home | Home Assistant | Home Assistant (automation editor) |
| Customer Support | Chatwoot, Zammad (v1 report) | Chatwoot (live chat widget) |

---

## Selection Criteria

- **Excluded** internal developer tools (CI/CD, monitoring, databases)
- **Excluded** admin-only apps without consumer/user-facing flows
- **Excluded** apps without Docker support (except PeelJobs, included for sector coverage)
- **Prioritized** apps with: public demos, meaningful multi-step user flows, Docker/compose support, active maintenance, diverse economic sectors
- **Balanced** across 22 distinct real-world sectors
