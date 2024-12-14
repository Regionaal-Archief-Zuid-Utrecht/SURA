# SURA - Secure URL Access Service

A FastAPI-based service that provides secure URL access through JWT tokens. The service can operate in both public and private modes, with token generation available in public mode.

## Features

- **Dual Mode Operation**: Run in either public (token generation) or private mode
- **JWT Token Generation**: Create secure tokens for authorized URL access
- **File-Bound Tokens**: Each token is bound to a specific file path for enhanced security
- **Configurable Endpoints**: Support for multiple endpoints with different configurations
- **Flexible Token Duration**: Configurable token expiration times
- **Optional IP Validation**: Can include IP validation in tokens if required

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
    "status": "ok"
}
```

## Security Features

- HTTPS-only connections
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
   - Update configuration values

5. Run the server:
   ```bash
   uvicorn main:app --host 127.0.0.1 --port 8443 --ssl-keyfile certs/key.pem --ssl-certfile certs/cert.pem
   ```

## Notes

- In private mode, JWT configuration is ignored for security
- File paths are automatically extracted from URLs
- Tokens are bound to specific files and cannot be reused for other files
- IP validation is optional and can be enabled per endpoint
