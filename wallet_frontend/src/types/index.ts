export interface Wallet {
    balance: string;
    debit_limit: string;
    credit_limit: string;
    account_no: string;
}

export interface Transaction {
    reference: string;
    type: string;
    amount: string;
    balance_before: string;
    balance_after: string;
    description: string;
    status: string;
    date: string;
}

export interface KYCStatus {
    kyc_tier: number;
    tier_label: string;
    verifications: {
        email_verified: boolean;
        phone_verified: boolean;
        bvn_validated: boolean;
        face_id_verified: boolean;
    };
    wallet_credit_limit: string;
    loan_limits: { max_amount: string, max_months: number };
    next_tier_requires: string;
}

export interface Loan {
    id: number;
    user_loan_number: number;
    amount_requested: string;
    amount_approved: string;
    interest_rate: string;
    duration_months: number;
    status: string;
    total_repayable: string;
    monthly_instalment: string;
    amount_repaid: string;
    outstanding_balance: string;
    created_at: string;
}

export interface Bank {
    id: number;
    name: string;
    code: string;
    slug: string;
}


export interface ProviderTransaction {
    reference: string;
    direction: "FUNDING" | "WITHDRAWAL";
    amount: string;
    status: string;
    created_at: string;
}


