from typing import Dict, Optional
import os
from dotenv import load_dotenv
from dataclasses import dataclass
import re
from pathlib import Path
import warnings

@dataclass
class JWTEndpointConfig:
    base_url: str
    jwt_secret: str
    duration: str
    nbf: str
    use_ip: bool

class Config:
    def __init__(self):
        # Load all environment files
        load_dotenv("general.env")
        
        
        # Get mode from general.env
        self.mode = os.getenv("MODE", "private")
        if self.mode == "private" and Path("jwt.env").exists():
            warnings.warn("SECURITY WARNING: JWT endpoints are configured, but MODE is set to 'private'. This is not secure. Remove 'jwt.env' file or set MODE to 'public' to enable JWT endpoints.")
        
        # Load JWT configuration
        if self.mode == "public":
            if Path("s3.env").exists():
                warnings.warn("SECURITY WARNING: S3 endpoints are configured, but MODE is set to 'public'. This is not secure. Remove 's3.env' file or set MODE to 'private' to enable S3 endpoints.")
            if not Path("jwt.env").exists():
                raise ValueError("JWT endpoints are not configured. Add the 'jwt.env' file or Set MODE to 'private' to disable JWT endpoints.")

            load_dotenv("jwt.env")
            self.endpoints: Dict[str, JWTEndpointConfig] = {}
            self.general_duration: Optional[str] = None
            env_vars = os.environ
            base_url_pattern = re.compile(r"(.+)_BASEURL$")
            for key in env_vars:
                match = base_url_pattern.match(key)
                if match:
                    prefix = match.group(1)  # e.g., "ONE", "TWO"
                    self.endpoints[prefix] = JWTEndpointConfig(
                        base_url=env_vars[f"{prefix}_BASEURL"],
                        jwt_secret=env_vars[f"{prefix}_JWTSECRET"],
                        duration=env_vars.get(f"{prefix}_DURATION", "0"),
                        nbf=env_vars.get(f"{prefix}_NBF", "0"),
                    use_ip=env_vars.get(f"{prefix}_IP", "FALSE").upper() == "TRUE"
                )
            if not self.endpoints:
                warnings.warn("No JWT endpoints configured. The service will not be able to handle any URLs.")
            else:
                self.general_duration = env_vars.get("GENERAL_DURATION", "0")
        

    def get_endpoint_config(self, url: str) -> Optional[JWTEndpointConfig]:
        """Find the matching endpoint configuration for a given URL"""
        if self.mode != "public":
            return None
            
        for endpoint_key, config in self.endpoints.items():
            if url.startswith(config.base_url):
                return config
        return None

    def parse_duration(self, duration_str: str) -> int:
        """Parse a duration string into seconds
        Format: <number><unit> where unit can be s(seconds), m(minutes), h(hours), d(days)
        Example: "1h" = 3600 seconds, "30m" = 1800 seconds
        """
        if not duration_str:
            return 3600  # default 1 hour
            
        units = {
            's': 1,
            'm': 60,
            'h': 3600,
            'd': 86400
        }
        
        unit = duration_str[-1].lower()
        try:
            value = int(duration_str[:-1])
            if unit in units:
                return value * units[unit]
            else:
                return value  # assume seconds if no valid unit
        except ValueError:
            return 3600  # default to 1 hour on error

# Create a global config instance
config = Config()
