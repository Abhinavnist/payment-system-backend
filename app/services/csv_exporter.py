# app/services/csv_exporter.py
import csv
import io
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.payment import Payment
from app.core.config import settings


class CSVExporter:
    def __init__(self, db: Session):
        self.db = db
    
    def export_payments(self, 
                       merchant_id: Optional[str] = None,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> str:
        """
        Export payments to CSV file
        
        Returns the filepath to the generated CSV
        """
        # Build query
        query = self.db.query(Payment)
        
        if merchant_id:
            query = query.filter(Payment.merchant_id == merchant_id)
        
        if start_date:
            query = query.filter(Payment.created_at >= start_date)
        
        if end_date:
            query = query.filter(Payment.created_at <= end_date)
        
        payments = query.all()
        
        if not payments:
            raise HTTPException(status_code=404, detail="No payments found with the given criteria")
        
        # Ensure directory exists
        os.makedirs(settings.CSV_EXPORT_PATH, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        merchant_suffix = f"_{merchant_id}" if merchant_id else ""
        filename = f"payments{merchant_suffix}_{timestamp}.csv"
        filepath = os.path.join(settings.CSV_EXPORT_PATH, filename)
        
        # Write CSV
        with open(filepath, "w", newline="") as csvfile:
            fieldnames = [
                "id", "merchant_id", "reference", "trxn_hash_key", "payment_type",
                "payment_method", "amount", "currency", "status", "upi_id",
                "bank_name", "account_name", "account_number", "ifsc_code",
                "utr_number", "verified_by", "verification_method",
                "created_at", "updated_at", "remarks"
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for payment in payments:
                row = {
                    "id": payment.id,
                    "merchant_id": payment.merchant_id,
                    "reference": payment.reference,
                    "trxn_hash_key": payment.trxn_hash_key,
                    "payment_type": payment.payment_type,
                    "payment_method": payment.payment_method,
                    "amount": payment.amount,
                    "currency": payment.currency,
                    "status": payment.status,
                    "upi_id": payment.upi_id,
                    "bank_name": payment.bank_name,
                    "account_name": payment.account_name,
                    "account_number": payment.account_number,
                    "ifsc_code": payment.ifsc_code,
                    "utr_number": payment.utr_number,
                    "verified_by": payment.verified_by,
                    "verification_method": payment.verification_method,
                    "created_at": payment.created_at,
                    "updated_at": payment.updated_at,
                    "remarks": payment.remarks
                }
                writer.writerow(row)
        
        return filepath
    
    def generate_payments_csv_string(self, 
                                   merchant_id: Optional[str] = None,
                                   start_date: Optional[datetime] = None,
                                   end_date: Optional[datetime] = None) -> str:
        """
        Generate CSV data as a string for direct download
        """
        # Build query
        query = self.db.query(Payment)
        
        if merchant_id:
            query = query.filter(Payment.merchant_id == merchant_id)
        
        if start_date:
            query = query.filter(Payment.created_at >= start_date)
        
        if end_date:
            query = query.filter(Payment.created_at <= end_date)
        
        payments = query.all()
        
        if not payments:
            raise HTTPException(status_code=404, detail="No payments found with the given criteria")
        
        # Create CSV in memory
        output = io.StringIO()
        fieldnames = [
            "id", "merchant_id", "reference", "trxn_hash_key", "payment_type",
            "payment_method", "amount", "currency", "status", "upi_id",
            "bank_name", "account_name", "account_number", "ifsc_code",
            "utr_number", "verified_by", "verification_method",
            "created_at", "updated_at", "remarks"
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for payment in payments:
            row = {
                "id": payment.id,
                "merchant_id": payment.merchant_id,
                "reference": payment.reference,
                "trxn_hash_key": payment.trxn_hash_key,
                "payment_type": payment.payment_type,
                "payment_method": payment.payment_method,
                "amount": payment.amount,
                "currency": payment.currency,
                "status": payment.status,
                "upi_id": payment.upi_id,
                "bank_name": payment.bank_name,
                "account_name": payment.account_name,
                "account_number": payment.account_number,
                "ifsc_code": payment.ifsc_code,
                "utr_number": payment.utr_number,
                "verified_by": payment.verified_by,
                "verification_method": payment.verification_method,
                "created_at": payment.created_at,
                "updated_at": payment.updated_at,
                "remarks": payment.remarks
            }
            writer.writerow(row)
        
        return output.getvalue()