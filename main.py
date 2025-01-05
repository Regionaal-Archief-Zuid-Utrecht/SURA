from fastapi import FastAPI, Request, HTTPException, Query, Form, Response, APIRouter
from elastic_proxy_utils import forward_to_elastic
from fastapi.responses import StreamingResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from jwt_handler import generate_token
from ip_utils import get_client_ip
from url_utils import process_url_with_token
from s3_utils import generate_presigned_url, s3_config
from config import config
import httpx
from urllib.parse import urlparse
import os
import warnings

# Get server port from environment or use default
SERVER_PORT = int(os.getenv("PORT", "8000"))

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Be specific about allowed origins
    allow_credentials=True,
    allow_methods=["POST", "OPTIONS"],  # Only allow methods we actually support
    allow_headers=["Content-Type", "Authorization"],  # Be specific about allowed headers
    max_age=3600  # Cache preflight response for 1 hour
)

# Add middleware to only allow localhost requests
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1"]
)

# Only force HTTPS in production
if os.getenv("ENVIRONMENT", "development") == "production":
    # Force HTTPS
    app.add_middleware(HTTPSRedirectMiddleware)
    
    # Additional security middleware to ensure HTTPS
    @app.middleware("http")
    async def ensure_https(request: Request, call_next):
        if request.url.scheme != "https":
            raise HTTPException(status_code=400, detail="Only HTTPS connections are allowed")
        response = await call_next(request)
        return response

@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
        response = Response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response
    else:
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response

@app.get("/health")
async def health():
    return {"status": "ok", "mode": config.MODE}

@app.post("/process-url")
async def process_url(
    request: Request,
    url: str = Query(..., description="URL to process"),
    forwarded_ip: Optional[str] = Query(None, description="Optional end-user IP address when behind a proxy")
):
    try:
        # Get the client's real IP address
        client_ip = get_client_ip(request, forwarded_ip)
        
        if config.mode == "private":
            # Extract filename and bucket from the URL
            parsed_url = urlparse(url)
            path_parts = parsed_url.path.strip('/').split('/')
            if not path_parts:
                raise HTTPException(status_code=400, detail="Invalid URL format")
                
            filename = path_parts[-1]
            try:
                bucket = parsed_url.netloc.split('.')[0]  # Gets 'particulier' from 'particulier.opslag.razu.nl'
            except (IndexError, AttributeError):
                raise HTTPException(status_code=400, detail="Invalid URL format: cannot extract bucket name")
            # Return proxy URL format
            return {
                "url": f"http://localhost:{SERVER_PORT}/proxy/{filename}?bucket={bucket}",
                "client_ip": client_ip,
                "access_type": "s3_proxy"
            }
        else:
            # In public mode, handle JWT token generation
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
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/proxy/{filename}")
async def proxy_content(
    filename: str,
    bucket: str,
    request: Request
):
    try:
        # Reconstruct the original URL
        original_url = f"https://{bucket}.opslag.razu.nl/{filename}"
        
        # Override the bucket for this request
        s3_config.bucket = bucket
        
        # Generate pre-signed URL
        presigned_url = generate_presigned_url(original_url, s3_config)
        if not presigned_url:
            raise HTTPException(
                status_code=400,
                detail="Unable to generate pre-signed URL. Check if the URL is valid for this service."
            )
            
        # Stream the content through our service
        async with httpx.AsyncClient() as client:
            response = await client.get(presigned_url)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Error fetching content from storage"
                )
                
            return StreamingResponse(
                response.aiter_bytes(),
                media_type="image/jpeg",  #response.headers.get("content-type"), Temporarily forcing JPEG mime type
                headers={
                    "content-disposition": response.headers.get("content-disposition", "inline"),
                    "content-length": response.headers.get("content-length"),
                    "cache-control": "private, no-cache"
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/_search")
async def search(request: Request):
    request_body = await request.json()
    #response = request_body
    response = forward_to_elastic(request_body)

    if response is None:
        raise HTTPException(status_code=500, detail="Error forwarding request to Elastic")
    return response

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, 
                host="0.0.0.0", 
                port=SERVER_PORT)
