from typing import Optional
from jose import jwt
import time
from urllib.parse import urlparse
from config import config, JWTEndpointConfig
from ip_utils import is_valid_ip

def generate_token(url: str, client_ip: Optional[str] = None) -> Optional[str]:
    """
    Generate a JWT token for the given URL if it matches a configured endpoint.
    
    Args:
        url: The URL to generate a token for
        client_ip: Optional IP address of the client. If IP validation
                  is enabled, it will be included in the token.
    """
    if config.mode != 'public':
        return None
        
    endpoint_config = config.get_endpoint_config(url)
    if not endpoint_config:
        return None
        
    now = int(time.time())
    
    # Extract file path from URL
    parsed_url = urlparse(url)
    file_path = parsed_url.path
    
    claims = {
        "iat": now,
        "nbf": now + int(endpoint_config.nbf),
        "exp": now + config.parse_duration(endpoint_config.duration),
        "file": file_path  # File claim is always required
    }
    
    # Add IP claim if configured and valid IP provided
    if endpoint_config.use_ip and client_ip and is_valid_ip(client_ip):
        claims["ip"] = client_ip
    
    return jwt.encode(claims, endpoint_config.jwt_secret, algorithm="HS256")
