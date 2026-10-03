# Product Validation

## Product boundary
Evidence presentation and aggregation layer. It is not a SIEM, SOC monitor, or source of truth by itself.

## Real-world validation ladder
1. Static rendering and authenticated API tests.
2. Freshness check against source-repository evidence.
3. Reject dashboard metrics that cannot be traced to a repository/commit/artifact.
4. Display weak or unavailable results instead of silently dropping them.
5. Optional live aggregation only when a real evidence source is explicitly configured.

## Evidence rules
The dashboard may summarize evidence; it may not upgrade snapshot evidence into a current or production claim.
