"use client";
import { useState, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuthStore } from "@/store/auth";
import api from "@/lib/api";
import { getErrorMessage } from "@/lib/utils";

const loginSchema = z.object({ email: z.string().email(), password: z.string().min(1) });
const registerSchema = z.object({
  full_name: z.string().min(2), email: z.string().email(),
  password: z.string().min(8), bvn: z.string().length(11), pin: z.string().min(4).max(6),
});
type LoginData = z.infer<typeof loginSchema>;
type RegisterData = z.infer<typeof registerSchema>;

function useToast() {
  const [toast, setToast] = useState<{msg:string;ok:boolean}|null>(null);
  const show = (msg:string, ok=true) => {
    setToast({msg,ok});
    setTimeout(()=>setToast(null), 3200);
  };
  return { toast, show };
}

export default function AuthPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const login = useAuthStore((s) => s.login);
  const [tab, setTab] = useState<"login"|"register">(
    searchParams.get("tab") === "register" ? "register" : "login"
  );
  const [loading, setLoading] = useState(false);
  const [devToken, setDevToken] = useState<string|null>(null);
  const { toast, show } = useToast();

  const lf = useForm<LoginData>({ resolver: zodResolver(loginSchema) });
  const rf = useForm<RegisterData>({ resolver: zodResolver(registerSchema) });

  const onLogin = async (data: LoginData) => {
    setLoading(true);
    try {
      const res = await api.post("/auth/login/", data);
      login(res.data.access, res.data.refresh, data.email);
      show("Welcome back!");
      router.push("/dashboard");
    } catch(err) { show(getErrorMessage(err), false); }
    finally { setLoading(false); }
  };

  const onRegister = async (data: RegisterData) => {
    setLoading(true);
    try {
      const res = await api.post("/auth/register/", data);
      setDevToken(res.data.dev_otp ?? res.data.dev_email_verification_token);
      show("Account created! Check your email.");
      setTimeout(() => { setTab("login"); setDevToken(null); }, 4000);
    } catch(err) { show(getErrorMessage(err), false); }
    finally { setLoading(false); }
  };

  return (
    <div style={{position:"relative",minHeight:"100vh"}}>
      {/* Aurora background */}
      <div className="aurora" aria-hidden="true">
        <span className="orb orb-1"/><span className="orb orb-2"/>
        <span className="orb orb-3"/><span className="orb orb-4"/>
        <div className="grid-overlay"/>
      </div>

      {/* Top bar */}
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">◆</span>
          <span className="brand-text">VelaWallet</span>
        </div>
      </header>

      <main className="container">
        <section className="auth-wrap">
          {/* Hero */}
          <div className="auth-hero reveal">
            <div className="hero-pill">⚡ Secure · KYC-compliant · AES-256</div>
            <h1 className="hero-title">
              Banking that feels<br/>
              <span className="grad-text">effortless &amp; epic.</span>
            </h1>
            <p className="hero-sub">
              Move money in seconds. Fund your wallet, send to anyone, and withdraw to
              your bank — all wrapped in bank-grade encryption.
            </p>
            <ul className="hero-feats">
              <li><span className="feat-ico">🔐</span> AES-256 encrypted, KYC-verified accounts</li>
              <li><span className="feat-ico">⚡</span> Instant intra-wallet transfers</li>
              <li><span className="feat-ico">🛡️</span> PIN-protected debits &amp; smart limits</li>
            </ul>
          </div>

          {/* Auth card */}
          <div className="card auth-card reveal reveal-2">
            {/* Tabs */}
            <div className="tabs">
              <button className={`tab${tab==="login"?" active":""}`} onClick={()=>setTab("login")}>Login</button>
              <button className={`tab${tab==="register"?" active":""}`} onClick={()=>setTab("register")}>Register</button>
              <span className="tab-glow" style={{left: tab==="login" ? "6px" : "50%"}}/>
            </div>

            {/* Dev token */}
            {devToken && (
              <div style={{marginBottom:16,padding:"12px 16px",borderRadius:12,background:"rgba(245,158,11,0.1)",border:"1px solid rgba(245,158,11,0.25)"}}>
                <p style={{color:"#fbbf24",fontSize:"0.75rem",fontWeight:700,margin:"0 0 4px"}}>Dev Email OTP</p>
                <p style={{color:"#fde68a",fontSize:"1.6rem",fontWeight:800,letterSpacing:"0.3em",margin:0}}>{devToken}</p>
              </div>
            )}

            {/* Login form */}
            {tab === "login" && (
              <form className="fw-form" onSubmit={lf.handleSubmit(onLogin)}>
                <h2>Welcome back 👋</h2>
                <label className="fw-label">Email
                  <input type="email" className="fw-input" placeholder="you@example.com" {...lf.register("email")}/>
                  {lf.formState.errors.email && <span style={{color:"#ff8794",fontSize:"0.75rem"}}>{lf.formState.errors.email.message}</span>}
                </label>
                <label className="fw-label">Password
                  <input type="password" className="fw-input" placeholder="••••••••" {...lf.register("password")}/>
                </label>
                <button type="submit" className="btn btn-primary btn-glow" disabled={loading}>
                  {loading ? "Logging in…" : "Login →"}
                </button>
              </form>
            )}

            {/* Register form */}
            {tab === "register" && (
              <form className="fw-form" onSubmit={rf.handleSubmit(onRegister)}>
                <h2>Create your wallet ✨</h2>
                <label className="fw-label">Full name
                  <input className="fw-input" placeholder="Ada Lovelace" {...rf.register("full_name")}/>
                </label>
                <label className="fw-label">Email
                  <input type="email" className="fw-input" placeholder="you@example.com" {...rf.register("email")}/>
                </label>
                <label className="fw-label">Password
                  <input type="password" className="fw-input" placeholder="Min 8 chars" {...rf.register("password")}/>
                </label>
                <div className="row-2">
                  <label className="fw-label">BVN (11 digits)
                    <input className="fw-input" placeholder="22200011122" {...rf.register("bvn")}/>
                  </label>
                  <label className="fw-label">PIN (4–6 digits)
                    <input type="password" className="fw-input" placeholder="1234" {...rf.register("pin")}/>
                  </label>
                </div>
                <button type="submit" className="btn btn-primary btn-glow" disabled={loading}>
                  {loading ? "Creating…" : "Create account →"}
                </button>
              </form>
            )}
          </div>
        </section>
      </main>

      {/* Toast */}
      {toast && (
        <div className={`fw-toast ${toast.ok?"ok":"err"}`}>
          {toast.ok ? "✅" : "⚠️"} {toast.msg}
        </div>
      )}

      <style>{`.container{max-width:1140px;margin:0 auto;padding:34px 22px 80px}`}</style>
    </div>
  );
}





