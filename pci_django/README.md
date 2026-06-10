# PCI Django Transaction API

A secure Django REST API for processing and storing payment transaction data with encryption, masking, validation, audit logging, authentication, and rate limiting.

---

# Features

- JWT Authentication
- PAN (card number) validation
- PAN masking
- PAN encryption at rest
- Expiry date encryption
- Transaction reference generation
- Request validation
- Rate limiting
- Structured audit logging
- Secure transaction retrieval
- PostgreSQL database support
- OpenAPI/Swagger documentation

---

# Security Controls

## PAN Protection

Card numbers are never returned in plain text during normal transaction processing.

Example:

```json
{
  "pan_masked": "************4444"
}
```

## Encryption

Sensitive fields are encrypted before being stored in the database:

- PAN
- Expiry Date

Example:

```text
pan_encrypted:
MkzvN+eOxqOCpK2+/h1IH8WBtZS3UD/twyzuR8WeNrwGutUX...

expiry_encrypted:
Q4HvdDym+aa/q8LMc6f+zRXyVYQTktc0WlZAfCx69uRC
```

## Audit Logging

All important operations are logged:

- Authentication events
- Validation failures
- Transaction creation
- Database errors
- Rate limit violations

---

# Technology Stack

## Backend

- Python 3.13
- Django
- Django REST Framework

## Database

- PostgreSQL

## Security

- JWT Authentication
- AES Encryption
- PAN Masking
- Input Validation

---

# Project Structure

```text
pci_django/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── pci_api/
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── validators.py
│   ├── encryption.py
│   ├── rate_limit.py
│   ├── utils.py
│   └── urls.py
│
├── logs/
│   └── application.log
│
├── manage.py
└── README.md
```

---

# Installation

## Clone Repository

```bash
git clone <repository-url>
cd pci_django
```

## Create Virtual Environment

```bash
python -m venv venv
```

## Activate Virtual Environment

### macOS/Linux

```bash
source venv/bin/activate
```

### Windows

```bash
venv\Scripts\activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Environment Variables

Create a `.env` file:

```env
SECRET_KEY=your-secret-key

DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432

ENCRYPTION_KEY=your-base64-encryption-key
```

---

# Database Setup

## Create Migrations

```bash
python manage.py makemigrations
```

## Apply Migrations

```bash
python manage.py migrate
```

---

# Run Application

```bash
python manage.py runserver 8000
```

API will be available at:

```text
http://127.0.0.1:8000
```

---

# Authentication

Obtain a JWT token and include it in requests:

```http
Authorization: Bearer <token>
```

---

# API Endpoints

## Process Transaction

### Endpoint

```http
POST /api/processTransaction
```

### Request

```json
{
  "pan": "5************4444",
  "expiry_date": "12/30",
  "amount": "99.90",
  "pin": "2020",
  "email": "user@example.com"
}
```

### Response

```json
{
  "success": true,
  "saved": true,
  "message": "Transaction stored successfully.",
  "transaction_ref": "txn_19b1d9ec35d1c19076986f78",
  "pan_masked": "************4444",
  "amount": "99.90",
  "email": "user@example.com",
  "status": "pending"
}
```

---

## Retrieve Transaction

### Endpoint

```http
GET /api/transaction/<transaction_ref>
```

### Response

```json
{
  "success": true,
  "transaction_ref": "txn_19b1d9ec35d1c19076986f78",
  "pan_masked": "************4444",
  "pan_decrypted": "5555555555554444",
  "expiry_decrypted": "12/30"
}
```

---

# Validation Rules

## PAN

- Must be between 13 and 19 digits
- Spaces and dashes automatically removed
- Luhn algorithm validation

## Expiry Date

Accepted formats:

```text
MM/YY
MM/YYYY
```

## PIN

- Minimum: 4 digits
- Maximum: 6 digits

## Amount

```text
Minimum: 0.01
Maximum: 1,000,000.00
```

## Email

Must be a valid email address.

---

# Logging

Application logs are written to:

```text
logs/application.log
```

Clear log file:

```bash
truncate -s 0 logs/application.log
```

or

```bash
> logs/application.log
```

---

# Testing

Run tests:

```bash
python manage.py test
```

---

# Future Improvements

- HSM integration
- Key rotation support
- Tokenization service
- Transaction settlement workflow
- Fraud detection engine
- Webhook notifications
- PCI DSS compliance enhancements

---


