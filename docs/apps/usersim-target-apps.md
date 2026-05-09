# UserSim Target Applications: Open Source Web Apps for AI-Powered UX Testing

A curated list of 28 open source web applications that ship complete, opinionated front-ends with meaningful user flows — ideal targets for UserSim's AI-powered UX testing. Every app on this list has a real UI you can point agents at and generate fix diffs against.

---

## 1. E-Commerce

### 1.1 OpenCart
- **GitHub:** https://github.com/opencart/opencart
- **Stars:** ~7.5k
- **Category:** Full-stack e-commerce platform
- **Tech Stack:** PHP, Twig templates, jQuery, Bootstrap
- **Key User Flows:**
  - Customer storefront: product browsing, category navigation, search with auto-suggest, product comparison, wishlist, cart, multi-step checkout (account, billing, shipping, payment, confirm), order tracking
  - Account: registration, login, address book, order history, returns, recurring payments, reward points
  - Admin back-office: product/category management, order processing, customer management, marketing (coupons, mail), reports (sales, products, customers), extension marketplace
- **Demo/Setup:** Docker; official demo at demo.opencart.com (storefront + admin)
- **Why it's great for UserSim:** Ships a complete, opinionated storefront and admin out of the box. The multi-step checkout and product comparison flows are classic UX friction points.

### 1.2 Spree Commerce
- **GitHub:** https://github.com/spree/spree
- **Stars:** ~14k
- **Category:** Full-stack e-commerce platform with built-in storefront
- **Tech Stack:** Ruby on Rails, Stimulus/Turbo (Hotwire), Bootstrap
- **Key User Flows:**
  - Customer storefront: product catalog with faceted search/filters, product detail pages, cart, multi-step checkout, customer account with order history
  - Admin: product management (variants, option types, properties), order processing, inventory/stock management, promotions engine, tax/shipping configuration, CMS pages, multi-store management
- **Demo/Setup:** Docker; demo at demo.spreecommerce.org
- **Why it's great for UserSim:** Ships a fully themed, server-rendered storefront — no "bring your own frontend." The promotions engine and multi-step checkout are rich UX scenarios.

### 1.3 PrestaShop
- **GitHub:** https://github.com/PrestaShop/PrestaShop
- **Stars:** ~8.5k
- **Category:** Full-stack e-commerce platform
- **Tech Stack:** PHP/Symfony, jQuery, Vue.js (new admin), Twig templates
- **Key User Flows:**
  - Customer storefront: product search, category browsing, cart, multi-step checkout, account creation, wishlist, product reviews
  - Admin back-office: catalog management, order processing, shipping rules, tax configuration, theme management, analytics dashboard, module installation
- **Demo/Setup:** Docker setup available; official demo at demo.prestashop.com
- **Why it's great for UserSim:** One of the most feature-rich e-commerce UIs. The new Hummingbird 2.0 theme (v9.1) and complex back-office provide deep UX testing scenarios.

### 1.4 Bagisto
- **GitHub:** https://github.com/bagisto/bagisto
- **Stars:** ~16k
- **Category:** Laravel-based e-commerce framework
- **Tech Stack:** PHP/Laravel, Vue.js
- **Key User Flows:**
  - Storefront: multi-language product browsing, search with filters, cart, checkout, customer account management
  - Admin: product management (simple, configurable, grouped, bundled, virtual, downloadable), category tree, CMS pages, currency/exchange rates, inventory sources
- **Demo/Setup:** Docker quickstart; live demo available at demo.bagisto.com
- **Why it's great for UserSim:** Rich storefront with marketplace features; complex product types create interesting form-filling scenarios.

---

## 2. CRM & Business

### 2.1 Twenty
- **GitHub:** https://github.com/twentyhq/twenty
- **Stars:** ~45k
- **Category:** CRM (Salesforce alternative)
- **Tech Stack:** TypeScript, React, Node.js, PostgreSQL
- **Key User Flows:**
  - Onboarding: workspace creation, profile setup, data import
  - Core CRM: contact/company management, deal pipeline (kanban), activity logging, email integration, task management
  - Customization: custom objects and fields, view creation with filters/sort/group-by, workflow automation setup
  - Settings: workspace settings, roles/permissions, integrations, API keys
