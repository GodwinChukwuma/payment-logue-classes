-- Wallet API -Database schema
CREATE TABLE IF NOT EXISTS wallet_users (
    id BIGSERIAL PRIMARY KEY,
    password VARCHAR(128) NOT NULL,
    last_login TIMESTAMPTZ,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    full_name  VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    bvn_encrypted TEXT NOT NULL,
    pin_encrypted TEXT NOT NULL,
    account_no VARCHAR(20) NOT NULL DEFAULT '',
    is_kyc_validated BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_staff BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON wallet_users(email);
CREATE INDEX IF NOT EXISTS idx_users_account_no ON wallet_users(account_no);
CREATE INDEX IF NOT EXISTS idx_users_kyc ON wallet_users(is_kyc_validated);

-- Django permission many to many relationship table
CREATE TABLE IF NOT EXISTS wallet_users_groups (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES wallet_users(id) ON DELETE CASCADE,
    group_id INTEGER NOT NULL REFERENCES auth_group(id) ON DELETE CASCADE,
    UNIQUE(user_id, group_id)
);

CREATE TABLE IF NOT EXISTS wallet_users_user_permissions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES wallet_users(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES auth_permission(id) ON DELETE CASCADE,
    UNIQUE(user_id, permission_id)
);

-- Wallet table
-- One wallet per user, auto-created on registration
CREATE TABLE IF NOT EXISTS wallets (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES wallet_users(id) ON DELETE CASCADE,
    balance NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    debit_limit NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    credit_limit NUMERIC(15, 2) NOT NULL DEFAULT 1000000.00,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_balance_non_negative CHECK (balance >= debit_limit),
    CONSTRAINT chk_credit_limit_positive CHECK (credit_limit > 0)
);

CREATE INDEX IF NOT EXISTS idx_wallets_user_id ON wallets(user_id);

-- Wallet Transactions
-- Eevry wallet movement: funding, withdrawal, transfer (in/out), loan events.
DO $$
BEGIN
    CREATE TYPE txn_type AS ENUM (
        'FUND',
        'WITHDRAWAL',
        'TRANSFER_IN',
        'TRANSFER_OUT',
        'LOAN_CREDIT',
        'LOAN_DEBIT'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END$$;

DO $$
BEGIN
    CREATE TYPE txn_status AS ENUM (
        'PENDING',
        'SUCCESS',
        'FAILED',
        'REVERSED'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END$$;

CREATE TABLE IF NOT EXISTS wallet_transactions (
    id BIGSERIAL PRIMARY KEY,
    wallet_id BIGINT NOT NULL REFERENCES wallets(id) ON DELETE RESTRICT,
    reference VARCHAR(64) NOT NULL UNIQUE,
    type VARCHAR(20) NOT NULL,
    amount NUMERIC(15, 2) NOT NULL,
    balance_before NUMERIC(15, 2) NOT NULL,
    balance_after NUMERIC(15, 2) NOT NULL,
    description VARCHAR(255) NOT NULL DEFAULT '',
    status VARCHAR(10) NOT NULL DEFAULT 'SUCCESS',
    counterpart_ref VARCHAR(64) NOT NULL DEFAULT '',
    date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_amount_positive CHECK (amount > 0)
);

CREATE INDEX IF NOT EXISTS idx_txn_wallet_id ON wallet_transactions(wallet_id);
CREATE INDEX IF NOT EXISTS idx_txn_reference ON wallet_transactions(reference);
CREATE INDEX IF NOT EXISTS idx_txn_type ON wallet_transactions(type);
CREATE INDEX IF NOT EXISTS idx_txn_created_at ON wallet_transactions(created_at DESC);


-- Loan Apllications
CREATE TABLE IF NOT EXISTS loan_applications (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES wallet_users(id) ON DELETE RESTRICT,
    amount_requested NUMERIC(15, 2) NOT NULL,
    amount_approved NUMERIC(15, 2),
    interest_rate NUMERIC(15, 2) NOT NULL,
    duration_months INTEGER NOT NULL CHECK (duration_months BETWEEN 1 and 60),
    purpose VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    disbursed_at TIMESTAMPTZ,
    disbursement_ref VARCHAR(64) NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_loan_amount_positive CHECK (amount_requested > 0),
    CONSTRAINT chk_interest_rate_non_neg CHECK (interest_rate > 0)
);

CREATE INDEX IF NOT EXISTS idx_loan_user_id ON loan_applications(user_id);
CREATE INDEX IF NOT EXISTS idx_loan_status ON loan_applications(status);
CREATE INDEX IF NOT EXISTS idx_loan_created_at ON loan_applications(created_at DESC);

-- loand repayment
-- One row per schedule instalment. Created automatically on loan approval
CREATE TABLE IF NOT EXISTS loan_repayments (
    id BIGSERIAL PRIMARY KEY,
    loan_id BIGINT NOT NULL REFERENCES loan_applications(id) ON DELETE RESTRICT,
    instalment_no INTEGER NOT NULL,
    amount_due NUMERIC(15, 2) NOT NULL,
    amount_paid NUMERIC(15, 2),
    due_date DATE NOT NULL,
    paid_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    transaction_ref VARCHAR(64) NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_instalment_positive CHECK (instalment_no > 0),
    CONSTRAINT chk_repayment_amount CHECK (amount_due > 0),
    UNIQUE (loan_id, instalment_no)
);

CREATE INDEX IF NOT EXISTS idx_repayment_loan_id ON loan_repayments(loan_id);
CREATE INDEX IF NOT EXISTS idx_repayment_due_date ON loan_repayments(due_date);
CREATE INDEX IF NOT EXISTS idx_repayment_status ON loan_repayments(status);

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO wallet_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO wallet_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO wallet_user;

\echo 'Schema created. Now run: python manage.py migrate'




