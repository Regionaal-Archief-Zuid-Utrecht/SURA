from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from typing import Optional

def process_url_with_token(url: str, new_token: Optional[str] = None) -> str:
    """
    Process a URL, handling token replacement while preserving other parameters.
    
    Args:
        url: The original URL
        new_token: The new token to add, or None if no token should be added
        
    Returns:
        The processed URL with token replaced/added/preserved as appropriate
    """
    # Parse the URL into components
    parsed = urlparse(url)
    
    # Parse the query parameters
    query_params = parse_qs(parsed.query, keep_blank_values=True)
    
    if new_token:
        # Replace or add the token
        query_params['token'] = [new_token]
    
    # Convert query parameters back to string
    # Note: parse_qs creates lists for all values, so we take first item if it exists
    new_query = urlencode(
        {k: v[0] if isinstance(v, list) else v 
         for k, v in query_params.items()},
        doseq=False
    )
    
    # Reconstruct the URL with all components
    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))