- **Demo/Setup:** Docker Compose; free cloud workspace at twenty.com
- **Why it's great for UserSim:** Beautiful, modern UI inspired by Notion/Linear. Complex data entry forms, drag-and-drop kanban, extensive settings. Great demo scenario: "set up a sales pipeline and add your first deal."

### 2.2 ERPNext
- **GitHub:** https://github.com/frappe/erpnext
- **Stars:** ~34k
- **Category:** Full ERP (accounting, inventory, CRM, HR, manufacturing)
- **Tech Stack:** Python/Frappe Framework, JavaScript, MariaDB
- **Key User Flows:**
  - Setup wizard: company creation, chart of accounts, fiscal year, departments
  - Sales: lead capture, quotation creation, sales order, invoice generation, payment recording
  - Inventory: item creation, stock entry, purchase order, goods receipt
  - HR: employee onboarding, leave application, expense claims, payroll
  - Settings: dozens of configuration screens across all modules
- **Demo/Setup:** Docker; free trial at erpnext.com; demo instances available
- **Why it's great for UserSim:** Maximally complex UI with hundreds of forms and workflows. Any "friction point" findings here would be highly impactful since ERPNext serves millions of users.

### 2.3 Invoice Ninja
- **GitHub:** https://github.com/invoiceninja/invoiceninja
- **Stars:** ~9.7k
- **Category:** Invoicing, quotes, time tracking
- **Tech Stack:** PHP/Laravel (API), Flutter (web admin), React (client portal)
- **Key User Flows:**
  - Onboarding: company setup, payment gateway configuration
  - Core workflows: create client, create invoice (line items, taxes, discounts), send invoice, record payment, create recurring invoice
  - Client portal: view invoices, make payments, approve quotes
  - Reports: profit & loss, invoice aging, expense tracking
- **Demo/Setup:** Docker; hosted version with free tier; live demo available
- **Why it's great for UserSim:** Invoicing is a common task with clear success/failure criteria. The client portal provides an end-user perspective distinct from the admin view.

---

## 3. Project Management

### 3.1 Plane
- **GitHub:** https://github.com/makeplane/plane
- **Stars:** ~48k
- **Category:** Project management (Jira/Linear alternative)
- **Tech Stack:** TypeScript, Next.js, Python/Django
- **Key User Flows:**
  - Onboarding: workspace creation, project setup, invite team members
  - Issue management: create issue, set priority/labels/assignees, sub-issues, link issues
  - Views: list, board (kanban), calendar, spreadsheet, Gantt chart
  - Cycles (sprints): create cycle, add issues, track progress, burndown
  - Pages/Docs: collaborative document editor
  - Settings: workspace, project, member management, integrations (GitHub, Slack)
- **Demo/Setup:** Docker Compose self-host; free cloud tier at plane.so
- **Why it's great for UserSim:** Very polished modern UI. Multiple view types and complex filtering create rich interaction scenarios. Great for "create a sprint and plan your first issues" demo.

### 3.2 Huly
- **GitHub:** https://github.com/hcengineering/platform
- **Stars:** ~25k
- **Category:** All-in-one project management (Linear/Jira/Slack/Notion alternative)
- **Tech Stack:** TypeScript, Svelte
- **Key User Flows:**
  - Onboarding: workspace setup, team creation
  - Issue tracking: create/assign issues, kanban boards, sprints, roadmaps
  - Documents: collaborative editor (Notion-like), wiki
  - Chat: team messaging, channels, threads
  - HR module: employee profiles, department management
  - Virtual office: video calls, screen sharing
- **Demo/Setup:** Docker Compose; cloud version at huly.io
- **Why it's great for UserSim:** Combines project management + chat + docs in one UI. Rich for testing cross-module navigation and feature discovery.

### 3.3 Taiga
- **GitHub:** https://github.com/kaleidos-ventures/taiga
- **Stars:** ~3.3k (across repos)
- **Category:** Agile project management (Scrum + Kanban)
- **Tech Stack:** Python/Django (backend), Angular (frontend)
- **Key User Flows:**
  - Project creation: select template (Scrum/Kanban), invite members, configure roles
  - Scrum: backlog management, sprint planning, story point estimation, sprint board, burndown charts
  - Kanban: board management, WIP limits, swimlanes
  - Issue tracking: create issues, assign, set severity/priority/type
  - Wiki: create and organize documentation pages
