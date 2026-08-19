# mlsec-dashboards

FastAPI server aggregating evidence metrics from sibling ML security repos. Authenticated API endpoints serve portfolio metrics from committed JSON artifacts. Internal tooling  -  not a product.

```bash
pip install fastapi uvicorn
DASHBOARD_API_KEY = os.environ.get("DASHBOARD_API_KEY", "") python -m uvicorn dashboard_server:app --port 8080
```
