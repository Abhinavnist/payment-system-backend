# Payment System

A secure payment tracking system that allows merchants to integrate payment processing through API and provides an admin interface for managing transactions.

## Features

- **Merchant Integration**: Easy API integration for merchants
- **Payment Processing**: Support for UPI and bank transfers
- **Dynamic QR Code Generation**: Generate QR codes for UPI payments
- **UTR Verification**: Manual and automated verification of transactions
- **Admin Dashboard**: Complete control over payments and merchants
- **Reporting**: CSV export of transaction data
- **Secure Authentication**: JWT token-based authentication
- **API Key Security**: API key-based access for merchants
- **Callback System**: Notify merchants on payment status changes

## Tech Stack

### Backend
- FastAPI (Python)
- PostgreSQL
- SQLAlchemy ORM
- Alembic (Migrations)
- JWT Authentication
- Docker & Docker Compose

### Frontend (Coming Soon)
- Next.js
- React
- TypeScript
- Tailwind CSS

## API Documentation

Base URL: `https://yourdomain.com/api/v1`

### Authentication

- `/auth/login/access-token` - Get JWT token
- `/auth/reset-password` - Reset user password

### Payments

- `/payments/request` - Create payment request
- `/payments/check-request` - Check payment status
- `/payments/verify-payment` - Verify payment with UTR

### Admin Endpoints

- `/admin/users` - Manage users
- `/admin/pending-payments` - Get payments pending verification
- `/admin/verify-payment/{payment_id}` - Verify payment
- `/admin/decline-payment/{payment_id}` - Decline payment
- `/admin/export-payments` - Export payments to CSV
- `/admin/dashboard-stats` - Get dashboard statistics

### Merchant Endpoints

- `/merchants` - Manage merchants
- `/reports/payments` - Get merchant payments
- `/reports/download-payments` - Download merchant payments CSV

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/payment-system.git
   cd payment-system
   ```

2. Copy environment example files:
   ```bash
   cp backend/.env-example backend/.env
   ```

3. Start services with Docker Compose:
   ```bash
   docker-compose up -d
   ```

4. Access the API at http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Admin panel coming soon at http://localhost:3000

### Local Development

1. Create a virtual environment:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the API with hot reload:
   ```bash
   uvicorn main:app --reload
   ```

## Merchant Integration Guide

### API Authentication

All merchant API requests must include the `X-API-Key` header with the provided API key.

### Create Payment Request

```http
POST /api/v1/payments/request
Content-Type: application/json
X-API-Key: your-api-key-here

{
  "api_key": "your-api-key-here",
  "service_type": 1,
  "currency": "INR",
  "action": "DEPOSIT",  // or "WITHDRAWAL"
  "reference": "your-transaction-reference",
  "amount": 1000,
  "account_name": "Customer Name",  // Required for WITHDRAWAL
  "account_number": "1234567890",   // Required for WITHDRAWAL
  "bank": "Bank Name",              // Required for WITHDRAWAL
  "bank_ifsc": "IFSC0001234",       // Required for WITHDRAWAL
  "callback_url": "https://your-callback-url.com/payment-update",
  "ae_type": "1"
}
```

### Check Payment Status

```http
POST /api/v1/payments/check-request
Content-Type: application/json
X-API-Key: your-api-key-here

{
  "trxnHashKey": "transaction-hash-received-from-request"
}
```

### Handle Callback

Your callback endpoint will receive:

```json
{
  "reference_id": "your-transaction-reference",
  "status": 2,  // 2: Confirmed, 3: Declined
  "remarks": "Payment processed successfully",
  "amount": "1000"
}
```

## Security Best Practices

1. Store API keys securely
2. Use HTTPS for all communications
3. Validate all inputs on your server
4. Implement IP whitelisting
5. Verify callbacks with transaction reference matching
6. Implement rate limiting

## License

This project is licensed under the MIT License - see the LICENSE file for details.