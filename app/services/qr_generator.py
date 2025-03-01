# app/services/qr_generator.py
import qrcode
import io
import base64
from typing import Optional
from urllib.parse import quote


def generate_upi_qr(upi_id: str, name: str, amount: float, transaction_ref: str) -> str:
    """
    Generate a QR code for UPI payment and return as base64 string
    
    Format: upi://pay?pa={upi_id}&pn={name}&am={amount}&tr={transaction_ref}&cu=INR
    """
    # Format UPI payment string
    upi_string = f"upi://pay?pa={upi_id}&pn={quote(name)}&am={amount}&tr={transaction_ref}&cu=INR"
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(upi_string)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffered = io.BytesIO()
    img.save(buffered)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"


