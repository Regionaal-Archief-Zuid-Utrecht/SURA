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
        # Load general environment first
        load_dotenv("general.env")
        self.mode = os.getenv("MODE", "private")
        jwt_env_path = Path("jwt.env")
        # Only load JWT config if mode is public
        self.endpoints: Dict[str, JWTEndpointConfig] = {}
        self.general_duration: Optional[str] = None
        
        if self.mode == "public":
            if not jwt_env_path.exists():
                raise FileNotFoundError("jwt.env is required when mode is set to public")
                
            load_dotenv("jwt.env")
            self.general_duration = os.getenv("GENERAL_DURATION", "1h")
            
            # Find all endpoint configurations by searching for _BASEURL
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
        
        if self.mode == "private" and jwt_env_path.exists():
            warnings.warn(
                "jwt.env is not required when mode is set to private and considered insecure to include when not in use. Ignoring.",
                UserWarning,
                stacklevel=2
            )
    
    def get_endpoint_config(self, url: str) -> Optional[JWTEndpointConfig]:
        """Find the matching endpoint configuration for a given URL"""
        if self.mode != "public":
            return None
            
        for config in self.endpoints.values():
            if url.startswith(config.base_url):
                return config
        return None
    
    def parse_duration(self, duration: str) -> int:
        """Convert duration string (e.g., '1h', '30m', '2d') to seconds"""
        if not self.general_duration:
            raise RuntimeError("Cannot parse duration in private mode")
            
        if duration == "0":
            duration = self.general_duration
            
        match = re.match(r"(\d+)([mhd])", duration)
        if not match:
            raise ValueError(f"Invalid duration format: {duration}")
            
        amount = int(match.group(1))
        unit = match.group(2)
        
        if unit == 'm':
            return amount * 60
        elif unit == 'h':
            return amount * 3600
        elif unit == 'd':
            return amount * 86400
        else:
            raise ValueError(f"Invalid duration unit: {unit}")

# Create a global config instance
config = Config()
