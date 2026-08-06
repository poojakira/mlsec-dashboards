# Security Audit — mlsec-dashboards

**Date:** 2026-08-06  
**Classification:** STATIC DEMONSTRATION with critical security vulnerabilities

---

## Critical Findings

### CRITICAL-1: Unauthenticated subprocess execution

**File:** dashboard_server.py  
**Issue:** If the server executes subprocess commands based on user input without authentication or command allowlisting, this is a remote code execution vulnerability.  
**Remediation:** Remove all subprocess execution, or add: authentication, command allowlist, input validation, shell=False.

### CRITICAL-2: No authentication on any endpoint

**Issue:** All API endpoints and WebSocket connections are accessible without credentials.  
**Remediation:** Add token-based authentication before any production deployment.

---

## High Findings

### HIGH-1: CORS wildcard or overly permissive configuration

**Issue:** If CORS allows all origins, any website can make credentialed requests.  
**Remediation:** Restrict CORS to specific trusted origins.

### HIGH-2: Tokens in query strings

**Issue:** If authentication tokens are passed via URL query parameters, they appear in server logs, browser history, and referrer headers.  
**Remediation:** Use Authorization headers only.

---

## Medium Findings

### M-01: No dependabot.yml
### M-02: No rate limiting
### M-03: No request size limits

---

## Recommendation

**ARCHIVE THIS REPOSITORY** — it duplicates the portfolio website and command center with added security vulnerabilities. If retained, all critical findings must be fixed before any deployment.
