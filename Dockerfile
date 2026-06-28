# RHCLOUD V1 backend image (§12.2) — includes Xvfb for HEADED Chromium ([修正-5]).
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Virtual display so Chromium can run headed (harder for sites to flag as a bot).
RUN apt-get update && apt-get install -y xvfb && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN playwright install chromium      # pre-install to avoid first-run timeout

EXPOSE 8000
# Entry point is C's FastAPI app (src/main.py); run under xvfb-run for headed
# mode. Shell form so $PORT (injected by Railway/most PaaS) is honored; falls
# back to 8000 for local `docker run`.
CMD ["sh", "-c", "xvfb-run -a uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
