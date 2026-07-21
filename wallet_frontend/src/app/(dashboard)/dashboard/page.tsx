"use client";
import { useEffect, useState } from "react";
import {
  ArrowDownLeft, ArrowUpRight, ArrowLeftRight,
  CreditCard, History, ShieldCheck,
} from "lucide-react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { formatNaira, formatDate } from "@/lib/utils";
import api from "@/lib/api";
import type { Wallet, Transaction, KYCStatus } from "@/types";

const quickActions = [
  { href: "/dashboard/fund",     label: "Fund",     icon: ArrowDownLeft, bg: "icon-blue",   color: "text-blue-600" },
  { href: "/dashboard/withdraw", label: "Withdraw", icon: ArrowUpRight,  bg: "icon-pink",   color: "text-pink-500" },
  { href: "/dashboard/transfer", label: "Transfer", icon: ArrowLeftRight,bg: "icon-teal",   color: "text-teal-600" },
  { href: "/dashboard/loans",    label: "Loans",    icon: CreditCard,    bg: "icon-yellow", color: "text-amber-500" },
  { href: "/dashboard/history",  label: "History",  icon: History,       bg: "icon-purple", color: "text-purple-600" },
  { href: "/dashboard/kyc",      label: "KYC",      icon: ShieldCheck,   bg: "icon-pink",   color: "text-rose-500" },
];

const STATUS_VARIANT: Record<string, "success"|"warning"|"destructive"|"pending"> = {
  SUCCESS: "success", PENDING: "pending", FAILED: "destructive", REVERSED: "warning",
};

const isCredit = (type: string) =>
  ["FUND", "TRANSFER_IN", "LOAN_CREDIT"].includes(type);

export default function DashboardPage() {
  const [wallet, setWallet] = useState<Wallet | null>(null);
  const [txns, setTxns] = useState<Transaction[]>([]);
  const [kyc, setKyc] = useState<KYCStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get("/wallet/"),
      api.get("/wallet/history/"),
      api.get("/wallet/kyc/status/"),
    ]).then(([w, h, k]) => {
      setWallet(w.data);
      setTxns(h.data.transactions?.slice(0, 5) ?? []);
      setKyc(k.data);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse p-4">
        <div className="h-40 rounded-2xl bg-blue-200/60" />
        <div className="grid grid-cols-3 gap-3">
          {[...Array(6)].map((_, i) => <div key={i} className="h-20 rounded-2xl bg-white/80" />)}
        </div>
        <div className="h-64 rounded-2xl bg-white/80" />
      </div>
    );
  }

  return (
    <div className="space-y-5 pb-8">

      {/* Hero balance card — blue gradient like reference */}
      <div className="hero-gradient rounded-2xl p-6 text-white relative overflow-hidden mx-1">
        {/* Decorative circles */}
        <div className="absolute -right-8 -top-8 h-32 w-32 rounded-full bg-white/10" />
        <div className="absolute -right-2 top-12 h-20 w-20 rounded-full bg-white/10" />

        <p className="text-white/70 text-sm font-medium">Available Balance</p>
        <p className="text-4xl font-bold mt-1 tabular-nums relative z-10">
          {wallet ? formatNaira(wallet.balance) : "₦0.00"}
        </p>
        <div className="flex items-center gap-3 mt-4 text-white/60 text-xs">
          <span>Acct: {wallet?.account_no ?? "—"}</span>
          <span>·</span>
          <span>Limit: {wallet ? formatNaira(wallet.credit_limit) : "—"}</span>
        </div>

        {/* KYC tier pill */}
        {kyc && (
          <div className="mt-3 inline-flex items-center gap-1.5 bg-white/20 rounded-full px-3 py-1">
            <div className="h-2 w-2 rounded-full bg-white" />
            <span className="text-xs text-white font-medium">{kyc.tier_label}</span>
          </div>
        )}
      </div>

      {/* Quick actions — pastel icon grid like reference */}
      <div className="bg-white rounded-2xl p-4 card-shadow mx-1">
        <div className="grid grid-cols-3 gap-4">
          {quickActions.map(({ href, label, icon: Icon, bg, color }) => (
            <Link key={href} href={href}>
              <div className="flex flex-col items-center gap-2 py-2">
                <div className={`h-12 w-12 rounded-2xl flex items-center justify-center ${bg}`}>
                  <Icon className={`h-5 w-5 ${color}`} />
                </div>
                <span className="text-xs font-medium text-muted-foreground text-center leading-tight">
                  {label}
                </span>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* KYC next step hint */}
      {kyc && kyc.kyc_tier < 3 && (
        <div className="mx-1 bg-white rounded-2xl p-4 card-shadow border-l-4 border-primary">
          <p className="text-xs text-muted-foreground">Next tier</p>
          <p className="text-sm font-medium text-foreground mt-0.5">{kyc.next_tier_requires}</p>
          <Link href="/dashboard/kyc" className="text-xs text-primary font-semibold mt-2 inline-block">
            Upgrade now →
          </Link>
        </div>
      )}

      {/* Recent transactions — list card style from reference */}
      <div className="bg-white rounded-2xl card-shadow mx-1 overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <p className="font-bold text-foreground">Recent Transactions</p>
          <Link href="/dashboard/history"
            className="text-xs text-primary font-semibold">
            See all
          </Link>
        </div>

        {txns.length === 0 ? (
          <div className="py-12 text-center text-muted-foreground text-sm">
            No transactions yet.
          </div>
        ) : (
          <div>
            {txns.map((t) => (
              <div key={t.reference}
                className="flex items-center justify-between px-5 py-4 border-b border-border/60 last:border-0">
                <div className="flex items-center gap-3">
                  <div className={`h-10 w-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
                    isCredit(t.type) ? "icon-teal" : "icon-pink"
                  }`}>
                    {isCredit(t.type)
                      ? <ArrowDownLeft className="h-5 w-5 text-teal-600" />
                      : <ArrowUpRight className="h-5 w-5 text-pink-500" />
                    }
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-foreground capitalize">
                      {t.type.replace(/_/g, " ").toLowerCase()}
                    </p>
                    <p className="text-xs text-muted-foreground">{formatDate(t.date)}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={`font-bold text-sm ${isCredit(t.type) ? "text-teal-600" : "text-rose-500"}`}>
                    {isCredit(t.type) ? "+" : "−"}{formatNaira(t.amount)}
                  </p>
                  <Badge variant={STATUS_VARIANT[t.status] ?? "secondary"} className="text-xs mt-0.5">
                    {t.status}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Wallet limits card */}
      {wallet && (
        <div className="mx-1 bg-white rounded-2xl p-5 card-shadow">
          <p className="font-bold text-foreground mb-3">Wallet Limits</p>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-background rounded-xl p-3">
              <p className="text-xs text-muted-foreground">Debit Floor</p>
              <p className="font-bold text-foreground mt-1">{formatNaira(wallet.debit_limit)}</p>
            </div>
            <div className="bg-background rounded-xl p-3">
              <p className="text-xs text-muted-foreground">Credit Ceiling</p>
              <p className="font-bold text-primary mt-1">{formatNaira(wallet.credit_limit)}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}



