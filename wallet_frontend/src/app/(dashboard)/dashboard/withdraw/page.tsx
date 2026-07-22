"use client";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Loader2, Search, CheckCircle2, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { formatNaira } from "@/lib/utils";
import api from "@/lib/api";
import type { Bank } from "@/types";

const DarkInput = ({ placeholder, value, onChange, type="text" }: {
  placeholder:string; value?:string; onChange?:(v:string)=>void; type?:string;
}) => (
  <input type={type} placeholder={placeholder} value={value} onChange={e=>onChange?.(e.target.value)}
    className="w-full h-11 px-4 rounded-xl text-white/80 text-sm placeholder-white/20 outline-none transition-all"
    style={{ background:"rgba(255,255,255,0.05)", border:"1px solid rgba(255,255,255,0.08)" }}
    onFocus={e=>e.target.style.borderColor="#7c3aed"}
    onBlur={e=>e.target.style.borderColor="rgba(255,255,255,0.08)"} />
);

type Step = "form"|"otp"|"done";

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
  const [bankCode, setBankCode] = useState("");
  const [accountNumber, setAccountNumber] = useState("");
  const [amount, setAmount] = useState("");
  const [pin, setPin] = useState("");

  useEffect(() => { api.get("/payments/banks/").then(r=>setBanks(r.data.banks??[])); }, []);

  const resolve = async () => {
    if (!bankCode || accountNumber.length < 10) return;
    setResolving(true); setAccountName("");
    try {
      const r = await api.post("/payments/withdraw/resolve/", { bank_code:bankCode, account_number:accountNumber });
      setAccountName(r.data.account_name);
      toast.success(`Verified: ${r.data.account_name}`);
    } catch { toast.error("Could not verify account."); }
    finally { setResolving(false); }
  };

  const initWithdraw = async () => {
    if (!accountName||!amount||!pin) { toast.error("Fill all fields"); return; }
    setLoading(true);
    try {
      const r = await api.post("/payments/withdraw/initialize/", { amount, bank_code:bankCode, account_number:accountNumber, account_name:accountName, pin });
      setTransferCode(r.data.transfer_code);
      setSummary({ amount, recipient:accountName });
      setStep("otp");
      toast.success("Check your email for Paystack OTP.");
    } catch (err: unknown) {
      toast.error((err as {response?:{data?:{error?:{message?:string}}}})?.response?.data?.error?.message ?? "Failed");
    } finally { setLoading(false); }
  };

  const finalize = async () => {
    if (otp.length!==6) { toast.error("Enter 6-digit OTP"); return; }
    setFinalizing(true);
    try {
      await api.post("/payments/withdraw/finalize/", { transfer_code:transferCode, otp });
      setStep("done"); toast.success("Withdrawal complete!");
    } catch (err: unknown) {
      toast.error((err as {response?:{data?:{error?:{message?:string}}}})?.response?.data?.error?.message ?? "Invalid OTP");
    } finally { setFinalizing(false); }
  };

  const Card = ({ children }: {children:React.ReactNode}) => (
    <div className="rounded-2xl p-6 max-w-lg mx-auto"
      style={{ background:"rgba(255,255,255,0.04)", border:"1px solid rgba(255,255,255,0.08)", backdropFilter:"blur(20px)" }}>
      {children}
    </div>
  );

  const GradBtn = ({ onClick, disabled, loading:l, children }: {onClick:()=>void;disabled?:boolean;loading?:boolean;children:React.ReactNode}) => (
    <button onClick={onClick} disabled={disabled||l}
      className="w-full h-11 rounded-xl font-semibold text-white text-sm flex items-center justify-center gap-2 transition-all hover:opacity-90 disabled:opacity-40"
      style={{ background:"linear-gradient(90deg,#7c3aed,#db2777)" }}>
      {l&&<Loader2 className="h-4 w-4 animate-spin"/>}{children}
    </button>
  );

  return (
    <div className="p-4 lg:p-8 space-y-5 max-w-3xl mx-auto">
      <div className="flex items-center gap-3">
        <Link href="/dashboard" className="flex items-center gap-1.5 text-white/40 hover:text-white/70 text-sm transition-colors">
          <ArrowLeft className="h-4 w-4"/> Home
        </Link>
      </div>

      {step==="done" && (
        <Card>
          <div className="text-center py-6 space-y-4">
            <div className="h-16 w-16 rounded-full flex items-center justify-center mx-auto" style={{background:"rgba(5,150,105,0.15)"}}>
              <CheckCircle2 className="h-8 w-8 text-emerald-400"/>
            </div>
            <div>
              <p className="text-white font-bold text-xl">Withdrawal Complete!</p>
              {summary && <p className="text-white/40 text-sm mt-1">{formatNaira(summary.amount)} sent to {summary.recipient}</p>}
            </div>
            <div className="flex gap-3 justify-center">
              <button onClick={()=>router_go("/dashboard")} className="px-5 py-2.5 rounded-xl text-sm text-white/50 hover:text-white/70 transition-colors" style={{border:"1px solid rgba(255,255,255,0.1)"}}>Home</button>
              <button onClick={()=>{setStep("form");setAccountName("");setOtp("");}}
                className="px-5 py-2.5 rounded-xl text-sm font-semibold text-white" style={{background:"linear-gradient(90deg,#7c3aed,#db2777)"}}>New Withdrawal</button>
            </div>
          </div>
        </Card>
      )}

      {step==="otp" && (
        <Card>
          <h2 className="text-white font-bold text-xl mb-1">Confirm Transfer</h2>
          <p className="text-white/40 text-sm mb-5">Enter the 6-digit OTP Paystack sent to your email.</p>
          {summary && (
            <div className="p-4 rounded-xl mb-4" style={{background:"rgba(255,255,255,0.04)", border:"1px solid rgba(255,255,255,0.08)"}}>
              <p className="text-white/40 text-xs">Amount</p>
              <p className="text-white font-bold text-2xl">{formatNaira(summary.amount)}</p>
              <p className="text-white/40 text-xs mt-2">To: {summary.recipient}</p>
              <p className="text-white/25 text-xs font-mono mt-0.5">{transferCode}</p>
            </div>
          )}
          <div className="space-y-4">
            <div>
              <p className="text-white/50 text-xs mb-1.5">6-digit OTP</p>
              <input type="text" maxLength={6} placeholder="000000" value={otp}
                onChange={e=>setOtp(e.target.value.replace(/\D/g,"").slice(0,6))}
                className="w-full h-14 px-4 rounded-xl text-white text-3xl font-bold tracking-[0.5em] text-center placeholder-white/20 outline-none transition-all"
                style={{background:"rgba(255,255,255,0.05)",border:"1px solid rgba(255,255,255,0.08)"}}
                onFocus={e=>e.target.style.borderColor="#7c3aed"}
                onBlur={e=>e.target.style.borderColor="rgba(255,255,255,0.08)"} />
            </div>
            <GradBtn onClick={finalize} loading={finalizing} disabled={otp.length!==6}>Confirm Transfer</GradBtn>
          </div>
        </Card>
      )}

      {step==="form" && (
        <Card>
          <h2 className="text-white font-bold text-xl mb-1">Withdraw</h2>
          <p className="text-white/40 text-sm mb-5">Send to your bank account. KYC + PIN required.</p>
          <div className="space-y-4">
            <div>
              <p className="text-white/50 text-xs mb-1.5">Amount (₦)</p>
              <DarkInput placeholder="Minimum ₦100" value={amount} onChange={setAmount} type="number"/>
            </div>
            <div>
              <p className="text-white/50 text-xs mb-1.5">Bank</p>
              <select value={bankCode} onChange={e=>setBankCode(e.target.value)}
                className="w-full h-11 px-4 rounded-xl text-white/70 text-sm outline-none transition-all"
                style={{background:"rgba(255,255,255,0.05)",border:"1px solid rgba(255,255,255,0.08)"}}>
                <option value="" disabled style={{background:"#1a1a2e"}}>Select bank</option>
                {banks.map(b=><option key={b.code} value={b.code} style={{background:"#1a1a2e"}}>{b.name}</option>)}
              </select>
            </div>
            <div>
              <p className="text-white/50 text-xs mb-1.5">Account Number</p>
              <div className="flex gap-2">
                <div className="flex-1"><DarkInput placeholder="10-digit account" value={accountNumber} onChange={setAccountNumber}/></div>
                <button onClick={resolve} disabled={resolving||!bankCode||accountNumber.length<10}
                  className="h-11 px-4 rounded-xl text-white/70 text-xs font-semibold flex items-center gap-1.5 transition-all hover:text-white disabled:opacity-30"
                  style={{background:"rgba(255,255,255,0.07)",border:"1px solid rgba(255,255,255,0.1)"}}>
                  {resolving?<Loader2 className="h-4 w-4 animate-spin"/>:<Search className="h-4 w-4"/>} Verify
                </button>
              </div>
            </div>
            {accountName && (
              <div className="flex items-center gap-2.5 p-3 rounded-xl" style={{background:"rgba(5,150,105,0.1)",border:"1px solid rgba(5,150,105,0.2)"}}>
                <CheckCircle2 className="h-4 w-4 text-emerald-400 flex-shrink-0"/>
                <div>
                  <p className="text-emerald-400 text-xs font-medium">Verified</p>
                  <p className="text-emerald-300 text-sm font-bold">{accountName}</p>
                </div>
              </div>
            )}
            <div>
              <p className="text-white/50 text-xs mb-1.5">Transaction PIN</p>
              <DarkInput placeholder="••••" value={pin} onChange={setPin} type="password"/>
            </div>
            <GradBtn onClick={initWithdraw} loading={loading} disabled={!accountName}>Withdraw</GradBtn>
          </div>
        </Card>
      )}
    </div>
  );
}

function router_go(path: string) { window.location.href = path; }




