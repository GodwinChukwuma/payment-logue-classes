"use client";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { Loader2, CheckCircle2, ArrowLeftRight } from "lucide-react";
import { formatNaira } from "@/lib/utils";
import api from "@/lib/api";

export default function TransferPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{amount:string;new_balance:string;recipient_account:string}|null>(null);
  const { register, handleSubmit, reset } = useForm({
    defaultValues: { recipient_account_no:"", amount:"", pin:"", description:"" },
  });

  const onSubmit = async (data: Record<string,string>) => {
    setLoading(true);
    try {
      const res = await api.post("/wallet/transfer/", data);
      setResult(res.data);
      toast.success("Transfer successful!");
    } catch (err: unknown) {
      toast.error((err as {response?:{data?:{error?:{message?:string}}}})?.response?.data?.error?.message ?? "Failed");
    } finally { setLoading(false); }
  };

  if (result) return (
    <div className="space-y-4 pb-8">
      <div className="px-1"><h1 className="text-xl font-bold">Transfer</h1></div>
      <div className="bg-white rounded-2xl p-8 card-shadow flex flex-col items-center text-center gap-4">
        <div className="h-16 w-16 rounded-full icon-teal flex items-center justify-center">
          <CheckCircle2 className="h-8 w-8 text-teal-600" />
        </div>
        <div>
          <h2 className="text-lg font-bold">Transfer Successful!</h2>
          <p className="text-muted-foreground text-sm mt-1">
            {formatNaira(result.amount)} sent to {result.recipient_account}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            New balance: <strong className="text-primary">{formatNaira(result.new_balance)}</strong>
          </p>
        </div>
        <button onClick={() => { setResult(null); reset(); }}
          className="px-6 py-3 bg-primary text-white rounded-xl text-sm font-semibold hover:bg-primary/90 transition-all">
          New Transfer
        </button>
      </div>
    </div>
  );

  return (
    <div className="space-y-4 pb-8">
      <div className="px-1"><h1 className="text-xl font-bold">Transfer</h1>
        <p className="text-muted-foreground text-sm">Send to another VelaWallet account</p></div>

      <div className="hero-gradient rounded-2xl p-6 flex items-center gap-4 relative overflow-hidden">
        <div className="absolute -right-6 -bottom-6 h-28 w-28 rounded-full bg-white/10" />
        <div className="h-14 w-14 rounded-2xl bg-white/20 flex items-center justify-center flex-shrink-0">
          <ArrowLeftRight className="h-7 w-7 text-white" />
        </div>
        <div className="text-white">
          <p className="font-bold text-lg">Intra-wallet Transfer</p>
          <p className="text-white/70 text-sm">Instant, within VelaWallet</p>
        </div>
      </div>

      <div className="bg-white rounded-2xl p-5 card-shadow">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {[
            { id:"recipient_account_no", label:"Recipient Account Number", placeholder:"10-digit wallet number", type:"text" },
            { id:"amount", label:"Amount (₦)", placeholder:"Amount", type:"number" },
            { id:"description", label:"Description (optional)", placeholder:"e.g. Rent payment", type:"text" },
            { id:"pin", label:"Transaction PIN", placeholder:"Your PIN", type:"password" },
          ].map(({ id, label, placeholder, type }) => (
            <div key={id}>
              <label className="text-sm font-medium block mb-1.5">{label}</label>
              <input type={type} placeholder={placeholder}
                className="w-full h-11 px-4 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                {...register(id as "recipient_account_no"|"amount"|"description"|"pin", { required: id !== "description" })} />
            </div>
          ))}
          <button type="submit" disabled={loading}
            className="w-full h-12 rounded-xl bg-primary text-white font-semibold text-sm flex items-center justify-center gap-2 hover:bg-primary/90 transition-all disabled:opacity-60">
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
            Transfer
          </button>
        </form>
      </div>
    </div>
  );
}

