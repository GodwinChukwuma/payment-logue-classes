"use client";
import { useEffect, useState } from "react";
import { ArrowDownLeft, ArrowUpRight, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { formatNaira, formatDate } from "@/lib/utils";
import api from "@/lib/api";
import type { Transaction } from "@/types";

const TYPE_LABEL: Record<string,string> = {
  FUND:"Funding", WITHDRAWAL:"Withdrawal", TRANSFER_IN:"Transfer In",
  TRANSFER_OUT:"Transfer Out", LOAN_CREDIT:"Loan Disbursement", LOAN_DEBIT:"Loan Repayment",
};

export default function HistoryPage() {
  const [txns, setTxns] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const isCredit = (t: string) => ["FUND","TRANSFER_IN","LOAN_CREDIT"].includes(t);

  useEffect(() => {
    api.get("/wallet/history/").then(r => setTxns(r.data.transactions ?? [])).finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-4 lg:p-8 xl:p-10 max-w-4xl mx-auto space-y-5">
      <div className="flex items-center gap-3">
        <Link href="/dashboard" className="flex items-center gap-1.5 text-white/40 hover:text-white/70 text-sm transition-colors">
          <ArrowLeft className="h-4 w-4" /> Home
        </Link>
      </div>

      <div className="rounded-2xl overflow-hidden"
        style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}>
        <div className="flex items-center justify-between px-6 py-4 border-b" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
          <h1 className="text-white font-bold text-lg">Transaction History</h1>
          <span className="text-white/30 text-sm">{txns.length} transactions</span>
        </div>

        {loading ? (
          <div className="space-y-px animate-pulse">
            {[...Array(6)].map((_,i) => <div key={i} className="h-16" style={{ background: "rgba(255,255,255,0.03)" }} />)}
          </div>
        ) : txns.length === 0 ? (
          <p className="text-white/30 text-sm text-center py-16">No transactions yet.</p>
        ) : txns.map((t) => (
          <div key={t.reference} className="flex items-center gap-4 px-6 py-4 border-b transition-colors hover:bg-white/3"
            style={{ borderColor: "rgba(255,255,255,0.04)" }}>
            <div className="h-10 w-10 rounded-xl flex items-center justify-center flex-shrink-0"
              style={{ background: isCredit(t.type) ? "rgba(5,150,105,0.15)" : "rgba(190,18,60,0.15)" }}>
              {isCredit(t.type)
                ? <ArrowDownLeft className="h-5 w-5 text-emerald-400" />
                : <ArrowUpRight className="h-5 w-5 text-rose-400" />}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-white/80 text-sm font-semibold">{TYPE_LABEL[t.type] || t.type}</p>
              <p className="text-white/30 text-xs truncate">{t.description || t.reference}</p>
              <p className="text-white/25 text-xs">{formatDate(t.date)}</p>
            </div>
            <div className="text-right flex-shrink-0">
              <p className={`font-bold text-sm ${isCredit(t.type) ? "text-emerald-400" : "text-rose-400"}`}>
                {isCredit(t.type) ? "+" : "−"}{formatNaira(t.amount)}
              </p>
              <p className="text-white/30 text-xs">→ {formatNaira(t.balance_after)}</p>
              <span className="text-xs px-2 py-0.5 rounded-full mt-0.5 inline-block"
                style={{ background: t.status === "SUCCESS" ? "rgba(5,150,105,0.2)" : "rgba(255,255,255,0.08)", color: t.status === "SUCCESS" ? "#34d399" : "rgba(255,255,255,0.4)" }}>
                {t.status}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}





