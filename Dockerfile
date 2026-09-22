FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt
COPY dashboard_server.py index.html ./
COPY shared ./shared

RUN useradd --create-home --uid 10001 dashboard
USER dashboard

ENV DASHBOARD_ENV=production
EXPOSE 8080
CMD ["uvicorn", "dashboard_server:app", "--host", "0.0.0.0", "--port", "8080", "--no-access-log"]
