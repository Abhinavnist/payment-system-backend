# app/services/qr_generator.py
import qrcode
import io
import base64
import hashlib
from typing import Optional, Tuple
from urllib.parse import quote


def shorten_upi_link(upi_id: str, name: str, amount: float, transaction_ref: str) -> str:
    """
    Generate a short UPI payment link
    Format: upi://pay?pa={upi_id}&pn={name}&am={amount}&tr={transaction_ref}&cu=INR
    """
    # Format UPI payment string
    upi_string = f"upi://pay?pa={upi_id}&pn={quote(name)}&am={amount}&tr={transaction_ref}&cu=INR"
    
    # Generate a short hash for the link
    hash_obj = hashlib.md5(upi_string.encode())
    short_hash = hash_obj.hexdigest()[:8]
    
    # You can store this mapping in Redis or database if needed
    # For now, we'll just return the original UPI string
    return upi_string


def generate_upi_qr(upi_id: str, name: str, amount: float, transaction_ref: str) -> Tuple[str, str]:
    """
    Generate a QR code for UPI payment and return both the UPI link and QR code
    Returns: (upi_link, qr_code_base64)
    """
    # Get shortened UPI link
    upi_link = shorten_upi_link(upi_id, name, amount, transaction_ref)
    
    # Generate QR code with minimal size
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=6,  # Reduced box size
        border=2,    # Reduced border
    )
    qr.add_data(upi_link)
    qr.make(fit=True)
    
    # Create image with minimal size
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 with optimized PNG compression
    buffered = io.BytesIO()
    img.save(buffered, format='PNG', optimize=True, quality=70)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return upi_link, f"data:image/png;base64,{img_str}"


def generate_upi_link(upi_id: str, name: str, amount: float, reference: str) -> str:
    """
    Generate a UPI payment link
    
    Args:
        upi_id: The UPI ID to receive payment
        name: Name of the merchant/receiver
        amount: Amount in INR (not paisa)
        reference: Transaction reference
        
    Returns:
        str: UPI deep link that can be used to initiate payment
    """
    # URL encode parameters
    pa = quote(upi_id)  # Payee address (UPI ID)
    pn = quote(name)    # Payee name
    tn = quote(f"Payment for {reference}")  # Transaction note
    am = str(amount)    # Amount
    
    # Construct UPI URL
    # Format: upi://pay?pa=UPI_ID&pn=NAME&tn=NOTE&am=AMOUNT&cu=INR
    upi_link = f"upi://pay?pa={pa}&pn={pn}&tn={tn}&am={am}&cu=INR"
    
    return upi_link


