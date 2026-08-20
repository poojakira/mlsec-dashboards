# RUNBOOK — mlsec-dashboards

## Overview
FastAPI server serving local dev metrics dashboards.

## Install
```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## Start Server
```bash
python dashboard_server.py
```
Server runs at `http://localhost:8000`. API docs at `/docs`.

## View Dashboards
- Main dashboard: `http://localhost:8000/`
- Metrics API: `http://localhost:8000/api/metrics`
- Health check: `http://localhost:8000/health`

## Add New Metrics
1. Define metric schema in `app/models.py`:
   ```python
   class NewMetric(BaseModel):
       name: str
       value: float
       timestamp: datetime
   ```
2. Add collection logic in `app/collectors/`.
3. Register route in `app/routes/metrics.py`.
4. Add dashboard panel in `templates/` or frontend components.
5. Restart server to pick up changes.

## Troubleshooting
- **Port in use**: Kill existing process or use `--port 8001`.
- **Import errors**: Confirm venv is activated and deps installed.
- **Stale metrics**: Check collector schedule intervals in config.
