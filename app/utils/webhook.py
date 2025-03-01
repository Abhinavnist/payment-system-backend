import hmac
import hashlib
import time
import json
from typing import Dict, Any, Optional


def generate_webhook_signature(
    payload: Dict[str, Any],
    secret_key: str,
    timestamp: Optional[int] = None
) -> str:
    """
    Generate a signature for webhook payloads
    
    Args:
        payload: The webhook payload
        secret_key: The merchant's webhook secret key
        timestamp: Optional timestamp (defaults to current time)
    
    Returns:
        Signature string in format: t={timestamp},v1={signature}
    """
    if timestamp is None:
        timestamp = int(time.time())
    
    payload_string = json.dumps(payload, separators=(',', ':'), sort_keys=True)
    
    # Create string to sign: timestamp.payload
    to_sign = f"{timestamp}.{payload_string}"
    
    # Create HMAC signature
    signature = hmac.new(
        key=secret_key.encode(),
        msg=to_sign.encode(),
        digestmod=hashlib.sha256
    ).hexdigest()
    
    return f"t={timestamp},v1={signature}"


def verify_webhook_signature(
    payload: Dict[str, Any],
    signature_header: str,
    secret_key: str,
    tolerance: int = 300  # 5 minutes
) -> bool:
    """
    Verify a webhook signature
    
    Args:
        payload: The webhook payload
        signature_header: The signature header from the request
        secret_key: The merchant's webhook secret key
        tolerance: Maximum age of signature in seconds
    
    Returns:
        bool: True if signature is valid
    """
    # Parse signature header
    try:
        # Extract timestamp and signature
        parts = dict(item.split('=') for item in signature_header.split(','))
        timestamp = int(parts.get('t', 0))
        signature = parts.get('v1', '')
    except (ValueError, AttributeError):
        return False
    
    # Check timestamp freshness
    current_time = int(time.time())
    if abs(current_time - timestamp) > tolerance:
        # Signature too old or from the future
        return False
    
    # Generate expected signature
    expected_signature = generate_webhook_signature(
        payload=payload,
        secret_key=secret_key,
        timestamp=timestamp
    )
    
    # Compare signatures
    return hmac.compare_digest(expected_signature, signature_header)