- **Demo/Setup:** Docker Compose; taiga.io cloud with free tier
- **Why it's great for UserSim:** Beautiful, purpose-built agile UI. Sprint planning workflow is a uniquely complex multi-step process.

### 3.4 OpenProject
- **GitHub:** https://github.com/opf/openproject
- **Stars:** ~10k
- **Category:** Enterprise project management
- **Tech Stack:** Ruby on Rails, Angular
- **Key User Flows:**
  - Project setup: create project, configure modules, set up work package types
  - Work packages: create, assign, set dates, link dependencies
  - Gantt charts: visual timeline, drag to reschedule, dependency management
  - Boards: agile boards with custom columns
  - Time tracking: log time, view reports
  - Meetings: schedule, create agenda, record minutes
  - Wiki: project documentation
  - Admin: user management, roles/permissions, custom fields, LDAP configuration
- **Demo/Setup:** Docker; free community edition; demo at community.openproject.org
- **Why it's great for UserSim:** Enterprise-grade complexity with deeply configurable workflows. Gantt chart interaction is a great test of UI responsiveness and usability.

---

## 4. Team Communication

### 4.1 Rocket.Chat
- **GitHub:** https://github.com/RocketChat/Rocket.Chat
- **Stars:** ~45k
- **Category:** Team messaging (Slack alternative)
- **Tech Stack:** TypeScript, Meteor.js, React
- **Key User Flows:**
  - Registration/onboarding: account creation, workspace setup, admin configuration wizard
  - Messaging: send messages, threads, reactions, file sharing, search
  - Channels: create public/private channels, manage members, set topic/description
  - Direct messages: start conversation, audio/video call
  - Administration: user management, permissions, integrations, customization (layout, branding), federation settings
  - Marketplace: browse and install apps/integrations
- **Demo/Setup:** Docker Compose; free cloud starter plan; demo at open.rocket.chat
- **Why it's great for UserSim:** The admin setup wizard alone is a rich onboarding flow. Messaging + channels + threads + calls provide diverse interaction patterns.

### 4.2 Mattermost
- **GitHub:** https://github.com/mattermost/mattermost
- **Stars:** ~35k
- **Category:** Team messaging and collaboration
- **Tech Stack:** Go (backend), React/TypeScript (frontend)
- **Key User Flows:**
  - Onboarding: workspace creation, team invitations, profile setup
  - Messaging: channels, threads, reactions, file attachments, link previews, search
  - Playbooks: create incident response playbooks, run workflows
  - Boards (Focalboard): kanban, table, calendar, gallery views for task management
  - System console: extensive admin settings (authentication, plugins, compliance, notifications)
  - Integrations: slash commands, webhooks, bot accounts, plugin marketplace
- **Demo/Setup:** Docker; free community edition; cloud free tier
- **Why it's great for UserSim:** The System Console has dozens of settings pages -- a treasure trove for finding settings UX friction. Boards integration adds another layer of UI complexity.

---

## 5. Content Management & Publishing

### 5.1 Ghost
- **GitHub:** https://github.com/TryGhost/Ghost
- **Stars:** ~53k
- **Category:** Publishing platform / headless CMS
- **Tech Stack:** Node.js, Ember.js (admin), Handlebars (themes)
- **Key User Flows:**
  - Setup: initial admin account creation, site title/description, invite staff
  - Content: write/edit posts with rich editor (cards for images, embeds, HTML, etc.), schedule publishing, manage tags, set featured image, SEO settings
  - Membership: configure tiers/pricing, design signup portal, manage subscribers, view member analytics
  - Newsletter: compose and send email newsletters, configure design
  - Settings: publication identity, navigation, integrations, code injection, theme management
- **Demo/Setup:** Docker or Ghost CLI (`ghost install`); free 14-day trial on ghost.io
- **Why it's great for UserSim:** Elegant, focused UI. The membership/newsletter setup flow is a rich multi-step configuration scenario. The post editor with its card system is a great test of content creation UX.

