from typing import Optional
from fastapi import Request
import ipaddress

def is_valid_ip(ip: str) -> bool:
    """Validate if the string is a valid IPv4 or IPv6 address"""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def get_client_ip(request: Request, forwarded_ip: Optional[str] = None) -> Optional[str]:
    """
    Get the client's real IP address, considering:
    1. Explicitly provided forwarded IP (if valid)
    2. X-Forwarded-For header
    3. X-Real-IP header
    4. Direct client IP
    
    Returns None if no valid IP can be determined
    """
    if forwarded_ip and is_valid_ip(forwarded_ip):
        return forwarded_ip
        
    # Check X-Forwarded-For header
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        # Get the first IP in the chain (original client)
        ips = [ip.strip() for ip in x_forwarded_for.split(",")]
        for ip in ips:
            if is_valid_ip(ip):
                return ip
    
    # Check X-Real-IP header
    x_real_ip = request.headers.get("X-Real-IP")
    if x_real_ip and is_valid_ip(x_real_ip):
        return x_real_ip
    
    # Fall back to direct client IP
    client_host = request.client.host if request.client else None
    if client_host and is_valid_ip(client_host):
        return client_host
        
    return None
