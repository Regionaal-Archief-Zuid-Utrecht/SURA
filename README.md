# SURA - Simple URL Return API

A FastAPI-based service that provides simple URL manipulation. The service can operate in both public and private modes.

## Features

- **Dual Mode Operation**: Run in either public (token generation) or private mode (S3 proxy)

- **JWT Token Generation**: Create secure tokens for authorized URL access
   - **File-Bound Tokens**: Each token is bound to a specific file path for enhanced security
   - **Configurable Endpoints**: Support for multiple endpoints with different configurations
   - **Flexible Token Duration**: Configurable token expiration times
   - **Optional IP Validation**: Can include IP validation in tokens if required

- **S3 Proxy Mode**: In private mode, can proxy requests to S3 buckets


## Configuration

### Environment Files

1. `general.env`:
   ```
   MODE="public"  # or "private"
   ```

2. `jwt.env`:
   ```
   GENERAL_DURATION="1h"  # Default token duration

   # Endpoint configuration
   ENDPOINT_BASEURL="https://example.com"
   ENDPOINT_JWTSECRET="your-secret-here"
   ENDPOINT_DURATION="1h"  # Optional, defaults to GENERAL_DURATION
   ENDPOINT_NBF="0"       # Optional Not Before offset in seconds
   ENDPOINT_IP="FALSE"    # Optional IP validation
   ```

3. `s3.env`:
   ```
   AWS_ACCESS_KEY_ID=your-access-key-id
   AWS_SECRET_ACCESS_KEY=your-secret-access-key
   AWS_REGION=eu-west-1
   S3_BUCKET=your-bucket-name
   S3_ENDPOINT_URL=https://s3.eu-west-1.amazonaws.com  # You can use a custom S3 endpoint
   URL_EXPIRATION=3600  # Pre-signed URL expiration in seconds
   CDN_TO_S3_PREFIX=/  # Optional: if S3 keys have a different prefix than CDN paths
   ```

### Configuration Parameters

- `MODE`: Sets the operation mode (public/private)
- `*_BASEURL`: Base URL for the endpoint
- `*_JWTSECRET`: Secret key for JWT token signing
- `*_DURATION`: Token validity duration (e.g., "1h", "30m", "1d")
- `*_NBF`: Not Before time offset in seconds
- `*_IP`: Enable/disable IP claim in tokens

## Token Claims

Generated tokens include the following claims:
- `iat`: Issued At timestamp
- `nbf`: Not Before timestamp
- `exp`: Expiration timestamp
- `file`: File path (always included)
- `ip`: Client IP address (optional, based on configuration)

## API Endpoints

### POST /process-url

Process a URL and generate a token if needed.

**Request:**
```
POST /process-url?url=https://example.com/path/to/file.jpg
```

**Response:**
```json
{
    "url": "https://example.com/path/to/file.jpg?token=...",
    "client_ip": "127.0.0.1",
    "ip_source": "detected",
    "token_action": "added"
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
    "status": "ok",
    "mode": "public" // or "private"
}
```

## Security Features

- Support for HTTPS-only connections
- File-specific token binding
- Optional IP validation
- Configurable token expiration
- Not Before (NBF) claim support

## Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:
   ```bash
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment files:
   - Copy `general.env.example` to `general.env`
   - Copy `jwt.env.example` to `jwt.env` (if using public mode)
   - Copy `s3.env.example` to `s3.env` (if using private mode)
   - Update configuration values

5. Run the server:
   ```bash
   # Basic usage (uses PORT from environment or defaults to 8000)
   uvicorn main:app --reload

   # Specify port directly
   uvicorn main:app --port 8849 --reload

   # Production with SSL
   uvicorn main:app --host 127.0.0.1 --port 8443 --ssl-keyfile certs/key.pem --ssl-certfile certs/cert.pem
   ```

## Operating Modes

### Public Mode
In public mode, the service generates and validates JWT tokens for URLs based on the configured endpoints in `jwt.env`.
**WARNING**: Make sure to remove s3.env in public mode.

### Private Mode (S3 Proxy)
In private mode, the service acts as a proxy for S3 buckets. It transforms incoming URLs into local proxy URLs that handle S3 authentication internally. No JWT tokens are generated or required in this mode.
**WARNING**: Make sure to remove jwt.env in private mode.

Example transformation:
```
Input:  https://bucket.example.com/path/to/file.jpg
Output: http://localhost:8000/proxy/path/to/file.jpg?bucket=bucket
```

## Notes

- In private mode, JWT configuration is ignored for security
- File paths are automatically extracted from URLs
- Tokens are bound to specific files and cannot be reused for other files
- IP validation is optional and can be enabled per endpoint
- Server port can be configured via PORT environment variable or --port argument
