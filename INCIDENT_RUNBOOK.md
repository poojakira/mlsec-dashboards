# Incident Runbook — mlsec-dashboards

## Table of Contents
1. [Dashboard Unavailable (5xx)](#1-dashboard-unavailable-5xx)
2. [Authentication Service Failure](#2-authentication-service-failure)
3. [Data Feed Stale / No Updates](#3-data-feed-stale--no-updates)
4. [High Latency on Dashboard Load](#4-high-latency-on-dashboard-load)
5. [WebSocket Disconnections](#5-websocket-disconnections)
6. [Static Assets Not Loading](#6-static-assets-not-loading)
7. [CORS Errors in Production](#7-cors-errors-in-production)
8. [Memory/CPU Spike on Dashboard Service](#8-memorycpu-spike-on-dashboard-service)
9. [Database Connection Pool Exhaustion](#9-database-connection-pool-exhaustion)
10. [SSL/TLS Certificate Expiry](#10-ssltls-certificate-expiry)

---

## 1. Dashboard Unavailable (5xx)

**Severity:** P1 — Critical  
**Impact:** All users cannot access the ML security dashboard.  
**SLA:** Acknowledge within 5 minutes, resolve within 30 minutes.

### Symptoms
- HTTP 500/502/503 responses from dashboard URL
- Health check endpoint `/health` returning errors
- Alerts from uptime monitoring (e.g., PagerDuty, Datadog)

### Diagnosis Steps
1. Check service status:
   ```bash
   kubectl get pods -n mlsec-dashboards
   kubectl logs -n mlsec-dashboards deployment/dashboard-api --tail=100
   ```
2. Verify load balancer targets are healthy:
   ```bash
   aws elbv2 describe-target-health --target-group-arn <TG_ARN>
   ```
3. Check recent deployments:
   ```bash
   kubectl rollout history deployment/dashboard-api -n mlsec-dashboards
   ```
4. Verify database connectivity:
   ```bash
   kubectl exec -it <pod> -n mlsec-dashboards -- python -c "from app import db; db.check_connection()"
   ```

### Resolution
- **If pods are crashing:** Check logs for OOM or unhandled exceptions. Roll back:
  ```bash
  kubectl rollout undo deployment/dashboard-api -n mlsec-dashboards
  ```
- **If load balancer issue:** Verify security groups and target group health check paths.
- **If database issue:** See [Database Connection Pool Exhaustion](#9-database-connection-pool-exhaustion).

### Post-Incident
- Update status page
- Write post-mortem within 48 hours
- Add regression test for failure mode

---

## 2. Authentication Service Failure

**Severity:** P1 — Critical  
**Impact:** No user can log in; existing sessions may be invalidated.  
**SLA:** Acknowledge within 5 minutes, resolve within 30 minutes.

### Symptoms
- All login attempts fail with 401/403
- Auth service health check failing
- Spike in authentication error logs

### Diagnosis Steps
1. Check auth service status:
   ```bash
   kubectl get pods -n auth-service
   curl -s https://auth.internal/health | jq .
   ```
2. Verify OAuth/OIDC provider reachability:
   ```bash
   curl -s https://idp.example.com/.well-known/openid-configuration | jq .status
   ```
3. Check token signing key availability:
   ```bash
   kubectl get secret jwt-signing-key -n auth-service -o jsonpath='{.data}'
   ```

### Resolution
- **If IdP is unreachable:** Check DNS, firewall rules, and IdP status page.
- **If signing keys rotated unexpectedly:** Restore previous key from backup.
- **If auth pods are down:** Restart or scale:
  ```bash
  kubectl rollout restart deployment/auth-api -n auth-service
  ```

### Post-Incident
- Verify all users can authenticate
- Audit any unauthorized access during outage window
- Review key rotation procedures

---

## 3. Data Feed Stale / No Updates

**Severity:** P2 — High  
**Impact:** Dashboard displays outdated security metrics; real-time threat visibility lost.  
**SLA:** Acknowledge within 15 minutes, resolve within 1 hour.

### Symptoms
- Dashboard "Last Updated" timestamp is stale (>5 minutes old)
- No new data points on threat timeline charts
- Data ingestion pipeline metrics show zero throughput

### Diagnosis Steps
1. Check data pipeline status:
   ```bash
   kubectl get pods -n data-pipeline
   kubectl logs -n data-pipeline deployment/metric-ingester --tail=100
   ```
2. Verify message queue health:
   ```bash
   aws sqs get-queue-attributes --queue-url <QUEUE_URL> \
     --attribute-names ApproximateNumberOfMessages
   ```
3. Check upstream data sources:
   ```bash
   curl -s http://ml-model-monitor.internal/health | jq .
   curl -s http://threat-detector.internal/health | jq .
   ```

### Resolution
- **If message queue is backed up:** Scale consumers:
  ```bash
  kubectl scale deployment/metric-ingester -n data-pipeline --replicas=5
  ```
- **If upstream source is down:** Alert upstream team, enable degraded mode.
- **If database write failure:** Check disk space and connection limits.

### Post-Incident
- Verify data backfill completed
- Check for data gaps in time series

---

## 4. High Latency on Dashboard Load

**Severity:** P2 — High  
**Impact:** Dashboard takes >5s to load; user experience severely degraded.  
**SLA:** Acknowledge within 15 minutes, resolve within 1 hour.

### Symptoms
- Page load time >5 seconds (normally <1.5s)
- API response times elevated (p99 > 3s)
- Users reporting slow or unresponsive dashboard

### Diagnosis Steps
1. Check API response times:
   ```bash
   kubectl top pods -n mlsec-dashboards
   curl -w "%{time_total}" -o /dev/null -s https://dashboard.example.com/api/v1/dashboard/summary
   ```
2. Identify slow queries:
   ```sql
   SELECT query, mean_exec_time, calls FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;
   ```
3. Check cache hit rates:
   ```bash
   redis-cli INFO stats | grep hit
   ```

### Resolution
- **If cache is cold/down:** Restart Redis, warm cache.
- **If slow queries:** Add missing indexes or optimize query.
- **If resource exhaustion:** Scale horizontally:
  ```bash
  kubectl scale deployment/dashboard-api -n mlsec-dashboards --replicas=5
  ```

---

## 5. WebSocket Disconnections

**Severity:** P3 — Medium  
**Impact:** Real-time updates stop; users must manually refresh.  
**SLA:** Acknowledge within 30 minutes, resolve within 2 hours.

### Symptoms
- Clients reporting "disconnected" status indicators
- WebSocket connection error logs spiking
- No real-time threat notifications delivered

### Diagnosis Steps
1. Check WebSocket server pods:
   ```bash
   kubectl get pods -n mlsec-dashboards -l component=websocket
   kubectl logs -n mlsec-dashboards -l component=websocket --tail=50
   ```
2. Verify load balancer WebSocket support and idle timeout.
3. Check connection limits: `cat /proc/sys/net/core/somaxconn`

### Resolution
- **If idle timeout:** Increase ALB idle timeout to 300s, add ping/pong keepalive.
- **If connection limit reached:** Scale WebSocket pods.
- **If pod restarts:** Check memory limits, enable graceful shutdown.

---

## 6. Static Assets Not Loading

**Severity:** P3 — Medium  
**Impact:** Dashboard renders without styles/scripts; partially functional.  
**SLA:** Acknowledge within 30 minutes, resolve within 2 hours.

### Symptoms
- Broken layout, missing CSS/JS
- Browser console shows 404 for static assets
- CDN returning stale or missing content

### Resolution
- **If assets missing from S3:** Re-run build and upload:
  ```bash
  npm run build
  aws s3 sync dist/static/ s3://mlsec-dashboard-static/static/ --delete
  ```
- **If CDN caching stale version:** Create invalidation:
  ```bash
  aws cloudfront create-invalidation --distribution-id <DIST_ID> --paths "/static/*"
  ```

---

## 7. CORS Errors in Production

**Severity:** P3 — Medium  
**Impact:** Cross-origin API calls fail; embedded dashboards broken.  
**SLA:** Acknowledge within 30 minutes, resolve within 2 hours.

### Symptoms
- Browser console shows CORS policy errors
- API calls from allowed origins being blocked

### Resolution
- **If origin not in allowlist:** Add origin to `CORS_ALLOWED_ORIGINS` env var and redeploy.
- **If OPTIONS not handled:** Ensure Flask-CORS or middleware is processing preflight.
- **If ALB stripping headers:** Configure ALB to forward CORS headers.

---

## 8. Memory/CPU Spike on Dashboard Service

**Severity:** P2 — High  
**Impact:** Service degradation, potential OOM kills.  
**SLA:** Acknowledge within 15 minutes, resolve within 1 hour.

### Symptoms
- Pod restarts due to OOMKilled
- CPU throttling visible in metrics
- Response times increasing progressively

### Resolution
- **If OOMKilled:** Increase memory limits temporarily:
  ```bash
  kubectl set resources deployment/dashboard-api -n mlsec-dashboards --limits=memory=2Gi
  ```
- **If memory leak:** Identify leaking code path, deploy fix, restart pods.
- **If sudden traffic spike:** Enable HPA:
  ```bash
  kubectl autoscale deployment/dashboard-api -n mlsec-dashboards --min=3 --max=10 --cpu-percent=70
  ```

---

## 9. Database Connection Pool Exhaustion

**Severity:** P1 — Critical  
**Impact:** All API calls fail; dashboard completely non-functional.  
**SLA:** Acknowledge within 5 minutes, resolve within 30 minutes.

### Symptoms
- "Connection pool exhausted" errors in logs
- API returning 500 with database errors

### Diagnosis
```sql
SELECT count(*) FROM pg_stat_activity WHERE datname = 'mlsec_dashboard';
SELECT state, count(*) FROM pg_stat_activity GROUP BY state;
```

### Resolution
- Terminate idle connections:
  ```sql
  SELECT pg_terminate_backend(pid) FROM pg_stat_activity
  WHERE state = 'idle' AND query_start < now() - interval '10 minutes';
  ```
- Increase `SQLALCHEMY_POOL_SIZE` and `POOL_MAX_OVERFLOW`.

---

## 10. SSL/TLS Certificate Expiry

**Severity:** P1 — Critical  
**Impact:** Browser shows security warning; users cannot access dashboard.  
**SLA:** Acknowledge within 5 minutes, resolve within 30 minutes.

### Diagnosis
```bash
echo | openssl s_client -connect dashboard.example.com:443 2>/dev/null | openssl x509 -noout -dates
kubectl get certificates -n mlsec-dashboards
```

### Resolution
- If cert-manager failed: check issuer, fix DNS/HTTP challenge, trigger renewal.
- Emergency: upload manual certificate while fixing automation.

---

## Escalation Matrix

| Severity | Acknowledge | Resolve | Escalate To |
|----------|-------------|---------|-------------|
| P1 | 5 min | 30 min | VP Eng + Security Lead |
| P2 | 15 min | 1 hour | Team Lead |
| P3 | 30 min | 2 hours | On-call engineer |
| P4 | 4 hours | Next business day | Backlog |
