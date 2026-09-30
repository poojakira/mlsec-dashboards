# Security Audit — 2026-09-30

## Scope
Initial pre-remediation review of current `main`.

## Runtime surface
Dashboard HTTP server plus static dashboards.

## Verified controls
- CI, Dependabot, security-hygiene workflow, production and incident documentation exist.
- No confirmed live API key was found in the current main branch.

## Findings to remediate/verify
1. Verify dashboard server binds safely, uses explicit allowed directories, and prevents path traversal.
2. Add authentication if deployed outside localhost/private network.
3. Add rate limiting/request limits if internet-facing.
4. Set CSP, nosniff, frame-ancestors/X-Frame-Options, and cache controls.
5. Escape all untrusted telemetry inserted into HTML.
6. Add generic error handling, critical alerts, and health-gated rollback if deployed as a service.

## Not applicable
Password reset and SQL tenant isolation unless accounts/data storage are added.

<!-- repo-verification:start -->
## Verification update — 2026-09-30

- **Scope:** Account-wide `poojakira` repository pass covering source/configuration, CI/release workflows, security-hygiene gates, dependency/SAST controls, and documentation consistency.
- **Remediation:** Fixed two Ruff-formatting mismatches, corrected the accidental literal-newline syntax regression, and re-ran all repository gates.
- **Verification state:** CI, Production Gate, Security Hygiene, Documentation Integrity, and GitHub Pages deployment all completed successfully after the final fix.
- **Security note:** The dashboards are presentation/inspection surfaces; displayed security findings must remain traceable to repository evidence.
- **Evidence boundary:** This update records repository and GitHub Actions evidence observed during the pass. It is not a claim of independent penetration testing, production deployment, or zero residual risk.
<!-- repo-verification:end -->

## Verification checkpoint — 2026-09-30

- **Snapshot commit:** `e586bdf32ccc58fd9f04b5600f61b32c82284aca`
- **Status:** VERIFIED GREEN
- **Evidence:** Documentation Integrity, Security Hygiene, Production Gate, CI, and GitHub Pages deployment all completed successfully on the current main revision.
- This checkpoint is intentionally date-bounded. It does not claim zero vulnerabilities or universal production readiness.


## Follow-up local boundary review

Original revision: `4761710551f0ad5708c3302dc649d68a8fc4b122`. Fixed invalid-key rotation rate-limit bypass, unbounded inactive identity retention, symlink evidence escapes, read-time size enforcement, non-ASCII key comparison errors, disclosure of nonnumeric metric content, and unescaped legacy HF severity markup. Added regression tests; 36 pass locally. Read-only checkout workflows no longer persist credentials. Authentication grants shared read access, without tenant/per-repository authorization. No upload endpoint exists. Multi-worker rate limiting, hostile local filesystem writers, TLS, and the separate legacy localhost service remain outside this implementation's guarantees.


Reachable-history scanner triage: ten curl-header detections are documented placeholder constants. A historical `DASHBOARD_API_KEY` assignment in `README.md` at commit `aa687f5bcf8a92d55242c1e21e0a4eaaed500be8` remains a potential exposed local application key: it is not a cloud-provider key and was not tested against any endpoint. If ever deployed, replace it in the deployment secret store; no provider revocation or history rewrite was performed. The only credential-shaped filename observed in history was a vendored certifi public CA bundle, not a private key.

The isolated dependency audit initially identified advisories in the audit environment's old pip (25.0.1), not dashboard runtime dependencies. After upgrading isolated pip to 26.2.1, `pip-audit --progress-spinner=off` reported no known vulnerabilities.

<!-- hardening-followup-20260930:start -->
## Follow-up hardening — 2026-09-30

- The historical dashboard application-key-like value previously noted in this audit is now explicitly rejected by the runtime using a SHA-256 fingerprint. The historical plaintext was not recommitted. A regression test verifies the deny behavior with synthetic values.
- This is an application-owned dashboard key, not a cloud-provider credential with a central revocation API. Any deployment that ever used the historical value must generate a fresh key, replace the deployment secret, and restart affected instances.
- GitHub Actions workflow-policy validation was strengthened on `main`, including nested action-path SHA validation and rejection of dangerous workflow triggers.
- The dashboard remains a single shared trust domain; tenant/per-repository authorization and multi-worker distributed rate limiting remain architecture/deployment limits rather than claimed controls.
<!-- hardening-followup-20260930:end -->
