import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import func, and_, or_, text
from sqlalchemy.orm import Session

from app.models.payment import Payment, PaymentStatus, PaymentType, PaymentMethod
from app.models.merchant import Merchant
from app.models.payment_link import PaymentLink

logger = logging.getLogger(__name__)


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_payment_summary(
        self,
        merchant_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get payment summary statistics
        
        Args:
            merchant_id: Optional merchant ID to filter by
            start_date: Optional start date to filter by
            end_date: Optional end date to filter by
            
        Returns:
            Dictionary with summary statistics
        """
        # Build query
        query = self.db.query(Payment)
        
        # Apply filters
        if merchant_id:
            query = query.filter(Payment.merchant_id == merchant_id)
        
        if start_date:
            query = query.filter(Payment.created_at >= start_date)
        
        if end_date:
            query = query.filter(Payment.created_at <= end_date)
        
        # Get total count
        total_count = query.count()
        
        # Get counts by status
        status_counts = self._get_status_counts(query)
        
        # Get amount summaries
        amount_summary = self._get_amount_summary(query)
        
        # Calculate success rate
        success_rate = 0
        if total_count > 0:
            confirmed_count = status_counts.get(PaymentStatus.CONFIRMED.value, 0)
            success_rate = (confirmed_count / total_count) * 100
        
        return {
            "total_count": total_count,
            "status_counts": status_counts,
            "amount_summary": amount_summary,
            "success_rate": round(success_rate, 2)
        }
    
    def get_daily_trends(
        self,
        merchant_id: Optional[str] = None,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Get daily payment trends
        
        Args:
            merchant_id: Optional merchant ID to filter by
            days: Number of days to include
            
        Returns:
            List of daily statistics
        """
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # SQL for daily aggregation
        sql = """
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as total_count,
            COUNT(CASE WHEN status = 'CONFIRMED' THEN 1 END) as confirmed_count,
            COUNT(CASE WHEN status = 'DECLINED' THEN 1 END) as declined_count,
            COUNT(CASE WHEN status = 'PENDING' THEN 1 END) as pending_count,
            SUM(CASE WHEN status = 'CONFIRMED' THEN amount ELSE 0 END) as confirmed_amount
        FROM 
            payment
        WHERE 
            created_at >= :start_date
            AND created_at <= :end_date
            {merchant_filter}
        GROUP BY 
            DATE(created_at)
        ORDER BY 
            date ASC
        """
        
        # Add merchant filter if provided
        merchant_filter = ""
        params = {"start_date": start_date, "end_date": end_date}
        
        if merchant_id:
            merchant_filter = "AND merchant_id = :merchant_id"
            params["merchant_id"] = merchant_id
        
        # Format SQL
        sql = sql.format(merchant_filter=merchant_filter)
        
        # Execute query
        result = self.db.execute(text(sql), params).fetchall()
        
        # Format results
        return [
            {
                "date": row.date.isoformat(),
                "total_count": row.total_count,
                "confirmed_count": row.confirmed_count,
                "declined_count": row.declined_count,
                "pending_count": row.pending_count,
                "confirmed_amount": row.confirmed_amount
            }
            for row in result
        ]
    
    def get_payment_method_distribution(
        self,
        merchant_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, int]:
        """
        Get distribution of payments by payment method
        
        Args:
            merchant_id: Optional merchant ID to filter by
            start_date: Optional start date to filter by
            end_date: Optional end date to filter by
            
        Returns:
            Dictionary with payment method counts
        """
        # Build query
        query = self.db.query(
            Payment.payment_method,
            func.count(Payment.id).label('count')
        )
        
        # Apply filters
        if merchant_id:
            query = query.filter(Payment.merchant_id == merchant_id)
        
        if start_date:
            query = query.filter(Payment.created_at >= start_date)
        
        if end_date:
            query = query.filter(Payment.created_at <= end_date)
        
        # Group by payment method
        query = query.group_by(Payment.payment_method)
        
        # Execute query
        result = query.all()
        
        # Format results
        return {
            method.value: count for method, count in result
        }
    
    def get_merchant_performance(
        self,
        days: int = 30,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get top merchants by payment volume
        
        Args:
            days: Number of days to include
            limit: Number of merchants to return
            
        Returns:
            List of merchants with their statistics
        """
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # SQL for merchant aggregation
        sql = """
        SELECT 
            m.id as merchant_id,
            m.business_name,
            COUNT(p.id) as total_payments,
            COUNT(CASE WHEN p.status = 'CONFIRMED' THEN 1 END) as confirmed_payments,
            SUM(CASE WHEN p.status = 'CONFIRMED' THEN p.amount ELSE 0 END) as confirmed_amount
        FROM 
            merchant m
        LEFT JOIN 
            payment p ON m.id = p.merchant_id AND p.created_at >= :start_date AND p.created_at <= :end_date
        GROUP BY 
            m.id, m.business_name
        ORDER BY 
            confirmed_amount DESC
        LIMIT :limit
        """
        
        # Execute query
        result = self.db.execute(
            text(sql), 
            {"start_date": start_date, "end_date": end_date, "limit": limit}
        ).fetchall()
        
        # Format results
        return [
            {
                "merchant_id": str(row.merchant_id),
                "business_name": row.business_name,
                "total_payments": row.total_payments,
                "confirmed_payments": row.confirmed_payments,
                "confirmed_amount": row.confirmed_amount,
                "success_rate": round((row.confirmed_payments / row.total_payments * 100), 2) if row.total_payments else 0
            }
            for row in result
        ]
    
    def get_payment_link_performance(
        self,
        merchant_id: Optional[str] = None,
        days: int = 30,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get performance metrics for payment links
        
        Args:
            merchant_id: Optional merchant ID to filter by
            days: Number of days to include
            limit: Number of payment links to return
            
        Returns:
            List of payment links with their statistics
        """
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # SQL for payment link aggregation
        sql = """
        SELECT 
            pl.id as payment_link_id,
            pl.title,
            pl.unique_code,
            pl.used_count,
            COUNT(p.id) as total_payments,
            COUNT(CASE WHEN p.status = 'CONFIRMED' THEN 1 END) as confirmed_payments,
            SUM(CASE WHEN p.status = 'CONFIRMED' THEN p.amount ELSE 0 END) as confirmed_amount
        FROM 
            paymentlink pl
        LEFT JOIN 
            payment p ON pl.id = p.payment_link_id AND p.created_at >= :start_date AND p.created_at <= :end_date
        WHERE 
            1=1
            {merchant_filter}
        GROUP BY 
            pl.id, pl.title, pl.unique_code, pl.used_count
        ORDER BY 
            confirmed_amount DESC
        LIMIT :limit
        """
        
        # Add merchant filter if provided
        merchant_filter = ""
        params = {"start_date": start_date, "end_date": end_date, "limit": limit}
        
        if merchant_id:
            merchant_filter = "AND pl.merchant_id = :merchant_id"
            params["merchant_id"] = merchant_id
        
        # Format SQL
        sql = sql.format(merchant_filter=merchant_filter)
        
        # Execute query
        result = self.db.execute(text(sql), params).fetchall()
        
        # Format results
        return [
            {
                "payment_link_id": str(row.payment_link_id),
                "title": row.title,
                "unique_code": row.unique_code,
                "used_count": row.used_count,
                "total_payments": row.total_payments,
                "confirmed_payments": row.confirmed_payments,
                "confirmed_amount": row.confirmed_amount,
                "conversion_rate": round((row.confirmed_payments / row.total_payments * 100), 2) if row.total_payments else 0
            }
            for row in result
        ]
    
    def get_verification_metrics(
        self,
        merchant_id: Optional[str] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get metrics related to payment verification
        
        Args:
            merchant_id: Optional merchant ID to filter by
            days: Number of days to include
            
        Returns:
            Dictionary with verification metrics
        """
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Build query for verification time calculation
        query = self.db.query(
            func.avg(func.extract('epoch', Payment.updated_at - Payment.created_at)).label('avg_verification_time'),
            func.min(func.extract('epoch', Payment.updated_at - Payment.created_at)).label('min_verification_time'),
            func.max(func.extract('epoch', Payment.updated_at - Payment.created_at)).label('max_verification_time')
        ).filter(
            Payment.status == PaymentStatus.CONFIRMED,
            Payment.created_at >= start_date,
            Payment.created_at <= end_date
        )
        
        # Apply merchant filter if provided
        if merchant_id:
            query = query.filter(Payment.merchant_id == merchant_id)
        
        # Execute query
        result = query.first()
        
        # Get verification methods
        methods_query = self.db.query(
            Payment.verification_method,
            func.count(Payment.id).label('count')
        ).filter(
            Payment.status == PaymentStatus.CONFIRMED,
            Payment.created_at >= start_date,
            Payment.created_at <= end_date
        )
        
        # Apply merchant filter if provided
        if merchant_id:
            methods_query = methods_query.filter(Payment.merchant_id == merchant_id)
        
        # Group by verification method
        methods_query = methods_query.group_by(Payment.verification_method)
        
        # Execute query
        methods_result = methods_query.all()
        
        # Count pending verifications
        pending_count = self.db.query(func.count(Payment.id)).filter(
            Payment.status == PaymentStatus.PENDING,
            Payment.created_at >= start_date
        )
        
        if merchant_id:
            pending_count = pending_count.filter(Payment.merchant_id == merchant_id)
        
        pending_count = pending_count.scalar()
        
        # Format results
        verification_methods = {
            method if method else "UNKNOWN": count for method, count in methods_result
        }
        
        return {
            "average_verification_time": round(result.avg_verification_time) if result.avg_verification_time else 0,
            "min_verification_time": round(result.min_verification_time) if result.min_verification_time else 0,
            "max_verification_time": round(result.max_verification_time) if result.max_verification_time else 0,
            "verification_methods": verification_methods,
            "pending_verifications": pending_count
        }
    
    def _get_status_counts(self, query):
        """Helper to get counts by status"""
        status_query = query.with_entities(
            Payment.status,
            func.count(Payment.id).label('count')
        ).group_by(Payment.status)
        
        status_results = status_query.all()
        
        return {
            status.value: count for status, count in status_results
        }
    
    def _get_amount_summary(self, query):
        """Helper to get amount summaries"""
        # Clone the query for different filters
        confirmed_query = query.filter(Payment.status == PaymentStatus.CONFIRMED)
        
        # Get total amounts by payment type
        deposit_amount = confirmed_query.filter(Payment.payment_type == PaymentType.DEPOSIT).with_entities(
            func.sum(Payment.amount)
        ).scalar() or 0
        
        withdrawal_amount = confirmed_query.filter(Payment.payment_type == PaymentType.WITHDRAWAL).with_entities(
            func.sum(Payment.amount)
        ).scalar() or 0
        
        return {
            "total_deposit_amount": deposit_amount,
            "total_withdrawal_amount": withdrawal_amount,
            "net_amount": deposit_amount - withdrawal_amount
        }