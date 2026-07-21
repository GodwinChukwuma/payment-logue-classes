"use client";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Loader2, CheckCircle2, Mail, Phone, ShieldCheck, Fingerprint } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { formatNaira } from "@/lib/utils";
import api from "@/lib/api";
import type { KYCStatus } from "@/types";

export default function KYCPage() {
  const [kyc, setKyc] = useState<KYCStatus|null>(null);
  const [loading, setLoading] = useState(true);
  const [emailOtp, setEmailOtp] = useState("");
  const [phoneOtp, setPhoneOtp] = useState("");
  const [phone, setPhone] = useState("");
  const [bvn, setBvn] = useState("");
  const [submitting, setSubmitting] = useState<string|null>(null);
  const [devOtp, setDevOtp] = useState<{email?:string;phone?:string}>({});

  const fetchKyc = () => api.get("/wallet/kyc/status/").then((r) => setKyc(r.data)).finally(() => setLoading(false));
  useEffect(() => { fetchKyc(); }, []);

  const action = async (key: string, fn: () => Promise<void>) => {
    setSubmitting(key);
    try { await fn(); fetchKyc(); }
    catch (err: unknown) {
      toast.error((err as {response?:{data?:{error?:{message?:string}}}})?.response?.data?.error?.message ?? "Failed");
    } finally { setSubmitting(null); }
  };

  if (loading) return (
    <div className="space-y-3 animate-pulse">
      <div className="h-32 rounded-2xl bg-blue-200/60" />
      {[...Array(4)].map((_,i) => <div key={i} className="h-24 bg-white rounded-2xl" />)}
    </div>
  );

  const v = kyc?.verifications;

  // Verification steps matching the calculator-list style from reference
  const steps = [
    {
      key: "email", label: "Email Verification", icon: Mail,
      done: v?.email_verified, bg: "icon-blue", color: "text-blue-600",
      content: !v?.email_verified && (
        <div className="space-y-2.5">
          <button disabled={submitting==="email-send"}
            onClick={() => action("email-send", async () => {
              const r = await api.post("/wallet/verify/email/send/");
              setDevOtp(p => ({...p, email: r.data.dev_otp}));
              toast.success("OTP sent");
            })}
            className="h-9 px-5 rounded-xl bg-primary text-white text-xs font-semibold flex items-center gap-1.5 hover:bg-primary/90 transition-all disabled:opacity-60">
            {submitting==="email-send"&&<Loader2 className="h-3 w-3 animate-spin"/>} Send OTP
          </button>
          {devOtp.email && (
            <div className="p-2.5 bg-amber-50 rounded-xl border border-amber-100">
              <p className="text-xs text-amber-600">Dev OTP: <strong className="tracking-widest">{devOtp.email}</strong></p>
            </div>
          )}
          <div className="flex gap-2">
            <input placeholder="6-digit OTP" maxLength={6} value={emailOtp}
              onChange={e=>setEmailOtp(e.target.value.replace(/\D/g,"").slice(0,6))}
              className="flex-1 h-10 px-3 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30" />
            <button disabled={emailOtp.length!==6||submitting==="email-confirm"}
              onClick={()=>action("email-confirm",async()=>{
                await api.post("/wallet/verify/email/confirm/",{token:emailOtp});
                toast.success("Email verified!"); setEmailOtp("");
              })}
              className="h-10 px-4 rounded-xl bg-primary text-white text-xs font-semibold flex items-center gap-1 hover:bg-primary/90 transition-all disabled:opacity-60">
              {submitting==="email-confirm"&&<Loader2 className="h-3 w-3 animate-spin"/>} Confirm
            </button>
          </div>
        </div>
      ),
    },
    {
      key: "phone", label: "Phone Verification", icon: Phone,
      done: v?.phone_verified, bg: "icon-pink", color: "text-pink-500",
      content: !v?.phone_verified && (
        <div className="space-y-2.5">
          <div className="flex gap-2">
            <input placeholder="+2348012345678" value={phone} onChange={e=>setPhone(e.target.value)}
              className="flex-1 h-10 px-3 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30" />
            <button disabled={!phone||submitting==="phone-send"}
              onClick={()=>action("phone-send",async()=>{
                const r=await api.post("/wallet/verify/phone/send/",{phone_number:phone});
                setDevOtp(p=>({...p,phone:r.data.dev_otp})); toast.success("OTP sent");
              })}
              className="h-10 px-4 rounded-xl bg-primary text-white text-xs font-semibold flex items-center gap-1 hover:bg-primary/90 transition-all disabled:opacity-60">
              {submitting==="phone-send"&&<Loader2 className="h-3 w-3 animate-spin"/>} Send
            </button>
          </div>
          {devOtp.phone&&(
            <div className="p-2.5 bg-amber-50 rounded-xl border border-amber-100">
              <p className="text-xs text-amber-600">Dev OTP: <strong className="tracking-widest">{devOtp.phone}</strong></p>
            </div>
          )}
          <div className="flex gap-2">
            <input placeholder="6-digit OTP" maxLength={6} value={phoneOtp}
              onChange={e=>setPhoneOtp(e.target.value.replace(/\D/g,"").slice(0,6))}
              className="flex-1 h-10 px-3 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30" />
            <button disabled={phoneOtp.length!==6||submitting==="phone-confirm"}
              onClick={()=>action("phone-confirm",async()=>{
                await api.post("/wallet/verify/phone/confirm/",{code:phoneOtp});
                toast.success("Phone verified!"); setPhoneOtp("");
              })}
              className="h-10 px-4 rounded-xl bg-primary text-white text-xs font-semibold flex items-center gap-1 hover:bg-primary/90 transition-all disabled:opacity-60">
              {submitting==="phone-confirm"&&<Loader2 className="h-3 w-3 animate-spin"/>} Confirm
            </button>
          </div>
        </div>
      ),
    },
    {
      key: "bvn", label: "BVN Validation", icon: ShieldCheck,
      done: v?.bvn_validated, bg: "icon-teal", color: "text-teal-600",
      content: !v?.bvn_validated && (
        <div className="flex gap-2">
          <input placeholder="11-digit BVN" maxLength={11} value={bvn}
            onChange={e=>setBvn(e.target.value.replace(/\D/g,"").slice(0,11))}
            className="flex-1 h-10 px-3 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30" />
          <button disabled={bvn.length!==11||submitting==="bvn"}
            onClick={()=>action("bvn",async()=>{
              await api.post("/wallet/kyc/validate/",{bvn});
              toast.success("BVN validated!"); setBvn("");
            })}
            className="h-10 px-4 rounded-xl bg-primary text-white text-xs font-semibold flex items-center gap-1 hover:bg-primary/90 transition-all disabled:opacity-60">
            {submitting==="bvn"&&<Loader2 className="h-3 w-3 animate-spin"/>} Validate
          </button>
        </div>
      ),
    },
    {
      key: "face", label: "Face ID Verification", icon: Fingerprint,
      done: v?.face_id_verified, bg: "icon-yellow", color: "text-amber-500",
      content: !v?.face_id_verified && v?.bvn_validated && (
        <button disabled={submitting==="face"}
          onClick={()=>action("face",async()=>{
            await api.post("/wallet/verify/face/",{face_verified:true});
            toast.success("Face ID verified! You are now Tier 3.");
          })}
          className="h-10 px-5 rounded-xl bg-primary text-white text-xs font-semibold flex items-center gap-1.5 hover:bg-primary/90 transition-all disabled:opacity-60">
          {submitting==="face"&&<Loader2 className="h-3 w-3 animate-spin"/>} Simulate Face Scan
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-4 pb-8">
      <div className="px-1">
        <h1 className="text-xl font-bold">KYC & Verification</h1>
        <p className="text-muted-foreground text-sm">Complete steps to unlock higher limits</p>
      </div>

      {/* Current tier hero */}
      {kyc && (
        <div className="hero-gradient rounded-2xl p-6 text-white relative overflow-hidden">
          <div className="absolute -right-8 -top-8 h-32 w-32 rounded-full bg-white/10" />
          <div className="flex items-start justify-between">
            <div>
              <p className="text-white/70 text-xs font-medium uppercase tracking-wide">Current Tier</p>
              <p className="text-2xl font-bold mt-0.5">{kyc.tier_label}</p>
              <p className="text-white/60 text-sm mt-1">{kyc.next_tier_requires}</p>
            </div>
            <div className="text-right">
              <p className="text-white/70 text-xs">Wallet Limit</p>
              <p className="text-lg font-bold">{formatNaira(kyc.wallet_credit_limit)}</p>
              <p className="text-white/50 text-xs mt-0.5">
                Loan: {formatNaira(kyc.loan_limits.max_amount)}
              </p>
            </div>
          </div>

          {/* Tier progress dots */}
          <div className="flex items-center gap-3 mt-4">
            {[1,2,3].map((t) => (
              <div key={t} className={`flex items-center gap-1.5 ${kyc.kyc_tier>=t?"text-white":"text-white/30"}`}>
                <div className={`h-2 w-2 rounded-full ${kyc.kyc_tier>=t?"bg-white":"bg-white/30"}`} />
                <span className="text-xs">T{t}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Verification steps — list style from reference */}
      <div className="bg-white rounded-2xl card-shadow overflow-hidden">
        {steps.map((step, i) => (
          <div key={step.key} className={`px-5 py-4 ${i < steps.length-1 ? "border-b border-border/60" : ""}`}>
            <div className="flex items-center gap-4 mb-3">
              <div className={`h-11 w-11 rounded-xl flex items-center justify-center flex-shrink-0 ${step.bg}`}>
                <step.icon className={`h-5 w-5 ${step.color}`} />
              </div>
              <div className="flex-1">
                <p className="text-sm font-semibold text-foreground">{step.label}</p>
              </div>
              {step.done
                ? <Badge variant="success" className="flex items-center gap-1">
                    <CheckCircle2 className="h-3 w-3" /> Verified
                  </Badge>
                : <Badge variant="warning">Pending</Badge>
              }
            </div>
            {step.content && <div className="ml-15 pl-[60px]">{step.content}</div>}
          </div>
        ))}
      </div>
    </div>
  );
}

