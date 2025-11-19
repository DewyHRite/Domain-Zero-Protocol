# Playwright E2E Integration for Domain Zero

This document explains how Playwright fits into the Domain Zero Protocol (DZP) and Domain Zero Agents (DZA), and how to run and visually watch end‑to‑end tests in a real browser.

## Where Playwright Fits (DZP/DZA)
- Tier 1 (Rapid): Optional. Use locally for demos only. No security review.
- Tier 2 (Standard): Recommended. Add E2E smoke tests for critical user flows. Part of Yuuji's deliverables; Megumi reviews results and artifacts (report/trace).
- Tier 3 (Critical): Required. Extend with integration/E2E coverage; capture traces, videos, and run in CI. Megumi examines traces for auth/payment/security flows.

Agent roles:
- Yuuji (Implementation): Creates/updates tests under `tests/e2e`, ensures repeatability, and documents in `.protocol-state/dev-notes.md`.
- Megumi (Security): Reviews test coverage for OWASP risks (authN/Z, XSS navigation, CSRF flows). Validates traces and artifacts.
- Gojo (Mission Control): Can wire CI to run Playwright on PRs and gate merges. Tracks skipped reviews if Tier 2/3.

## Project Layout
```
/tests/e2e/
  package.json             # Playwright tooling and scripts
  playwright.config.ts     # Multi‑browser config, reports & traces
  specs/
    counter.spec.ts        # Visual demo (local HTML + clicks)
    web_smoke.spec.ts      # External site smoke (optional)
  .gitignore               # Ignore reports/artifacts
.vscode/tasks.json         # One‑click run tasks in VS Code
```

## Setup (Windows PowerShell)
```pwsh
cd "c:\Users\Dewy\OneDrive\Documents\Personal IT Projects\Domain Zero\tests\e2e"
npm install
npm run install:browsers
```

## Run Visibly in a Browser
- Headed run (opens a real browser window):
```pwsh
npm run test:headed
```
- UI mode (watch tests, step through, inspect locators):
```pwsh
npm run test:ui
```
- HTML report (after a run):
```pwsh
npm run report
```

VS Code tasks (Terminal → Run Task):
- `E2E: Install Playwright Browsers`
- `E2E: Run (headed)`
- `E2E: UI Mode`
- `E2E: Show Report`

## Viewing What Tests Do
- `specs/counter.spec.ts` renders a small HTML page, clicks a button, and you can watch the increments in a real browser when using `--headed` or UI mode.
- Artifacts:
  - HTML report in `tests/e2e/playwright-report/`
  - Traces/videos on failures for investigation

## Protocol Mapping
- Tier 2+: Yuuji includes E2E smoke for main flows. After user review, Gojo prompts Megumi for security review. Megumi inspects reports/traces and documents findings in `.protocol-state/security-review.md`.
- Tier 3: Require traces on all retries, cover auth/payment/security‑sensitive flows, and run in CI. Attach Playwright artifacts to PRs.

Suggested prompts:
- Implementation (Yuuji):
  - "Read `protocol/yuuji.agent.md` and add Playwright E2E for [feature]; update docs and dev‑notes."
- Security (Megumi):
  - "Read `protocol/megumi.agent.md` and review the Playwright traces and coverage for [feature]."

## CI (Optional Next Step)
- Add a GitHub Action to run `npm ci && npx playwright install --with-deps && npm test` inside `tests/e2e`.
- Upload `playwright-report` as an artifact and set it as a PR check.

## Notes
- `web_smoke.spec.ts` requires internet; keep it as an example and focus your app‑specific specs under `specs/`.
- Use UI mode to interactively debug selectors and watch steps in real time.
