"use client";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Loader2, CheckCircle2, ArrowLeft } from "lucide-react";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import Link from "next/link";
import { formatNaira } from "@/lib/utils";
import api from "@/lib/api";
import type { KYCStatus } from "@/types";

const DarkInput = ({ placeholder, value, onChange, type="text" }: {
  placeholder:string;value?:string;onChange?:(v:string)=>void;type?:string;
}) => (
  <input type={type} placeholder={placeholder} value={value} onChange={e=>onChange?.(e.target.value)}
    className="w-full h-11 px-4 rounded-xl text-white/80 text-sm placeholder-white/20 outline-none transition-all"
    style={{background:"rgba(255,255,255,0.05)",border:"1px solid rgba(255,255,255,0.08)"}}
    onFocus={e=>e.target.style.borderColor="#7c3aed"}
    onBlur={e=>e.target.style.borderColor="rgba(255,255,255,0.08)"} />
);

const GlassCard = ({ children }: {children:React.ReactNode}) => (
  <div className="rounded-2xl p-5" style={{background:"rgba(255,255,255,0.04)",border:"1px solid rgba(255,255,255,0.08)",backdropFilter:"blur(20px)"}}>
    {children}
  </div>
);

export default function KYCPage() {
  const [kyc, setKyc] = useState<KYCStatus|null>(null);
  const [loading, setLoading] = useState(true);
  const [emailOtp, setEmailOtp] = useState("");
  const [phoneOtp, setPhoneOtp] = useState("");
  const [phone, setPhone] = useState("");
  const [bvn, setBvn] = useState("");
  const [faceToggle, setFaceToggle] = useState(false);
  const [submitting, setSubmitting] = useState<string|null>(null);
  const [devOtp, setDevOtp] = useState<{email?:string;phone?:string}>({});

  const fetchKyc = () => { setLoading(true); api.get("/wallet/kyc/status/").then(r=>setKyc(r.data)).finally(()=>setLoading(false)); };
  useEffect(()=>{ fetchKyc(); },[]);

  const action = async (key:string, fn:()=>Promise<void>) => {
    setSubmitting(key);
    try { await fn(); fetchKyc(); }
    catch (err:unknown) { toast.error((err as {response?:{data?:{error?:{message?:string}}}})?.response?.data?.error?.message??"Failed"); }
    finally { setSubmitting(null); }
  };

  if (loading) return <div className="p-8 space-y-4 animate-pulse">{[...Array(4)].map((_,i)=><div key={i} className="h-28 rounded-2xl" style={{background:"rgba(255,255,255,0.04)"}}/>)}</div>;

  const v = kyc?.verifications;
  const VerBadge = ({ done }: {done?:boolean}) => (
    <span className="text-xs font-semibold px-2.5 py-1 rounded-full"
      style={{background:done?"rgba(5,150,105,0.2)":"rgba(245,158,11,0.15)",color:done?"#34d399":"#fbbf24"}}>
      {done?"✓ Verified":"Pending"}
    </span>
  );
  const GradBtn = ({ onClick, disabled, loading:l, children }: {onClick:()=>void;disabled?:boolean;loading?:boolean;children:React.ReactNode}) => (
    <button onClick={onClick} disabled={disabled||l}
      className="h-10 px-5 rounded-xl text-white text-sm font-semibold flex items-center gap-2 hover:opacity-90 disabled:opacity-40 transition-all"
      style={{background:"linear-gradient(90deg,#7c3aed,#db2777)"}}>
      {l&&<Loader2 className="h-3.5 w-3.5 animate-spin"/>}{children}
    </button>
  );

  return (
    <div className="p-4 lg:p-8 space-y-5 max-w-3xl mx-auto">
      <div className="flex items-center gap-3">
        <Link href="/dashboard" className="flex items-center gap-1.5 text-white/40 hover:text-white/70 text-sm transition-colors">
          <ArrowLeft className="h-4 w-4"/> Home
        </Link>
      </div>

      {/* Tier hero */}
      {kyc && (
        <div className="rounded-2xl p-6 relative overflow-hidden"
          style={{background:"linear-gradient(135deg,rgba(80,30,160,0.6),rgba(20,40,120,0.5))",border:"1px solid rgba(255,255,255,0.1)"}}>
          <div className="absolute -right-8 -top-8 w-40 h-40 rounded-full blur-2xl opacity-30" style={{background:"radial-gradient(circle,#db2777,transparent)"}}/>
          <div className="relative z-10 flex items-start justify-between">
            <div>
              <p className="text-white/40 text-xs uppercase tracking-widest">Current Tier</p>
              <p className="text-2xl font-black text-white mt-1">{kyc.tier_label}</p>
              <p className="text-white/40 text-sm mt-1">{kyc.next_tier_requires}</p>
            </div>
            <div className="text-right">
              <p className="text-white/40 text-xs">Wallet Limit</p>
              <p className="text-xl font-bold text-white">{formatNaira(kyc.wallet_credit_limit)}</p>
              <p className="text-white/30 text-xs mt-0.5">Loan max: {formatNaira(kyc.loan_limits.max_amount)}</p>
            </div>
          </div>
          <div className="relative z-10 flex items-center gap-2 mt-4">
            {[1,2,3].map(t=>(
              <div key={t} className="flex items-center gap-1.5">
                <div className={`h-2.5 w-2.5 rounded-full ${(kyc.kyc_tier??0)>=t?"bg-purple-400":"bg-white/15"}`}/>
                <span className={`text-xs ${(kyc.kyc_tier??0)>=t?"text-purple-300":"text-white/25"}`}>T{t}</span>
                {t<3&&<div className={`h-px w-6 ${(kyc.kyc_tier??0)>t?"bg-purple-400":"bg-white/15"}`}/>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Steps */}
      {[
        {
          key:"email", emoji:"📧", label:"Email Verification", done:v?.email_verified,
          content: !v?.email_verified && (
            <div className="space-y-3 mt-3">
              <GradBtn onClick={()=>action("email-send",async()=>{const r=await api.post("/wallet/verify/email/send/");setDevOtp(p=>({...p,email:r.data.dev_otp}));toast.success("OTP sent");})} loading={submitting==="email-send"}>Send OTP</GradBtn>
              {devOtp.email&&<div className="p-3 rounded-xl" style={{background:"rgba(245,158,11,0.1)",border:"1px solid rgba(245,158,11,0.2)"}}><p className="text-amber-400 text-xs">Dev OTP</p><p className="text-amber-300 text-2xl font-bold tracking-[0.3em]">{devOtp.email}</p></div>}
              <div className="flex gap-2">
                <input placeholder="6-digit OTP" maxLength={6} value={emailOtp} onChange={e=>setEmailOtp(e.target.value.replace(/\D/g,"").slice(0,6))}
                  className="flex-1 h-11 px-4 rounded-xl text-white text-center text-xl font-bold tracking-widest placeholder-white/20 outline-none"
                  style={{background:"rgba(255,255,255,0.05)",border:"1px solid rgba(255,255,255,0.08)"}}/>
                <GradBtn onClick={()=>action("email-confirm",async()=>{await api.post("/wallet/verify/email/confirm/",{token:emailOtp});toast.success("Email verified!");setEmailOtp("");})} disabled={emailOtp.length!==6} loading={submitting==="email-confirm"}>Confirm</GradBtn>
              </div>
            </div>
          )
        },
        {
          key:"phone", emoji:"📱", label:"Phone Verification", done:v?.phone_verified,
          content: !v?.phone_verified && (
            <div className="space-y-3 mt-3">
              <div className="flex gap-2">
                <div className="flex-1"><DarkInput placeholder="+2348012345678" value={phone} onChange={setPhone}/></div>
                <GradBtn onClick={()=>action("phone-send",async()=>{const r=await api.post("/wallet/verify/phone/send/",{phone_number:phone});setDevOtp(p=>({...p,phone:r.data.dev_otp}));toast.success("OTP sent");})} disabled={!phone} loading={submitting==="phone-send"}>Send</GradBtn>
              </div>
              {devOtp.phone&&<div className="p-3 rounded-xl" style={{background:"rgba(245,158,11,0.1)",border:"1px solid rgba(245,158,11,0.2)"}}><p className="text-amber-400 text-xs">Dev OTP</p><p className="text-amber-300 text-2xl font-bold tracking-[0.3em]">{devOtp.phone}</p></div>}
              <div className="flex gap-2">
                <input placeholder="6-digit OTP" maxLength={6} value={phoneOtp} onChange={e=>setPhoneOtp(e.target.value.replace(/\D/g,"").slice(0,6))}
                  className="flex-1 h-11 px-4 rounded-xl text-white text-center text-xl font-bold tracking-widest placeholder-white/20 outline-none"
                  style={{background:"rgba(255,255,255,0.05)",border:"1px solid rgba(255,255,255,0.08)"}}/>
                <GradBtn onClick={()=>action("phone-confirm",async()=>{await api.post("/wallet/verify/phone/confirm/",{code:phoneOtp});toast.success("Phone verified!");setPhoneOtp("");})} disabled={phoneOtp.length!==6} loading={submitting==="phone-confirm"}>Confirm</GradBtn>
              </div>
            </div>
          )
        },
        {
          key:"bvn", emoji:"🛡️", label:"BVN Validation", done:v?.bvn_validated,
          content: !v?.bvn_validated && (
            <div className="flex gap-2 mt-3">
              <div className="flex-1"><DarkInput placeholder="11-digit BVN" value={bvn} onChange={v=>{if(/^\d*$/.test(v)&&v.length<=11)setBvn(v);}}/></div>
              <GradBtn onClick={()=>action("bvn",async()=>{await api.post("/wallet/kyc/validate/",{bvn});toast.success("BVN validated!");setBvn("");})} disabled={bvn.length!==11} loading={submitting==="bvn"}>Validate</GradBtn>
            </div>
          )
        },
        {
          key:"face", emoji:"🪪", label:"Face ID Verification", done:v?.face_id_verified,
          content: !v?.face_id_verified && (
            <div className="space-y-4 mt-3">
              {!v?.bvn_validated
                ? <p className="text-white/30 text-sm">Validate BVN above first to unlock Face ID.</p>
                : <>
                    <div className="flex items-center justify-between p-4 rounded-xl" style={{background:"rgba(255,255,255,0.04)",border:"1px solid rgba(255,255,255,0.08)"}}>
                      <div>
                        <Label htmlFor="face-toggle" className="text-white/70 text-sm font-semibold cursor-pointer">Enable Face Verification</Label>
                        <p className="text-white/30 text-xs mt-0.5">Toggle on to simulate a face scan</p>
                      </div>
                      <Switch id="face-toggle" checked={faceToggle} onCheckedChange={setFaceToggle}/>
                    </div>
                    <GradBtn onClick={()=>action("face",async()=>{await api.post("/wallet/verify/face/",{face_verified:true});toast.success("Face ID verified! Tier 3 unlocked!");})} disabled={!faceToggle} loading={submitting==="face"}>
                      Confirm Face ID Scan
                    </GradBtn>
                  </>}
            </div>
          )
        }
      ].map(step=>(
        <GlassCard key={step.key}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-2xl">{step.emoji}</span>
              <p className="text-white font-semibold">{step.label}</p>
            </div>
            <VerBadge done={step.done}/>
          </div>
          {step.content}
          {step.done && (
            <div className="flex items-center gap-2 mt-3">
              <CheckCircle2 className="h-4 w-4 text-emerald-400"/>
              <p className="text-emerald-400 text-sm">Completed</p>
            </div>
          )}
        </GlassCard>
      ))}
    </div>
  );
}




