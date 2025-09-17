import os
import time
import json
import asyncio
import contextlib
import base64
import requests
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

APP_NAME = "instabids-realtime"
DEFAULT_PORT = int(os.getenv("PORT", "5050"))

app = FastAPI(title="InstaBids Realtime Sidecar", version="0.1.0")

# CORS
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = [o.strip() for o in allowed_origins_env.split(",")] if allowed_origins_env else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve client UI at /ui
app.mount("/ui", StaticFiles(directory="web", html=True), name="ui")

def build_ice_servers() -> List[Dict[str, Any]]:
    servers: List[Dict[str, Any]] = []

    # Default STUN
    stun_urls = ["stun:stun.l.google.com:19302"]
    extra_stun_env = os.getenv("STUN_URLS", "")
    if extra_stun_env:
        stun_urls.extend([u.strip() for u in extra_stun_env.split(",") if u.strip()])
    servers.append({"urls": stun_urls})

    # Cloudflare TURN (preferred) via CF_* envs (urls may be comma-separated)
    cf_turn_urls = [u.strip() for u in os.getenv("CF_TURN_URLS", "").split(",") if u.strip()]
    cf_user = os.getenv("CF_TURN_USERNAME")
    cf_cred = os.getenv("CF_TURN_CREDENTIAL")

    # Generic TURN via TURN_* envs as fallback
    turn_urls = [u.strip() for u in os.getenv("TURN_URLS", "").split(",") if u.strip()]
    turn_user = os.getenv("TURN_USERNAME")
    turn_cred = os.getenv("TURN_PASSWORD") or os.getenv("TURN_CREDENTIAL")

    if cf_turn_urls and cf_user and cf_cred:
        servers.append({"urls": cf_turn_urls, "username": cf_user, "credential": cf_cred})
    elif turn_urls and turn_user and turn_cred:
        servers.append({"urls": turn_urls, "username": turn_user, "credential": turn_cred})

    return servers

def fetch_cloudflare_turn_credentials() -> Optional[List[Dict[str, Any]]]:
    """
    Attempts to fetch short-lived TURN credentials from Cloudflare RealtimeKit.
    Returns a list suitable for RTCPeerConnection.iceServers or None on failure.
    Env:
      CF_ORG_ID: Cloudflare Organization ID
      CF_API_KEY: Cloudflare API key (optional if CF_BASIC_AUTH provided)
      CF_BASIC_AUTH: Pre-built Basic header (e.g., "Basic base64(org:apiKey)")
      CF_TURN_API_URL: Override API endpoint (default: "https://api.cloudflare.com/realtime/turn/credentials")
      TURN_URLS: The Cloudflare TURN URL to advertise (default: "turns:turn.cloudflare.com:443?transport=tcp")
    """
    org_id = os.getenv("CF_ORG_ID")
    api_key = os.getenv("CF_API_KEY")
    basic_hdr = os.getenv("CF_BASIC_AUTH")
    endpoint = os.getenv("CF_TURN_API_URL", "https://api.cloudflare.com/realtime/turn/credentials")
    turn_urls = os.getenv("TURN_URLS", "turns:turn.cloudflare.com:443?transport=tcp")

    if not org_id or (not api_key and not basic_hdr):
        return None

    headers: Dict[str, str] = {"Content-Type": "application/json"}
    # Prefer provided CF_BASIC_AUTH header if present, else build from ORG:APIKEY
    if basic_hdr:
        headers["Authorization"] = basic_hdr
    else:
        try:
            token = base64.b64encode(f"{org_id}:{api_key}".encode("utf-8")).decode("utf-8")
            headers["Authorization"] = f"Basic {token}"
        except Exception:
            return None

    # Some APIs may require org id explicitly; include it for compatibility.
    headers.setdefault("CF-Org-Id", org_id)

    try:
        # Payload can be empty; if API supports TTL or other options, add here.
        resp = requests.post(endpoint, json={}, headers=headers, timeout=5)
        resp.raise_for_status()
        data = resp.json() if resp.content else {}
    except Exception:
        # On any error, fall back to static env TURN
        return None

    # If Cloudflare returns iceServers directly, use them
    if isinstance(data, dict) and "iceServers" in data and isinstance(data["iceServers"], list):
        return data["iceServers"]

    # Otherwise expect username/password fields; build iceServers ourselves.
    username = data.get("username") or data.get("user") or data.get("turnUsername")
    credential = data.get("password") or data.get("secret") or data.get("turnPassword")
    if username and credential:
        return [
            {"urls": [turn_urls], "username": username, "credential": credential},
            {"urls": ["stun:stun.cloudflare.com:3478"]},
        ]

    # As a last resort, return None to trigger static fallback
    return None


