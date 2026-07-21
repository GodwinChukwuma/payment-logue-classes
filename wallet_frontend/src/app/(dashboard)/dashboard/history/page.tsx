"use client";
import { useEffect, useState } from "react";
import { ArrowDownLeft, ArrowUpRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { formatNaira, formatDate } from "@/lib/utils";
import api from "@/lib/api";
import type { Transaction } from "@/types";

const TYPE_LABEL: Record<string, string> = {
  FUND: "Wallet Funding", WITHDRAWAL: "Withdrawal",
  TRANSFER_IN: "Transfer In", TRANSFER_OUT: "Transfer Out",
  LOAN_CREDIT: "Loan Disbursement", LOAN_DEBIT: "Loan Repayment",
};
const STATUS_VARIANT: Record<string, "success"|"pending"|"destructive"|"warning"> = {
  SUCCESS: "success", PENDING: "pending", FAILED: "destructive", REVERSED: "warning",
};
const isCredit = (type: string) => ["FUND","TRANSFER_IN","LOAN_CREDIT"].includes(type);

export default function HistoryPage() {
  const [txns, setTxns] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/wallet/history/").then((r) => setTxns(r.data.transactions ?? [])).finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-4 pb-8">
      <div className="px-1">
        <h1 className="text-xl font-bold text-foreground">Transaction History</h1>
        <p className="text-muted-foreground text-sm">{txns.length} transactions</p>
      </div>

      <div className="bg-white rounded-2xl card-shadow overflow-hidden">
        {loading ? (
          <div className="space-y-px animate-pulse">
            {[...Array(6)].map((_, i) => <div key={i} className="h-20 bg-muted/40" />)}
          </div>
        ) : txns.length === 0 ? (
          <div className="py-16 text-center text-muted-foreground text-sm">No transactions yet.</div>
        ) : (
          txns.map((t) => (
            <div key={t.reference} className="flex items-center gap-4 px-5 py-4 border-b border-border/60 last:border-0">
              <div className={`h-11 w-11 rounded-xl flex items-center justify-center flex-shrink-0 ${
                isCredit(t.type) ? "icon-teal" : "icon-pink"
              }`}>
                {isCredit(t.type)
                  ? <ArrowDownLeft className="h-5 w-5 text-teal-600" />
                  : <ArrowUpRight className="h-5 w-5 text-rose-500" />}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-foreground">{TYPE_LABEL[t.type] || t.type}</p>
                <p className="text-xs text-muted-foreground truncate">{t.description || t.reference}</p>
                <p className="text-xs text-muted-foreground">{formatDate(t.date)}</p>
              </div>
              <div className="text-right flex-shrink-0">
                <p className={`font-bold text-sm ${isCredit(t.type) ? "text-teal-600" : "text-rose-500"}`}>
                  {isCredit(t.type) ? "+" : "−"}{formatNaira(t.amount)}
                </p>
                <p className="text-xs text-muted-foreground">→ {formatNaira(t.balance_after)}</p>
                <Badge variant={STATUS_VARIANT[t.status]} className="text-xs mt-0.5">{t.status}</Badge>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}