### 5.2 Discourse
- **GitHub:** https://github.com/discourse/discourse
- **Stars:** ~43k
- **Category:** Community forum / discussion platform
- **Tech Stack:** Ruby on Rails, Ember.js
- **Key User Flows:**
  - Registration: sign-up, email verification, onboarding (new user tutorial, trust levels)
  - Posting: create new topic, reply, quote, format text, upload images, use polls
  - Discovery: browse categories, search, filter (latest, top, unread), tag navigation
  - User profile: edit bio, preferences, notification settings, activity history
  - Moderation: flag posts, review queue, user management, category permissions
  - Admin: site settings (hundreds of options), plugins, themes, email configuration, backups
- **Demo/Setup:** Docker-based install (recommended method); try.discourse.org for demo
- **Why it's great for UserSim:** The progressive trust system and onboarding tutorial are uniquely testable flows. Admin has hundreds of settings -- ideal for "find and change X setting" tasks.

---

## 6. Analytics & Dashboards

### 6.1 Metabase
- **GitHub:** https://github.com/metabase/metabase
- **Stars:** ~47k
- **Category:** Business intelligence / data visualization
- **Tech Stack:** Clojure (backend), TypeScript/React (frontend)
- **Key User Flows:**
  - Setup: connect database, create admin account, set preferences
  - Question builder: visual query builder (no SQL), select table, add filters, choose visualization, save question
  - SQL query: write SQL, visualize results, create variables for filters
  - Dashboard: create dashboard, add cards, configure filters, set auto-refresh, subscribe to email/Slack alerts
  - Data Studio: manage database connections, curate tables, define metrics
  - Admin: user/group management, permissions, SSO configuration, audit logs
- **Demo/Setup:** Docker (`docker run metabase/metabase`); free open source edition; cloud free tier
- **Why it's great for UserSim:** The visual query builder is a unique interaction pattern -- selecting tables, joining, filtering, grouping, and choosing chart types. Great scenario: "Create a dashboard showing monthly revenue trends."

### 6.2 Grafana
- **GitHub:** https://github.com/grafana/grafana
- **Stars:** ~68k
- **Category:** Observability / metrics visualization
- **Tech Stack:** Go (backend), TypeScript/React (frontend)
- **Key User Flows:**
  - Setup: add data source (Prometheus, InfluxDB, PostgreSQL, etc.), configure connection
  - Dashboard: create dashboard, add panels, configure queries, select visualization type, set time ranges
  - Panel editing: query editor, transformation pipeline, threshold configuration, alert rules
  - Alerting: create alert rules, define conditions, set notification channels
  - Explore: ad-hoc querying across data sources
  - Admin: organization management, user/team permissions, LDAP/OAuth, plugins
- **Demo/Setup:** Docker; play.grafana.org for live demo
- **Why it's great for UserSim:** Panel editing with its query builder, transformation pipeline, and visualization options is extremely interaction-rich. Time range picker and variable selectors add UI complexity.

### 6.3 Plausible Analytics
- **GitHub:** https://github.com/plausible/analytics
- **Stars:** ~24k
- **Category:** Privacy-first web analytics (Google Analytics alternative)
- **Tech Stack:** Elixir/Phoenix, React, PostgreSQL, ClickHouse
- **Key User Flows:**
  - Onboarding: create account, add website, install tracking script
  - Dashboard: view visitors, page views, bounce rate, visit duration; filter by source, page, country, device
  - Goals: set up custom events, conversion goals, funnels
  - Settings: site settings, people/team management, email reports, custom domains, import from Google Analytics
- **Demo/Setup:** Docker Compose; plausible.io for managed version; public demo dashboard available
- **Why it's great for UserSim:** Clean, simple UI -- ideal for testing whether "simple" actually means "easy to use." The onboarding flow (add site, install script, verify tracking) is a clear end-to-end task.

---

## 7. Customer Support & Helpdesk

