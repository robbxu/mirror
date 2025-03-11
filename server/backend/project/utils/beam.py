import base64
import hashlib
import hmac
import requests
import json
from project.config import settings

def verify_signature(
    request_body: bytes, secret_key: str, timestamp: int, signature: str
):
    # Encode request body to Base64
    base64_payload = base64.b64encode(request_body).decode()

    # Create data to sign by concatenating base64 payload with timestamp
    data_to_sign = f"{base64_payload}:{timestamp}"

    # Initialize HMAC with SHA256 and secret key
    h = hmac.new(secret_key.encode(), data_to_sign.encode(), hashlib.sha256)

    # Compute the HMAC signature
    computed_signature = h.hexdigest()
    assert signature == computed_signature

