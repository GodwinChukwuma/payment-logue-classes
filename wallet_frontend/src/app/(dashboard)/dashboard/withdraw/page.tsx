"use client";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { Loader2, Search, CheckCircle2, ArrowUpRight } from "lucide-react";
import { formatNaira } from "@/lib/utils";
import api from "@/lib/api";
import type { Bank } from "@/types";

type Step = "form" | "otp" | "done";

export default function WithdrawPage() {
  const [banks, setBanks] = useState<Bank[]>([]);
  const [step, setStep] = useState<Step>("form");
  const [loading, setLoading] = useState(false);
  const [resolving, setResolving] = useState(false);
  const [accountName, setAccountName] = useState("");
  const [transferCode, setTransferCode] = useState("");
  const [otp, setOtp] = useState("");
  const [finalizing, setFinalizing] = useState(false);
  const [summary, setSummary] = useState<{amount:string;recipient:string}|null>(null);

  const { register, handleSubmit, watch, setValue } = useForm({
    defaultValues: { amount:"", bank_code:"", account_number:"", pin:"" },
  });
  const bankCode = watch("bank_code");
  const accountNumber = watch("account_number");

  useEffect(() => { api.get("/payments/banks/").then((r) => setBanks(r.data.banks ?? [])); }, []);

  const resolveAccount = async () => {
    if (!bankCode || accountNumber.length < 10) return;
    setResolving(true); setAccountName("");
    try {
      const res = await api.post("/payments/withdraw/resolve/", { bank_code: bankCode, account_number: accountNumber });
      setAccountName(res.data.account_name);
      toast.success(`Verified: ${res.data.account_name}`);
    } catch { toast.error("Could not verify account."); }
    finally { setResolving(false); }
  };

  const onSubmit = async (data: Record<string,string>) => {
    if (!accountName) { toast.error("Verify account first"); return; }
    setLoading(true);
    try {
      const res = await api.post("/payments/withdraw/initialize/", { ...data, account_name: accountName });
      setTransferCode(res.data.transfer_code);
      setSummary({ amount: data.amount, recipient: accountName });
      setStep("otp");
      toast.success("Check your email for the Paystack OTP.");
    } catch (err: unknown) {
      toast.error((err as {response?:{data?:{error?:{message?:string}}}})?.response?.data?.error?.message ?? "Failed");
    } finally { setLoading(false); }
  };

  const finalizeTransfer = async () => {
    if (otp.length !== 6) { toast.error("Enter the 6-digit OTP"); return; }
    setFinalizing(true);
    try {
      await api.post("/payments/withdraw/finalize/", { transfer_code: transferCode, otp });
      setStep("done");
      toast.success("Withdrawal completed!");
    } catch (err: unknown) {
      toast.error((err as {response?:{data?:{error?:{message?:string}}}})?.response?.data?.error?.message ?? "Invalid OTP");
    } finally { setFinalizing(false); }
  };

  if (step === "done") return (
    <div className="space-y-4 pb-8">
      <div className="px-1"><h1 className="text-xl font-bold">Withdraw</h1></div>
      <div className="bg-white rounded-2xl p-8 card-shadow flex flex-col items-center text-center gap-4">
        <div className="h-16 w-16 rounded-full icon-teal flex items-center justify-center">
          <CheckCircle2 className="h-8 w-8 text-teal-600" />
        </div>
        <div>
          <h2 className="text-lg font-bold">Withdrawal Complete!</h2>
          <p className="text-muted-foreground text-sm mt-1">
            {summary && `${formatNaira(summary.amount)} sent to ${summary.recipient}`}
          </p>
        </div>
        <button onClick={() => { setStep("form"); setAccountName(""); setOtp(""); }}
          className="px-6 py-3 bg-primary text-white rounded-xl text-sm font-semibold hover:bg-primary/90 transition-all">
          New Withdrawal
        </button>
      </div>
    </div>
  );

  if (step === "otp") return (
    <div className="space-y-4 pb-8">
      <div className="px-1"><h1 className="text-xl font-bold">Confirm Transfer</h1></div>

      {summary && (
        <div className="hero-gradient rounded-2xl p-6 text-white relative overflow-hidden">
          <div className="absolute -right-6 -top-6 h-24 w-24 rounded-full bg-white/10" />
          <p className="text-white/70 text-sm">Amount</p>
          <p className="text-3xl font-bold mt-1">{formatNaira(summary.amount)}</p>
          <p className="text-white/60 text-sm mt-2">To: {summary.recipient}</p>
          <p className="text-white/40 text-xs mt-1 font-mono">{transferCode}</p>
        </div>
      )}

      <div className="bg-white rounded-2xl p-5 card-shadow space-y-4">
        <div>
          <label className="text-sm font-medium text-foreground block mb-1.5">
            6-digit OTP from Paystack email
          </label>
          <input
            type="text" maxLength={6} placeholder="000000"
            className="w-full h-14 px-4 rounded-xl border border-border bg-background text-center text-3xl font-bold tracking-[0.5em] focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
            value={otp} onChange={(e) => setOtp(e.target.value.replace(/\D/g,"").slice(0,6))}
          />
        </div>
        <button onClick={finalizeTransfer} disabled={finalizing || otp.length !== 6}
          className="w-full h-12 rounded-xl bg-primary text-white font-semibold text-sm flex items-center justify-center gap-2 hover:bg-primary/90 transition-all disabled:opacity-60">
          {finalizing && <Loader2 className="h-4 w-4 animate-spin" />}
          Confirm Transfer
        </button>
      </div>
    </div>
  );

  return (
    <div className="space-y-4 pb-8">
      <div className="px-1"><h1 className="text-xl font-bold">Withdraw</h1>
        <p className="text-muted-foreground text-sm">Send to your bank account</p></div>

      <div className="hero-gradient rounded-2xl p-6 flex items-center gap-4 relative overflow-hidden">
        <div className="absolute -right-6 -bottom-6 h-28 w-28 rounded-full bg-white/10" />
        <div className="h-14 w-14 rounded-2xl bg-white/20 flex items-center justify-center flex-shrink-0">
          <ArrowUpRight className="h-7 w-7 text-white" />
        </div>
        <div className="text-white">
          <p className="font-bold text-lg">Bank Withdrawal</p>
          <p className="text-white/70 text-sm">KYC + PIN required</p>
        </div>
      </div>

      <div className="bg-white rounded-2xl p-5 card-shadow">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="text-sm font-medium block mb-1.5">Amount (₦)</label>
            <input type="number" min="100" placeholder="Minimum ₦100"
              className="w-full h-11 px-4 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
              {...register("amount", { required: true })} />
          </div>

          <div>
            <label className="text-sm font-medium block mb-1.5">Bank</label>
            <select
              className="w-full h-11 px-4 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
              onChange={(e) => setValue("bank_code", e.target.value)}
              defaultValue=""
            >
              <option value="" disabled>Select bank</option>
              {banks.map((b) => <option key={b.code} value={b.code}>{b.name}</option>)}
            </select>
          </div>

          <div>
            <label className="text-sm font-medium block mb-1.5">Account Number</label>
            <div className="flex gap-2">
              <input type="text" maxLength={10} placeholder="10-digit account number"
                className="flex-1 h-11 px-4 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                {...register("account_number", { required: true })} />
              <button type="button" onClick={resolveAccount}
                disabled={resolving || !bankCode || accountNumber.length < 10}
                className="h-11 px-4 rounded-xl bg-primary/10 text-primary font-semibold text-sm flex items-center gap-1.5 hover:bg-primary/20 transition-all disabled:opacity-40">
                {resolving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                Verify
              </button>
            </div>
          </div>

          {accountName && (
            <div className="p-3 icon-teal rounded-xl flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-teal-600 flex-shrink-0" />
              <div>
                <p className="text-xs text-teal-600 font-medium">Account verified</p>
                <p className="text-sm font-bold text-teal-800">{accountName}</p>
              </div>
            </div>
          )}

          <div>
            <label className="text-sm font-medium block mb-1.5">Transaction PIN</label>
            <input type="password" maxLength={6} placeholder="Your PIN"
              className="w-full h-11 px-4 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
              {...register("pin", { required: true })} />
          </div>

          <button type="submit" disabled={loading || !accountName}
            className="w-full h-12 rounded-xl bg-primary text-white font-semibold text-sm flex items-center justify-center gap-2 hover:bg-primary/90 transition-all disabled:opacity-60">
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
            Withdraw
          </button>
        </form>
      </div>
    </div>
  );
}