### 7.1 Chatwoot
- **GitHub:** https://github.com/chatwoot/chatwoot
- **Stars:** ~28k
- **Category:** Omni-channel customer support (Intercom/Zendesk alternative)
- **Tech Stack:** Ruby on Rails, Vue.js
- **Key User Flows:**
  - Setup: create account, configure inbox (website widget, email, Facebook, Twitter, WhatsApp, Telegram)
  - Agent workflow: view conversation list, reply to customer, use canned responses, assign to team, add labels, set priority, resolve conversation
  - Live chat widget: customer initiates chat, pre-chat form, conversation with agent
  - Help center: create articles, organize in categories, public knowledge base
  - Contacts: view customer profiles, conversation history, custom attributes
  - Reports: conversation reports, agent performance, CSAT scores
  - Settings: team management, automation rules, integrations, notification preferences
- **Demo/Setup:** Docker; free cloud tier; demo at app.chatwoot.com
- **Why it's great for UserSim:** Both agent-side and customer-side UIs to test. The live chat widget is a great embedded UI scenario. Automation rule creation involves complex conditional logic forms.

### 7.2 Zammad
- **GitHub:** https://github.com/zammad/zammad
- **Stars:** ~5.6k
- **Category:** Helpdesk / ticketing system
- **Tech Stack:** Ruby on Rails, CoffeeScript/JavaScript
- **Key User Flows:**
  - Setup: admin wizard (organization details, email, channels, base settings)
  - Ticket management: create ticket, assign agent, set priority/state, internal notes, merge tickets, link tickets
  - Customer portal: submit ticket, view ticket status, search knowledge base
  - Knowledge base: create/organize articles, manage categories, multilingual support
  - Overviews: customizable ticket views with filters
  - Admin: channels (email, chat, phone, social), triggers, automations, SLAs, macros, roles/permissions, branding
- **Demo/Setup:** Docker; free self-hosted; zammad.com cloud trial
- **Why it's great for UserSim:** The admin setup wizard is a multi-step onboarding flow. Ticket creation with custom fields and the knowledge base editor provide diverse form-filling scenarios.

---

## 8. Scheduling & Booking

### 8.1 Cal.com
- **GitHub:** https://github.com/calcom/cal.diy (formerly calcom/cal.com)
- **Stars:** ~42k
- **Category:** Scheduling infrastructure (Calendly alternative)
- **Tech Stack:** TypeScript, Next.js, tRPC, Prisma
- **Key User Flows:**
  - Onboarding: sign up, connect calendar (Google/Outlook), set availability, create first event type
  - Event types: create event type, set duration, configure booking questions, add location (Zoom/Meet/phone), set buffer times, configure payments
  - Booking page: public booking page, select date/time, fill in details, confirm booking
  - Workflows: create automation (email/SMS reminders before/after events)
  - Teams: create team, add members, round-robin or collective scheduling
  - Settings: profile, calendars, conferencing, appearance, billing
- **Demo/Setup:** Docker; free cloud tier at cal.com; quick local setup with `yarn dx`
- **Why it's great for UserSim:** The booking flow is a clear, testable end-to-end user journey. Event type configuration has many options and conditional logic. Great demo: "Book a 30-minute meeting with someone."

---

## 9. File Storage & Collaboration

### 9.1 Nextcloud
- **GitHub:** https://github.com/nextcloud/server
- **Stars:** ~35k
- **Category:** Self-hosted cloud platform (Google Workspace alternative)
- **Tech Stack:** PHP, JavaScript/Vue.js
- **Key User Flows:**
  - Setup: admin account creation, storage configuration, app installation
  - Files: upload, download, share (link, user, group), organize folders, search, version history
  - Collaborative editing: create/edit documents, spreadsheets, presentations (with Collabora/OnlyOffice)
  - Calendar: create events, invite participants, manage multiple calendars
  - Contacts: add/edit contacts, groups, import/export
  - Talk: start chat, create group conversation, video call
  - Admin: user management, app store, security settings, external storage, theming
  - Sharing: configure share links with password protection, expiration dates, permissions
- **Demo/Setup:** Docker; try.nextcloud.com for instant demo; snap package for easy install
- **Why it's great for UserSim:** Extremely broad UI surface area. File sharing permissions and collaborative editing are complex interaction scenarios. The app store and admin panel add even more depth.

---

## 10. Email & Newsletters

