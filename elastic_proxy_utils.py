import os
import requests
from dotenv import load_dotenv
from typing import Dict, Any, Optional
import warnings

def forward_to_elastic(request_body: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Forward a request to the Elastic endpoint and return the response.
    
    Args:
        request_body (Dict[str, Any]): The request body to send to Elastic
        
    Returns:
        Optional[Dict[str, Any]]: The response from Elastic, or None if the request fails
    """
    # Load environment variables
    load_dotenv('elastic.env')
    
    # Get Elastic configuration
    elastic_url = os.getenv('ELASTIC_SERVER')
    api_key = os.getenv('ELASTIC_API_KEY')
    
    if not elastic_url or not api_key:
        raise ValueError("Missing required Elastic configuration in elastic.env")
    
    # Set up headers with API key
    headers = {
        'Authorization': f'ApiKey {api_key}',
        'Content-Type': 'application/json'
    }
    warnings.warn(f'Request body: {request_body}')
    try:
        # Make the request to Elastic
        response = requests.post(
            elastic_url,
            headers=headers,
            json=request_body
        )
        
        # Raise an exception for bad status codes
        response.raise_for_status()
        warnings.warn(f'Response: {response.json()}')
        # Return the JSON response
        return response.json()
        
    except requests.exceptions.RequestException as e:
        # Log the error (you might want to use a proper logging system)
        print(f"Error forwarding request to Elastic: {str(e)}")
        return None