# ⚠️ ARCHIVED — Security audit recommends deprecation (see SECURITY_AUDIT.md)

> **This repository is archived and should not be used in production or development.**

## Critical Security Vulnerabilities

The dashboard server in this repository has **critical security vulnerabilities**, including **unauthenticated subprocess execution**. An attacker with network access to the dashboard can execute arbitrary commands on the host without any authentication.

## Recommended Alternatives

Use one of the following instead:

- **[Grafana](https://grafana.com/)** — Production-grade dashboarding with built-in authentication, RBAC, and audit logging.
- **[Streamlit](https://streamlit.io/)** — Lightweight Python dashboards with proper session management and no subprocess exposure.

Both are referenced in the unified ML Security Platform architecture (`unified-ml-security-platform`).

## What This Was

This repository was an experimental ML security metrics dashboard that attempted to provide a lightweight web UI for visualizing ATT&CK detection coverage, model scan results, and pipeline health. It was never hardened for production use.

---

*See `SECURITY_AUDIT.md` for the full findings.*
