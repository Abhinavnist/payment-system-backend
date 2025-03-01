import re
import logging
import pandas as pd
import io
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.payment import Payment, PaymentStatus
from app.services.utr_verifier import UTRVerifier

logger = logging.getLogger(__name__)


class BankStatementProcessor:
    """Service to process bank statements and match UTR numbers with pending payments"""
    
    def __init__(self, db: Session):
        self.db = db
        self.utr_verifier = UTRVerifier(db)
    
    def process_statement(self, file_content: bytes, file_type: str, verified_by: str) -> Dict[str, Any]:
        """
        Process a bank statement file and match UTR numbers
        
        Args:
            file_content: Raw content of the uploaded file
            file_type: MIME type of the file (e.g., 'text/csv', 'application/vnd.ms-excel')
            verified_by: ID of the admin user who uploaded the statement
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Parse the statement based on file type
            if file_type == 'text/csv':
                transactions = self._parse_csv(file_content)
            elif 'excel' in file_type or 'spreadsheet' in file_type:
                transactions = self._parse_excel(file_content)
            elif file_type == 'text/plain':
                transactions = self._parse_text(file_content)
            elif 'pdf' in file_type:
                transactions = self._parse_pdf(file_content)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported file type: {file_type}",
                    "matches": 0
                }
                
            # Match UTR numbers with pending payments
            match_results = self._match_transactions(transactions, verified_by)
            
            return {
                "success": True,
                "total_transactions": len(transactions),
                "matches": match_results["matched_count"],
                "matched_payments": match_results["matched_payments"],
                "unmatched_transactions": match_results["unmatched_transactions"]
            }
            
        except Exception as e:
            logger.error(f"Error processing bank statement: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to process statement: {str(e)}",
                "matches": 0
            }
    
    def _parse_csv(self, content: bytes) -> List[Dict[str, Any]]:
        """Parse CSV bank statement"""
        df = pd.read_csv(io.BytesIO(content))
        return self._extract_transactions_from_dataframe(df)
    
    def _parse_excel(self, content: bytes) -> List[Dict[str, Any]]:
        """Parse Excel bank statement"""
        df = pd.read_excel(io.BytesIO(content))
        return self._extract_transactions_from_dataframe(df)
    
    def _parse_text(self, content: bytes) -> List[Dict[str, Any]]:
        """Parse plain text bank statement"""
        text = content.decode('utf-8')
        transactions = []
        
        # Example pattern for UTR format: UTR followed by numbers/letters
        utr_pattern = r'(?:UTR|Ref|Reference|Txn)\s*(?:No|Number|ID|#|\:)?\s*[#:]?\s*([A-Za-z0-9]{6,18})'
        amount_pattern = r'(?:Rs|INR|₹)\s*\.?\s*(\d+(?:[.,]\d+)?)'
        date_pattern = r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
        
        lines = text.split('\n')
        current_transaction = {}
        
        for line in lines:
            # Look for UTR number
            utr_match = re.search(utr_pattern, line)
            if utr_match:
                if current_transaction and 'utr' in current_transaction:
                    transactions.append(current_transaction)
                    current_transaction = {}
                current_transaction['utr'] = utr_match.group(1)
            
            # Look for amount
            amount_match = re.search(amount_pattern, line)
            if amount_match and 'utr' in current_transaction and 'amount' not in current_transaction:
                amount_str = amount_match.group(1).replace(',', '')
                current_transaction['amount'] = float(amount_str)
            
            # Look for date
            date_match = re.search(date_pattern, line)
            if date_match and 'utr' in current_transaction and 'date' not in current_transaction:
                current_transaction['date'] = date_match.group(1)
        
        # Add the last transaction if exists
        if current_transaction and 'utr' in current_transaction:
            transactions.append(current_transaction)
        
        return transactions
    
    def _parse_pdf(self, content: bytes) -> List[Dict[str, Any]]:
        """
        Parse PDF bank statement
        Note: This would require additional libraries like PyPDF2 or pdfplumber
        For now, we'll return a placeholder implementation
        """
        # This would require additional libraries to implement
        # For a complete implementation, you'd need to:
        # 1. Use a PDF parsing library (PyPDF2, pdfplumber, etc.)
        # 2. Extract text from the PDF
        # 3. Process the text similarly to the _parse_text method
        
        logger.warning("PDF parsing is not fully implemented")
        return []
    
    def _extract_transactions_from_dataframe(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Extract transaction data from a DataFrame"""
        transactions = []
        
        # Try to identify relevant columns (column names vary by bank)
        # Look for common patterns in column names
        utr_columns = [col for col in df.columns if any(
            pattern in col.lower() for pattern in 
            ['utr', 'reference', 'ref', 'transaction id', 'txn']
        )]
        
        amount_columns = [col for col in df.columns if any(
            pattern in col.lower() for pattern in 
            ['amount', 'amt', 'credit', 'deposit']
        )]
        
        date_columns = [col for col in df.columns if any(
            pattern in col.lower() for pattern in 
            ['date', 'txn date', 'value date']
        )]
        
        if not utr_columns:
            logger.warning("No UTR column found in statement")
            return []
        
        # Use the first identified column of each type
        utr_col = utr_columns[0] if utr_columns else None
        amount_col = amount_columns[0] if amount_columns else None
        date_col = date_columns[0] if date_columns else None
        
        # Extract transactions
        for _, row in df.iterrows():
            if utr_col and pd.notna(row[utr_col]):
                transaction = {'utr': str(row[utr_col]).strip()}
                
                if amount_col and pd.notna(row[amount_col]):
                    transaction['amount'] = float(row[amount_col])
                
                if date_col and pd.notna(row[date_col]):
                    transaction['date'] = row[date_col]
                
                transactions.append(transaction)
        
        return transactions
    
    def _match_transactions(self, transactions: List[Dict[str, Any]], verified_by: str) -> Dict[str, Any]:
        """
        Match transactions with pending payments
        
        Args:
            transactions: List of transactions with UTR numbers
            verified_by: ID of the admin who uploaded the statement
            
        Returns:
            Dictionary with matching results
        """
        # Get pending payments
        pending_payments = self.db.query(Payment).filter(
            Payment.status == PaymentStatus.PENDING,
            Payment.created_at >= datetime.utcnow() - timedelta(days=30)  # Last 30 days
        ).all()
        
        matched_count = 0
        matched_payments = []
        unmatched_transactions = []
        
        # Try to match transactions with payments
        for transaction in transactions:
            utr = transaction.get('utr')
            if not utr:
                continue
                
            # Look for payment with matching amount (if available)
            amount = transaction.get('amount')
            matched = False
            
            for payment in pending_payments:
                # Skip already matched payments
                if payment.status != PaymentStatus.PENDING:
                    continue
                
                # Check if amount matches approximately (within 1%)
                amount_matches = True
                if amount is not None:
                    payment_amount = payment.amount
                    margin = payment_amount * 0.01  # 1% margin
                    amount_matches = abs(payment_amount - amount) <= margin
                
                if amount_matches:
                    # Verify payment with UTR
                    try:
                        verified_payment = self.utr_verifier.verify_utr(
                            utr_number=utr,
                            payment_id=str(payment.id),
                            verified_by=verified_by,
                            verification_method="AUTO_BANK_STATEMENT"
                        )
                        
                        if verified_payment:
                            matched_count += 1
                            matched_payments.append({
                                "payment_id": str(payment.id),
                                "reference": payment.reference,
                                "amount": payment.amount,
                                "utr": utr
                            })
                            matched = True
                            break
                    except Exception as e:
                        logger.error(f"Error verifying payment: {str(e)}")
            
            if not matched:
                unmatched_transactions.append(transaction)
        
        return {
            "matched_count": matched_count,
            "matched_payments": matched_payments,
            "unmatched_transactions": unmatched_transactions
        }