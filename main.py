from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from typing import Optional
from jwt_handler import generate_token
from ip_utils import get_client_ip
from url_utils import process_url_with_token
from config import config

app = FastAPI()

# Add middleware to only allow localhost requests
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1"]
)

# Force HTTPS
app.add_middleware(HTTPSRedirectMiddleware)

# Additional security middleware to ensure HTTPS
@app.middleware("http")
async def ensure_https(request: Request, call_next):
    if request.url.scheme != "https":
        raise HTTPException(status_code=400, detail="Only HTTPS connections are allowed")
    response = await call_next(request)
    return response

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/process-url")
async def process_url(
    url: str,
    request: Request,
    forwarded_ip: Optional[str] = Query(None, description="Optional end-user IP address when behind a proxy")
):
    # Get the client's real IP address
    client_ip = get_client_ip(request, forwarded_ip)
    
    # Check if this URL matches any of our endpoints
    endpoint_config = config.get_endpoint_config(url)
    
    # Generate JWT token if needed
    token = generate_token(url, client_ip) if endpoint_config else None
    
    # Process the URL, handling any existing token
    processed_url = process_url_with_token(url, token)
        
    return {
        "url": processed_url,
        "client_ip": client_ip,
        "ip_source": "forwarded" if forwarded_ip else "detected",
        "token_action": "replaced" if token and "token=" in url else 
                       "added" if token else 
                       "preserved" if "token=" in url else "none"
    }
