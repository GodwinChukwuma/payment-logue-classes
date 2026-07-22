"use client";
import { useState } from "react";
import { toast } from "sonner";
import { Loader2, CheckCircle2, ExternalLink, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { formatNaira } from "@/lib/utils";
import api from "@/lib/api";

const DarkInput = ({ placeholder, value, onChange, type="text" }: {placeholder:string;value?:string;onChange?:(v:string)=>void;type?:string}) => (
  <input type={type} placeholder={placeholder} value={value} onChange={e=>onChange?.(e.target.value)}
    className="w-full h-12 px-4 rounded-xl text-white/80 text-sm placeholder-white/20 outline-none transition-all"
    style={{background:"rgba(255,255,255,0.05)",border:"1px solid rgba(255,255,255,0.08)"}}
    onFocus={e=>e.target.style.borderColor="#7c3aed"} onBlur={e=>e.target.style.borderColor="rgba(255,255,255,0.08)"} />
);

export default function FundPage() {
  const [amount, setAmount] = useState("");
  const [loading, setLoading] = useState(false);
  const [checkoutUrl, setCheckoutUrl] = useState<string|null>(null);
  const [reference, setReference] = useState<string|null>(null);
  const [verifying, setVerifying] = useState(false);
  const [credited, setCredited] = useState(false);
  const [newBalance, setNewBalance] = useState("");

  const handleFund = async () => {
    if (Number(amount)<100) { toast.error("Minimum ₦100"); return; }
    setLoading(true);
    try {
      const r = await api.post("/payments/fund/initialize/",{amount});
      setCheckoutUrl(r.data.checkout_url); setReference(r.data.reference);
      toast.success("Initialized. Opening Paystack…");
      window.open(r.data.checkout_url,"_blank");
    } catch (err:unknown) { toast.error((err as {response?:{data?:{error?:{message?:string}}}})?.response?.data?.error?.message??"Failed"); }
    finally { setLoading(false); }
  };

  const verify = async () => {
    if (!reference) return;
    setVerifying(true);
    try {
      const r = await api.get(`/payments/callback?reference=${reference}`);
      if (r.data.success) { setCredited(true); setNewBalance(r.data.new_balance); toast.success("Wallet credited!"); }
    } catch { toast.error("Payment not confirmed yet."); }
    finally { setVerifying(false); }
  };

  const Card = ({children}:{children:React.ReactNode}) => (
    <div className="rounded-2xl p-6 max-w-md mx-auto" style={{background:"rgba(255,255,255,0.04)",border:"1px solid rgba(255,255,255,0.08)",backdropFilter:"blur(20px)"}}>
      {children}
    </div>
  );

  return (
    <div className="p-4 lg:p-8 space-y-5 max-w-2xl mx-auto">
      <Link href="/dashboard" className="flex items-center gap-1.5 text-white/40 hover:text-white/70 text-sm transition-colors">
        <ArrowLeft className="h-4 w-4"/> Home
      </Link>

      {credited ? (
        <Card>
          <div className="text-center py-6 space-y-4">
            <div className="h-16 w-16 rounded-full flex items-center justify-center mx-auto" style={{background:"rgba(5,150,105,0.15)"}}>
              <CheckCircle2 className="h-8 w-8 text-emerald-400"/>
            </div>
            <div>
              <p className="text-white font-bold text-xl">Wallet Funded!</p>
              <p className="text-white/40 text-sm mt-1">{formatNaira(amount)} added · Balance: {formatNaira(newBalance)}</p>
            </div>
            <div className="flex gap-3 justify-center">
              <Link href="/dashboard" className="px-5 py-2.5 rounded-xl text-sm text-white/50" style={{border:"1px solid rgba(255,255,255,0.1)"}}>Home</Link>
              <button onClick={()=>{setCredited(false);setCheckoutUrl(null);setReference(null);setAmount("");}}
                className="px-5 py-2.5 rounded-xl text-sm font-semibold text-white" style={{background:"linear-gradient(90deg,#7c3aed,#db2777)"}}>Fund again</button>
            </div>
          </div>
        </Card>
      ) : checkoutUrl ? (
        <Card>
          <p className="text-white font-bold text-xl mb-1">Complete Payment</p>
          <p className="text-white/40 text-sm mb-5">Pay on Paystack, then come back and confirm.</p>
          <div className="p-4 rounded-xl mb-4" style={{background:"rgba(255,255,255,0.04)"}}>
            <p className="text-white/40 text-xs">Amount</p>
            <p className="text-white font-bold text-2xl">{formatNaira(amount)}</p>
            <p className="text-white/25 text-xs font-mono mt-1">{reference}</p>
          </div>
          <div className="space-y-3">
            <button onClick={()=>window.open(checkoutUrl,"_blank")}
              className="w-full h-11 rounded-xl text-white text-sm font-semibold flex items-center justify-center gap-2"
              style={{background:"rgba(255,255,255,0.08)",border:"1px solid rgba(255,255,255,0.12)"}}>
              <ExternalLink className="h-4 w-4"/> Open Paystack
            </button>
            <button onClick={verify} disabled={verifying}
              className="w-full h-11 rounded-xl text-white text-sm font-semibold flex items-center justify-center gap-2 hover:opacity-90 disabled:opacity-40"
              style={{background:"linear-gradient(90deg,#059669,#16a34a)"}}>
              {verifying&&<Loader2 className="h-4 w-4 animate-spin"/>} I&apos;ve Paid — Confirm
            </button>
            <button onClick={()=>{setCheckoutUrl(null);setReference(null);}} className="w-full text-white/25 hover:text-white/50 text-xs py-1 transition-colors">Cancel</button>
          </div>
        </Card>
      ) : (
        <Card>
          <p className="text-white font-bold text-xl mb-1">💰 Fund Wallet</p>
          <p className="text-white/40 text-sm mb-5">Add money via Paystack. Minimum ₦100.</p>
          <div className="space-y-4">
            <div>
              <p className="text-white/50 text-xs mb-1.5">Amount (₦)</p>
              <DarkInput placeholder="e.g. 5000" value={amount} onChange={setAmount} type="number"/>
              {amount && Number(amount)>=100 && <p className="text-purple-400 text-xs mt-1">You will pay {formatNaira(amount)}</p>}
            </div>
            <button onClick={handleFund} disabled={loading}
              className="w-full h-12 rounded-xl text-white font-semibold text-sm flex items-center justify-center gap-2 hover:opacity-90 disabled:opacity-40"
              style={{background:"linear-gradient(90deg,#059669,#16a34a)"}}>
              {loading&&<Loader2 className="h-4 w-4 animate-spin"/>} Initialize Payment
            </button>
          </div>
        </Card>
      )}
    </div>
  );
}





