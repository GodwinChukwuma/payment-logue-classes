"use client";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { Loader2, Plus, CreditCard, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { formatNaira, formatDate } from "@/lib/utils";
import api from "@/lib/api";
import type { Loan } from "@/types";

const STATUS_VARIANT: Record<string,"pending"|"success"|"destructive"> = {
  ACTIVE:"pending", CLOSED:"success", REJECTED:"destructive",
};

export default function LoansPage() {
  const [loans, setLoans] = useState<Loan[]>([]);
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState(false);
  const [repaying, setRepaying] = useState<number|null>(null);
  const [showForm, setShowForm] = useState(false);
  const [repayAmounts, setRepayAmounts] = useState<Record<number,string>>({});

  const { register, handleSubmit, reset } = useForm({
    defaultValues: { amount_requested:"", duration_months:"", pin:"" },
  });

  const fetchLoans = () => {
    api.get("/loans/").then((r) => setLoans(r.data.loans ?? [])).finally(() => setLoading(false));
  };
  useEffect(() => { fetchLoans(); }, []);

  const onApply = async (data: Record<string,string>) => {
    setApplying(true);
    try {
      await api.post("/loans/apply/", data);
      toast.success("Loan application submitted!");
      setShowForm(false); reset(); fetchLoans();
    } catch (err: unknown) {
      toast.error((err as {response?:{data?:{error?:{message?:string}}}})?.response?.data?.error?.message ?? "Failed");
    } finally { setApplying(false); }
  };

  const onRepay = async (loanId: number) => {
    setRepaying(loanId);
    try {
      const pin = prompt("Enter your transaction PIN:");
      if (!pin) return;
      const amount = repayAmounts[loanId];
      await api.post(`/loans/${loanId}/repay/`, { pin, ...(amount ? { amount } : {}) });
      toast.success("Repayment successful!");
      fetchLoans();
    } catch (err: unknown) {
      toast.error((err as {response?:{data?:{error?:{message?:string}}}})?.response?.data?.error?.message ?? "Failed");
    } finally { setRepaying(null); }
  };

  return (
    <div className="space-y-4 pb-8">
      <div className="flex items-center justify-between px-1">
        <div>
          <h1 className="text-xl font-bold">Loans</h1>
          <p className="text-muted-foreground text-sm">Apply based on your KYC tier</p>
        </div>
        <button onClick={() => setShowForm(!showForm)}
          className="h-10 px-4 rounded-xl bg-primary text-white text-sm font-semibold flex items-center gap-2 hover:bg-primary/90 transition-all">
          <Plus className="h-4 w-4" /> Apply
        </button>
      </div>

      {/* Tier info banner */}
      <div className="hero-gradient rounded-2xl p-5 flex items-center gap-4 relative overflow-hidden">
        <div className="absolute -right-4 -bottom-4 h-24 w-24 rounded-full bg-white/10" />
        <div className="h-12 w-12 rounded-2xl bg-white/20 flex items-center justify-center flex-shrink-0">
          <CreditCard className="h-6 w-6 text-white" />
        </div>
        <div className="text-white text-sm">
          <p className="font-bold">Tier 1: up to ₦2,000</p>
          <p className="text-white/70">Tier 2: up to ₦10,000 · Tier 3: up to ₦1,000,000</p>
        </div>
      </div>

      {/* Apply form */}
      {showForm && (
        <div className="bg-white rounded-2xl p-5 card-shadow">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-bold text-foreground">New Loan Application</h2>
            <button onClick={() => setShowForm(false)} className="text-muted-foreground hover:text-foreground">
              <X className="h-5 w-5" />
            </button>
          </div>
          <form onSubmit={handleSubmit(onApply)} className="space-y-3.5">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-sm font-medium block mb-1.5">Amount (₦)</label>
                <input type="number" placeholder="e.g. 5000"
                  className="w-full h-11 px-4 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                  {...register("amount_requested", { required: true })} />
              </div>
              <div>
                <label className="text-sm font-medium block mb-1.5">Duration (months)</label>
                <input type="number" min="1" placeholder="e.g. 3"
                  className="w-full h-11 px-4 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                  {...register("duration_months", { required: true })} />
              </div>
            </div>
            <div>
              <label className="text-sm font-medium block mb-1.5">Transaction PIN</label>
              <input type="password" maxLength={6} placeholder="Your PIN"
                className="w-full h-11 px-4 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                {...register("pin", { required: true })} />
            </div>
            <div className="flex gap-3">
              <button type="submit" disabled={applying}
                className="flex-1 h-11 rounded-xl bg-primary text-white font-semibold text-sm flex items-center justify-center gap-2 hover:bg-primary/90 transition-all disabled:opacity-60">
                {applying && <Loader2 className="h-4 w-4 animate-spin" />} Submit
              </button>
              <button type="button" onClick={() => setShowForm(false)}
                className="h-11 px-5 rounded-xl border border-border text-sm font-medium hover:bg-muted transition-all">
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Loans list */}
      {loading ? (
        <div className="space-y-3 animate-pulse">
          {[...Array(2)].map((_, i) => <div key={i} className="h-44 bg-white rounded-2xl" />)}
        </div>
      ) : loans.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center card-shadow">
          <CreditCard className="h-12 w-12 text-muted-foreground/30 mx-auto mb-3" />
          <p className="text-muted-foreground text-sm">No loans yet. Click Apply to get started.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {loans.map((loan) => (
            <div key={loan.id} className="bg-white rounded-2xl card-shadow overflow-hidden">
              {/* Loan header */}
              <div className="px-5 py-4 border-b border-border/60 flex items-center justify-between">
                <div>
                  <p className="font-bold text-foreground">Loan #{loan.user_loan_number}</p>
                  <p className="text-xs text-muted-foreground">{formatDate(loan.created_at)}</p>
                </div>
                <Badge variant={STATUS_VARIANT[loan.status]}>{loan.status}</Badge>
              </div>

              {/* Loan stats grid */}
              <div className="grid grid-cols-3 gap-px bg-border/30 border-b border-border/30">
                {[
                  { label:"Approved", value: formatNaira(loan.amount_approved||loan.amount_requested) },
                  { label:"Monthly", value: formatNaira(loan.monthly_instalment) },
                  { label:"Outstanding", value: formatNaira(loan.outstanding_balance) },
                ].map(({ label, value }) => (
                  <div key={label} className="bg-white px-4 py-3 text-center">
                    <p className="text-xs text-muted-foreground">{label}</p>
                    <p className="text-sm font-bold text-foreground mt-0.5">{value}</p>
                  </div>
                ))}
              </div>

              {/* Repay */}
              {loan.status === "ACTIVE" && (
                <div className="px-5 py-3 flex gap-2">
                  <input type="number" placeholder="Amount (blank = next instalment)"
                    className="flex-1 h-10 px-3 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                    value={repayAmounts[loan.id]??""} onChange={(e) => setRepayAmounts(p=>({...p,[loan.id]:e.target.value}))} />
                  <button onClick={() => onRepay(loan.id)} disabled={repaying===loan.id}
                    className="h-10 px-4 rounded-xl bg-primary text-white text-sm font-semibold flex items-center gap-1.5 hover:bg-primary/90 transition-all disabled:opacity-60">
                    {repaying===loan.id && <Loader2 className="h-3 w-3 animate-spin" />} Repay
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

