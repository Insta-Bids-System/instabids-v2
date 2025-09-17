"""
Test script to monitor backend requests and identify crash cause
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import asyncio
import uvicorn
import json

app = FastAPI()

# Store requests for analysis
requests_log = []

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    body = b""
    if request.method == "POST":
        body = await request.body()
        # Create new request with body for processing
        from starlette.requests import Request as StarletteRequest
        from starlette.datastructures import Headers
        
        # Clone the request with the body we read
        request = StarletteRequest(
            scope=request.scope,
            receive=lambda: asyncio.create_task(asyncio.coroutine(lambda: {"body": body})())
        )
    
    # Log request details
    log_entry = {
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers),
        "body_size": len(body) if body else 0
    }
    
    if body and len(body) < 1000:  # Only log small bodies
        try:
            log_entry["body"] = json.loads(body)
        except:
            log_entry["body"] = body.decode('utf-8')[:200]
    
    requests_log.append(log_entry)
    print(f"\n{'='*60}")
    print(f"REQUEST #{len(requests_log)}: {request.method} {request.url.path}")
    print(f"Body size: {log_entry['body_size']} bytes")
    if 'body' in log_entry and isinstance(log_entry['body'], dict):
        # Check for large image data
        if 'images' in log_entry['body'] and log_entry['body']['images']:
            img_count = len(log_entry['body']['images'])
            img_sizes = [len(img) for img in log_entry['body']['images']]
            print(f"Images: {img_count} images, sizes: {img_sizes}")
            # Don't print the actual image data
            log_entry['body']['images'] = [f"<IMAGE {len(img)} bytes>" for img in log_entry['body']['images']]
    print(f"{'='*60}\n")
    
    # Process request
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        print(f"ERROR processing request: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/requests-log")
async def get_requests_log():
    """Get all logged requests"""
    return {"total": len(requests_log), "requests": requests_log}

if __name__ == "__main__":
    print("Starting request monitoring proxy on port 8009...")
    print("Configure frontend to use http://localhost:8009 instead of 8008")
    print("This will forward to the real backend at 8008")
    uvicorn.run(app, host="0.0.0.0", port=8009)