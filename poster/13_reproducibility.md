# Reproduce the Work — Poster 10

> Evidence status: This is a dated repository snapshot at the commit identified below. `VERIFIED_AT_SNAPSHOT` means verified for that commit and environment; it does not assert the same result on the latest `main`. Compare newer claims with the repository evidence before reuse.

**Repository:** `github.com/poojakira/mlsec-dashboards` · MIT • Python 3.12 • source snapshot c651768630530d2f8f2f4ff5f96ebd53e2c44142 • verified 2026-10-12

```
python -m pytest tests/ -q
# Server startup requires an operator-supplied DASHBOARD_API_KEY.
```

Evidence artifacts: dashboard_server.py, sibling evidence/*.json, tests/


## Claim audit and rendered-source boundary, October 13, 2026 UTC

The reviewed printed claims, source and test commit anchors, CI dates and benchmark limitations are in `verified_claims.json`. The PDF is generated from that manifest and the PNG is rasterized from the same page by `render_poster.py`. Source inventory, dated CI and separate reported experiments must not be combined into one result. Earlier artifact versions remain in Git history; these corrections do not assert production readiness.

Offline poster rendering: `python -m pip install reportlab==4.4.9 PyMuPDF==1.26.6`, then `python poster/render_poster.py`. The font is bundled with the pinned ReportLab package; no browser or network fetch is used during rendering.