### 10.1 Listmonk
- **GitHub:** https://github.com/knadh/listmonk
- **Stars:** ~19k
- **Category:** Newsletter and mailing list manager
- **Tech Stack:** Go (backend), Vue.js (frontend), PostgreSQL
- **Key User Flows:**
  - Setup: configure SMTP, create mailing lists
  - Subscribers: add subscribers (single/bulk import), manage lists, segment with SQL queries
  - Campaigns: create campaign, select template, write content (WYSIWYG/Markdown/HTML), choose recipients, schedule or send immediately
  - Templates: create/edit email templates with drag-and-drop builder
  - Analytics: view campaign stats (sent, opens, clicks, bounces), subscriber growth charts
  - Settings: SMTP configuration, bounce processing, media uploads, appearance
- **Demo/Setup:** Single binary or Docker; instant setup
- **Why it's great for UserSim:** Campaign creation is a clear multi-step workflow. Template editing and subscriber segmentation provide form-heavy scenarios. Compact enough to test thoroughly but feature-rich enough to find real UX issues.

---

## 11. Social & Community

### 11.1 Mastodon
- **GitHub:** https://github.com/mastodon/mastodon
- **Stars:** ~47k
- **Category:** Federated social network (Twitter/X alternative)
- **Tech Stack:** Ruby on Rails, React/Redux
- **Key User Flows:**
  - Registration: choose server, sign up, email verification, profile setup (avatar, bio, header)
  - Posting: compose toot, add media, set content warning, choose visibility, use hashtags, polls
  - Discovery: explore trending posts/hashtags, browse local/federated timelines, search users
  - Social: follow users, boost/favourite posts, reply, bookmark, create lists
  - Profile: edit profile, manage followers/following, view post history
  - Preferences: appearance (light/dark), notification settings, filters, muted/blocked accounts
  - Admin (for instance operators): moderation tools, domain blocks, reports, server settings
- **Demo/Setup:** Docker; mastodon.social for joining; many public instances
- **Why it's great for UserSim:** Social media flows (compose, discover, interact) are deeply familiar to users, making friction especially noticeable. The server selection during registration is a unique onboarding challenge.

---

## 12. Low-Code / Database

### 12.1 NocoDB
- **GitHub:** https://github.com/nocodb/nocodb
- **Stars:** ~62k
- **Category:** No-code database / Airtable alternative
- **Tech Stack:** TypeScript, Vue.js, Node.js
- **Key User Flows:**
  - Setup: connect to existing database or create new, configure base
  - Table management: create table, add fields (25+ field types), set constraints, link tables
  - Views: grid view, kanban, gallery, form view, calendar
  - Form builder: create shareable forms from table fields, configure validation, share link
  - Filtering/sorting: build complex filter conditions, group records
  - Collaboration: share base, set permissions, comment on records
  - API: auto-generated REST API documentation
- **Demo/Setup:** Docker one-liner; free cloud tier
- **Why it's great for UserSim:** Spreadsheet-like interaction with drag, resize, inline editing, and dropdown menus. Form builder and view switching provide varied UI patterns. Great scenario: "Create a project tracker with a kanban view."

---

## 13. Knowledge Management & LMS

### 13.1 BookStack
- **GitHub:** https://github.com/BookStackApp/BookStack
- **Stars:** ~16k
- **Category:** Wiki / documentation platform
- **Tech Stack:** PHP/Laravel, JavaScript
- **Key User Flows:**
  - Content creation: create shelf > book > chapter > page hierarchy; WYSIWYG and Markdown editors
  - Search: full-text search across all content, advanced search operators
  - Organization: drag-and-drop reordering, move pages between books/chapters
  - Permissions: role-based access, per-book/chapter/page permissions
  - Settings: registration settings, authentication (LDAP, SAML, OIDC), customization (logo, colors, homepage), webhooks
- **Demo/Setup:** Docker; demo at demo.bookstackapp.com (resets every half hour)
- **Why it's great for UserSim:** Hierarchical content organization (shelves > books > chapters > pages) is a unique navigation challenge. Permission management and the rich text editor provide complex interaction scenarios.

---

## Summary Table

