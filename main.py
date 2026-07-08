from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import time

app = FastAPI()

# ==========================
# CONFIGURATION
# ==========================

EMAIL = "24f2008333@ds.study.iitm.ac.in"

ALLOWED_ORIGINS = [
    "https://app-xubk6f.example.com",
]

RATE_LIMIT = 12
WINDOW = 10  # seconds

rate_buckets = {}

# =====================================================
# IMPORTANT:
# Replace the second origin below with the exam page's
# origin if you know it (for example https://exam.example.com)
# =====================================================

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*",
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# ==========================
# Request Context Middleware
# ==========================

@app.middleware("http")
async def request_context(request: Request, call_next):

    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


# ==========================
# Rate Limiter Middleware
# ==========================

@app.middleware("http")
async def rate_limit(request: Request, call_next):

    if request.method == "OPTIONS":
        return await call_next(request)

    client = request.headers.get("X-Client-Id", "anonymous")

    now = time.time()

    bucket = rate_buckets.setdefault(client, [])

    bucket[:] = [t for t in bucket if now - t < WINDOW]

    if len(bucket) >= RATE_LIMIT:

        retry = max(1, int(WINDOW - (now - bucket[0])))

        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
            headers={"Retry-After": str(retry)},
        )

    bucket.append(now)

    return await call_next(request)


# ==========================
# Root
# ==========================

@app.get("/")
def root():
    return {"status": "ok"}


# ==========================
# Ping
# ==========================

@app.get("/ping")
async def ping(request: Request):

    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }
