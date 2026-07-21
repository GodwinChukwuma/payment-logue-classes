"use client";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Loader2, ExternalLink, CheckCircle2, ArrowDownLeft } from "lucide-react";
import { formatNaira } from "@/lib/utils";
import api from "@/lib/api";

const schema = z.object({
  amount: z.string().min(1).refine((v) => Number(v) >= 100, "Minimum ₦100"),
});
type FormData = z.infer<typeof schema>;

export default function FundPage() {
  const [loading, setLoading] = useState(false);
  const [checkoutUrl, setCheckoutUrl] = useState<string|null>(null);
  const [reference, setReference] = useState<string|null>(null);
  const [verifying, setVerifying] = useState(false);
  const [credited, setCredited] = useState(false);
  const [newBalance, setNewBalance] = useState("");

  const { register, handleSubmit, watch, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema), defaultValues: { amount: "" },
  });
  const amount = watch("amount");

  const onSubmit = async (data: FormData) => {
    setLoading(true);
    try {
      const res = await api.post("/payments/fund/initialize/", { amount: data.amount });
      setCheckoutUrl(res.data.checkout_url);
      setReference(res.data.reference);
      toast.success("Payment initialized.");
    } catch (err: unknown) {
      toast.error((err as {response?:{data?:{error?:{message?:string}}}})?.response?.data?.error?.message ?? "Failed");
    } finally { setLoading(false); }
  };

  const verifyPayment = async () => {
    if (!reference) return;
    setVerifying(true);
    try {
      const res = await api.get(`/payments/callback?reference=${reference}`);
      if (res.data.success) {
        setCredited(true);
        setNewBalance(res.data.new_balance);
        toast.success("Wallet credited!");
      }
    } catch { toast.error("Payment not confirmed. Complete payment on Paystack first."); }
    finally { setVerifying(false); }
  };

  if (credited) return (
    <div className="space-y-4 pb-8">
      <div className="px-1"><h1 className="text-xl font-bold">Fund Wallet</h1></div>
      <div className="bg-white rounded-2xl p-8 card-shadow flex flex-col items-center text-center gap-4">
        <div className="h-16 w-16 rounded-full icon-teal flex items-center justify-center">
          <CheckCircle2 className="h-8 w-8 text-teal-600" />
        </div>
        <div>
          <h2 className="text-lg font-bold text-foreground">Wallet Funded!</h2>
          <p className="text-muted-foreground text-sm mt-1">
            {formatNaira(amount)} added. New balance: <strong>{formatNaira(newBalance)}</strong>
          </p>
        </div>
        <button onClick={() => { setCheckoutUrl(null); setReference(null); setCredited(false); }}
          className="px-6 py-3 bg-primary text-white rounded-xl text-sm font-semibold hover:bg-primary/90 transition-all">
          Fund again
        </button>
      </div>
    </div>
  );

  if (checkoutUrl) return (
    <div className="space-y-4 pb-8">
      <div className="px-1"><h1 className="text-xl font-bold">Complete Payment</h1></div>

      {/* Amount summary card */}
      <div className="hero-gradient rounded-2xl p-6 text-white relative overflow-hidden">
        <div className="absolute -right-6 -top-6 h-24 w-24 rounded-full bg-white/10" />
        <p className="text-white/70 text-sm">Amount to pay</p>
        <p className="text-3xl font-bold mt-1">{formatNaira(amount)}</p>
        <p className="text-white/50 text-xs mt-2 font-mono">{reference}</p>
      </div>

      <div className="bg-white rounded-2xl p-5 card-shadow space-y-3">
        <button onClick={() => window.open(checkoutUrl, "_blank")}
          className="w-full h-12 rounded-xl bg-primary text-white font-semibold text-sm flex items-center justify-center gap-2 hover:bg-primary/90 transition-all">
          <ExternalLink className="h-4 w-4" />
          Open Paystack Checkout
        </button>
        <button onClick={verifyPayment} disabled={verifying}
          className="w-full h-12 rounded-xl border-2 border-primary text-primary font-semibold text-sm flex items-center justify-center gap-2 hover:bg-primary/5 transition-all disabled:opacity-60">
          {verifying && <Loader2 className="h-4 w-4 animate-spin" />}
          I&apos;ve Paid — Confirm
        </button>
      </div>

      <div className="bg-blue-50 rounded-2xl p-4 border border-blue-100">
        <ol className="text-sm text-blue-700 space-y-1.5 list-decimal list-inside">
          <li>Click &quot;Open Paystack Checkout&quot; and complete payment</li>
          <li>Return here and click &quot;I&apos;ve Paid — Confirm&quot;</li>
          <li>Your wallet will be credited instantly</li>
        </ol>
      </div>
    </div>
  );

  return (
    <div className="space-y-4 pb-8">
      <div className="px-1"><h1 className="text-xl font-bold">Fund Wallet</h1>
        <p className="text-muted-foreground text-sm">Add money via Paystack</p></div>

      {/* Hero icon */}
      <div className="hero-gradient rounded-2xl p-6 flex items-center gap-4 relative overflow-hidden">
        <div className="absolute -right-6 -bottom-6 h-28 w-28 rounded-full bg-white/10" />
        <div className="h-14 w-14 rounded-2xl bg-white/20 flex items-center justify-center flex-shrink-0">
          <ArrowDownLeft className="h-7 w-7 text-white" />
        </div>
        <div className="text-white">
          <p className="font-bold text-lg">Fund your wallet</p>
          <p className="text-white/70 text-sm">Minimum: ₦100</p>
        </div>
      </div>

      <div className="bg-white rounded-2xl p-5 card-shadow space-y-4">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="text-sm font-medium text-foreground block mb-1.5">Amount (₦)</label>
            <input type="number" min="100" placeholder="e.g. 5000"
              className="w-full h-12 px-4 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
              {...register("amount")} />
            {errors.amount && <p className="text-xs text-destructive mt-1">{errors.amount.message}</p>}
            {amount && Number(amount) >= 100 && (
              <p className="text-xs text-muted-foreground mt-1">
                You will be charged <span className="font-semibold text-primary">{formatNaira(amount)}</span>
              </p>
            )}
          </div>
          <button type="submit" disabled={loading}
            className="w-full h-12 rounded-xl bg-primary text-white font-semibold text-sm flex items-center justify-center gap-2 hover:bg-primary/90 transition-all disabled:opacity-60">
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
            Initialize Payment
          </button>
        </form>
      </div>
    </div>
  );
}



