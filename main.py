import collections
import json
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

EMAIL = "24f3000207@ds.study.iitm.ac.in"
START = time.time()
COUNT = 0
LOGS = collections.deque(maxlen=2000)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def observe(request: Request, call_next):
    global COUNT
    COUNT += 1
    rid = request.headers.get("x-request-id") or str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    entry = {
        "level": "INFO",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "path": request.url.path,
        "request_id": rid,
        "method": request.method,
        "status": response.status_code,
    }
    LOGS.append(entry)
    print(json.dumps(entry), flush=True)
    return response


@app.get("/work")
def work(n: int = 1):
    total = 0
    for i in range(max(0, min(n, 1_000_000))):
        total += i
    return {"email": EMAIL, "done": n}


@app.get("/metrics")
def metrics():
    text = (
        "# HELP http_requests_total Total HTTP requests.\n"
        "# TYPE http_requests_total counter\n"
        f"http_requests_total {COUNT}\n"
    )
    return PlainTextResponse(text, media_type="text/plain; version=0.0.4")


@app.get("/healthz")
def healthz():
    return {"status": "ok", "uptime_s": time.time() - START}


@app.get("/logs/tail")
def tail(limit: int = 20):
    return list(LOGS)[-limit:] if limit > 0 else []


@app.get("/")
def root():
    return {"status": "ok"}