| # | Name | Category | Stars | Demo Available | Complexity |
|---|------|----------|-------|----------------|------------|
| 1 | OpenCart | E-commerce | ~7.5k | demo.opencart.com | High |
| 2 | Spree Commerce | E-commerce | ~14k | demo.spreecommerce.org | High |
| 3 | PrestaShop | E-commerce | ~8.5k | demo.prestashop.com | Very High |
| 4 | Bagisto | E-commerce | ~16k | demo.bagisto.com | High |
| 5 | Twenty | CRM | ~45k | twenty.com cloud | Medium-High |
| 6 | ERPNext | ERP | ~34k | erpnext.com trial | Very High |
| 7 | Invoice Ninja | Invoicing | ~9.7k | Live demo | Medium |
| 8 | Plane | Project Management | ~48k | plane.so cloud | Medium-High |
| 9 | Huly | Project Management | ~25k | huly.io cloud | High |
| 10 | Taiga | Agile PM | ~3.3k | taiga.io cloud | Medium |
| 11 | OpenProject | Enterprise PM | ~10k | community.openproject.org | High |
| 12 | Rocket.Chat | Team Chat | ~45k | open.rocket.chat | High |
| 13 | Mattermost | Team Chat | ~35k | Docker/Cloud free | High |
| 14 | Ghost | CMS/Publishing | ~53k | ghost.io trial | Medium |
| 15 | Discourse | Forum | ~43k | try.discourse.org | High |
| 16 | Metabase | BI/Analytics | ~47k | Docker one-liner | Medium-High |
| 17 | Grafana | Observability | ~68k | play.grafana.org | High |
| 18 | Plausible | Web Analytics | ~24k | plausible.io demo | Low-Medium |
| 19 | Chatwoot | Customer Support | ~28k | app.chatwoot.com | Medium-High |
| 20 | Zammad | Helpdesk/Ticketing | ~5.6k | zammad.com trial | Medium-High |
| 21 | Cal.com | Scheduling | ~42k | cal.com cloud | Medium |
| 22 | Nextcloud | Cloud Platform | ~35k | try.nextcloud.com | Very High |
| 23 | Listmonk | Email/Newsletter | ~19k | Docker one-liner | Medium |
| 24 | Mastodon | Social Network | ~47k | mastodon.social | Medium-High |
| 25 | NocoDB | No-code Database | ~62k | Docker one-liner | Medium |
| 26 | BookStack | Wiki/Knowledge Base | ~16k | demo.bookstackapp.com | Medium |
| 27 | Kanboard | Task Management | ~9k | kanboard.org demo | Low-Medium |
| 28 | Easy!Appointments | Booking/Scheduling | ~3.5k | Docker | Low-Medium |

---

## Recommended Demo Scenarios for UserSim

These scenarios represent common user journeys that would make compelling UserSim demos:

1. **E-commerce checkout** (PrestaShop/OpenCart): "Find a blue t-shirt in size M, add it to cart, and complete checkout as a new customer"
2. **CRM setup** (Twenty): "Create a new workspace, add 3 contacts, and set up a deal pipeline"
3. **Project planning** (Plane): "Create a new project, add 5 issues with priorities, and organize them into a sprint"
4. **Dashboard creation** (Metabase): "Connect to the sample database and create a dashboard showing sales by region"
5. **Support ticket** (Chatwoot): "As a customer, start a live chat and ask about a return policy"
6. **Booking flow** (Cal.com): "Set up your availability and create a 30-minute consultation event type"
7. **Content publishing** (Ghost): "Write a blog post with an image and schedule it for next week"
8. **Forum onboarding** (Discourse): "Sign up, complete the new user tutorial, and create your first topic"
9. **Newsletter campaign** (Listmonk): "Import a subscriber list, create a template, and send a campaign"
10. **Settings configuration** (Grafana): "Add a Prometheus data source and create an alert for high CPU usage"

---

## Selection Criteria Notes

- **Excluded** developer-centric tools with minimal UI (APIs, CLIs, libraries)
- **Excluded** mobile-only apps without web interfaces
- **Excluded** projects that are archived or unmaintained
- **Prioritized** projects with: public demos or easy Docker setup, active maintenance (recent commits), meaningful star counts indicating community adoption, diverse and rich user-facing flows
- **Balanced** across: categories (13 different categories), complexity levels (Low to Very High), tech stacks (React, Vue, Angular, Ember, Svelte, jQuery), project maturity (established to newer)