@app.get("/cloudflare/turn/creds")
def cloudflare_turn_creds() -> Dict[str, Any]:
    """
    Public endpoint for the UI to fetch Cloudflare TURN credentials (short-lived).
    """
    servers = fetch_cloudflare_turn_credentials()
    if servers:
        return {"iceServers": servers, "source": "cloudflare"}
    # Fallback to static env-configured servers if Cloudflare fetch fails
    return {"iceServers": build_ice_servers(), "source": "static-fallback"}


@app.get("/", response_class=PlainTextResponse)
def root() -> str:
    return "OK. See /healthz, /api/turn/ice, /attest, /events, /ws"

@app.get("/healthz")
def healthz() -> Dict[str, Any]:
    return {"ok": True, "service": APP_NAME, "ts": int(time.time())}

@app.get("/api/turn/ice")
def ice() -> Dict[str, Any]:
    # Prefer Cloudflare dynamic credentials when CF_ env is present
    if os.getenv("CF_ORG_ID") and (os.getenv("CF_BASIC_AUTH") or os.getenv("CF_API_KEY")):
        srv = fetch_cloudflare_turn_credentials()
        if srv:
            return {"iceServers": srv, "source": "cloudflare"}
    # Otherwise fall back to static TURN/STUN from env (.env / dev coturn)
    return {"iceServers": build_ice_servers(), "source": "static"}

@app.get("/attest")
def attest(req: Request) -> Dict[str, Any]:
    git_sha = os.getenv("GIT_SHA", "local-dev")
    image_digest = os.getenv("IMAGE_DIGEST", "unknown")
    public_hostname = os.getenv("PUBLIC_HOSTNAME", "")
    websockets_setting = os.getenv("CF_WEBSOCKETS", "")  # optional attestation flag if set elsewhere

    return {
        "service": APP_NAME,
        "git_sha": git_sha,
        "image_digest": image_digest,
        "allowed_origins": allowed_origins,
        "public_hostname": public_hostname,
        "port": DEFAULT_PORT,
        "websockets_enabled_env": websockets_setting if websockets_setting else None,
        "now": int(time.time()),
        "client": {
            "host": req.client.host if req.client else None,
            "headers": {k: v for (k, v) in req.headers.items() if k.lower() in ("cf-connecting-ip", "cf-ipcountry", "x-forwarded-for", "x-real-ip")},
        },
    }

# SSE: emit keepalive pings; ensure "no-transform" for Cloudflare
async def sse_generator():
    while True:
        payload = {"type": "ping", "ts": int(time.time())}
        yield f"data: {json.dumps(payload)}\n\n"
        await asyncio.sleep(15)

@app.get("/events")
def events():
    headers = {
        "Cache-Control": "no-cache, no-transform",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(sse_generator(), media_type="text/event-stream", headers=headers)

# Basic WebSocket that echoes and sends periodic pings
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    ping_task = None

    async def pinger():
        while True:
            try:
                await asyncio.sleep(15)
                await ws.send_json({"type": "ping", "ts": int(time.time())})
            except Exception:
                break

    try:
        ping_task = asyncio.create_task(pinger())
        while True:
            msg = await ws.receive_text()
            await ws.send_text(msg)  # echo
    except WebSocketDisconnect:
        pass
    finally:
        if ping_task:
            ping_task.cancel()
            with contextlib.suppress(Exception):
                await ping_task

# Optional endpoint to reflect Cloudflare websockets setting if provided via env
@app.get("/cloudflare/websockets")
def cloudflare_websockets():
    val = os.getenv("CF_WEBSOCKETS")
    return {"configured": val is not None, "value": val}
