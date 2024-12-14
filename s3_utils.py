from typing import Optional
import boto3
from botocore.client import Config
from urllib.parse import urlparse
import os
from dotenv import load_dotenv

class S3Config:
    def __init__(self):
        # Load S3 configuration
        load_dotenv("s3.env")
        
        # AWS credentials and region
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.getenv("AWS_REGION", "eu-west-1")
        
        # S3 configuration
        self.bucket = os.getenv("S3_BUCKET")
        self.endpoint_url = os.getenv("S3_ENDPOINT_URL")
        
        # URL configuration
        self.url_expiration = int(os.getenv("URL_EXPIRATION", "3600"))
        
        # CDN mapping (optional)
        self.cdn_base_url = os.getenv("CDN_BASE_URL")
        self.cdn_to_s3_prefix = os.getenv("CDN_TO_S3_PREFIX", "/")
        
        # Validate required settings
        if not all([self.aws_access_key_id, self.aws_secret_access_key, 
                   self.bucket]):
            raise ValueError("Missing required S3 configuration in s3.env")
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.aws_region,
            endpoint_url=self.endpoint_url,
            config=Config(signature_version='s3v4')
        )

def cdn_url_to_s3_key(url: str, config: S3Config) -> Optional[str]:
    """Convert a CDN URL to an S3 key"""
    parsed = urlparse(url)
    # Remove the base URL to get the path
    path = parsed.path.lstrip('/')
    
    # If there's a CDN to S3 prefix mapping, apply it
    if config.cdn_to_s3_prefix and config.cdn_to_s3_prefix != '/':
        if path.startswith(config.cdn_to_s3_prefix.lstrip('/')):
            path = path[len(config.cdn_to_s3_prefix.lstrip('/')):]
    
    return path

def generate_presigned_url(url: str, config: S3Config) -> Optional[str]:
    """Generate a pre-signed URL for S3 access"""
    try:
        # Convert CDN URL to S3 key
        s3_key = cdn_url_to_s3_key(url, config)
        if not s3_key:
            return None
            
        # Generate pre-signed URL
        presigned_url = config.s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': config.bucket,
                'Key': s3_key
            },
            ExpiresIn=config.url_expiration
        )
        
        return presigned_url
        
    except Exception as e:
        print(f"Error generating presigned URL: {str(e)}")
        return None

# Create a global config instance
s3_config = S3Config()
