# LeadForge — project state & roadmap
# Last updated: 2026-08-23 (session 2)

## GOAL
Automated funnel: find Czech businesses without websites (RZP registry),
auto-generate single-page demo sites, deploy demos, outreach, sell full setup.

## PIPELINE STAGES
NEW -> SCOUTED -> SCORED -> ENRICHED -> GENERATED -> QA -> DEPLOYED -> CONTACTED -> REPLIED -> WON/LOST/DISCARDED

## ARCHITECTURE
- orchestrator.py        : sweep loop over all stages (--loop for continuous)
- core/db.py             : SQLite state machine (data/leads.db), events log
- core/config.py         : env + proxy hygiene + OpenRouter LLM client
- agents/scout.py        : RZP ingestion (sample mode done, LIVE FETCH PENDING)
- agents/scorer.py       : heuristic scoring w/ reasons (threshold 60)
- agents/enricher.py     : contact lookup + has-website detection (sample mode)
- generator/site_builder.py: Jinja2 single-page sites (static copy OK; LLM copy ready)
- agents/qa.py           : quality gate (leak/hallucination checks)
- templates/             : (planned) per-industry template variants

## CURRENT STATE
- [x] Full pipeline runs offline end-to-end: 2 leads DEPLOYED (file:// demos)
- [x] QA gate working
- [ ] LIVE RZP fetch: justice.cz/rpp-opendata endpoints blocked/flaky from sandbox
      (rpp-opendata.egov.cz API 403; www.justice.cz redirects to msp.gov.cz).
      Next: try official XML dumps at justice.cz xslt exports or alternate mirror.
- [ ] LLM copy generation: code ready, needs OPENROUTER_API_KEY in sandbox
      (.env workaround pending user)
- [ ] Dashboard (funnel HTML view) — NOT STARTED
- [ ] Outreach agent + approval queue — NOT STARTED
- [ ] Real deployment (rsync to VPS, wildcard subdomain) — NOT STARTED

## DECISIONS LOG
- stdlib-first design; jinja2 only external dep so far
- demos hosted on own subdomain rather than free webhosts (professionalism)
- human approval queue before any outreach goes out

## UPDATE 2026-08-23 (session 3)
- Telegram gateway LIVE: bot @Raketaci_David_Petr_bot = same agent via Hermes gateway (/handoff)
- Both demos live: demo-autoservis-kral, demo-zahrady-petrov on matpet00.github.io (new 2026 template)
- Outreach approval flow built: /outreach draft|approve|send (send simulated until SMTP)
- Skills system: skills/<agent>.md loaded per message; QA + Generator have skill files
- Red button: /pause @agent, /freeze, /red, /resume (state in pipeline_meta table)
- Old custom supervisor_bot.py retired; Hermes gateway is the interface now

## UPDATE 2026-08-23 (session 4 — overnight, ox-alpha orchestrator)
- Live scout v2 via official ARES API (justice.cz dead): 59 real RZP leads,
  new industries: health (fyzioterapie...), sport (fitness, kluby), more trades
- Enricher v2: live website detection (DNS→HTTP→content match). ICO-on-page
  = definitive proof. Distinctive-token matching kills generic-name false
  positives. Contacts extracted from confirmed sites.
- Scorer v2: company-name scoring for ARES data + trade specialization bonus
- Reviewer agent (NEW): static quality analysis of demo sites — structure/
  UX/SEO/perf/a11y/code quality. Score 0-100, threshold 75, iterative fix
  loop capped at MAX_ITERATIONS=2. Template v3 scored 79→94.
- Customer Comms agent (NEW): personalized CZ outreach drafts with human
  approval flow; objections playbook in skills/customer_comms.md
- Dashboard rebuilt: funnel bars, KPIs, per-lead table, events feed
  (python3 dashboard.py → data/dashboard.html)
- Template v3: mobile hamburger menu, scroll reveal animations, hover states,
  nav shadow, SVG icons — self-contained, zero external requests
- Safety cap MAX_DEMOS=10 until Peter approves more
- Tester agent: 7/7 PASS health checks
