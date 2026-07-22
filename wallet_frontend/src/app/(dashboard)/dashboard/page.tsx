"use client";
import { useEffect, useState, useCallback } from "react";
import { formatNaira, formatDate } from "@/lib/utils";
import api from "@/lib/api";
import type { Wallet, Transaction, KYCStatus } from "@/types";

function useToast() {
  const [toast, setToast] = useState<{msg:string;ok:boolean}|null>(null);
  const show = (msg:string, ok=true) => { setToast({msg,ok}); setTimeout(()=>setToast(null),3200); };
  return { toast, show };
}

const ICONS: Record<string,string> = {
  FUND:"💰", WITHDRAWAL:"🏦", TRANSFER_IN:"⬇️", TRANSFER_OUT:"⬆️",
  LOAN_CREDIT:"💰", LOAN_DEBIT:"⬆️",
};

export default function DashboardPage() {
  const [wallet, setWallet] = useState<Wallet|null>(null);
  const [txns, setTxns] = useState<Transaction[]>([]);
  const [kyc, setKyc] = useState<KYCStatus|null>(null);
  const [loading, setLoading] = useState(true);
  const { toast, show } = useToast();

  // KYC
  const [bvn, setBvn] = useState(""); const [bvnLoading, setBvnLoading] = useState(false);
  // Fund
  const [fundAmt, setFundAmt] = useState(""); const [fundDesc, setFundDesc] = useState("Top up");
  const [fundLoading, setFundLoading] = useState(false);
  const [checkoutUrl, setCheckoutUrl] = useState<string|null>(null);
  const [fundRef, setFundRef] = useState<string|null>(null);
  // Transfer
  const [tAcct, setTAcct] = useState(""); const [tAmt, setTAmt] = useState("");
  const [tPin, setTPin] = useState(""); const [tDesc, setTDesc] = useState("");
  const [tLoading, setTLoading] = useState(false);

  const loadTxns = useCallback(async () => {
    try {
      const r = await api.get("/wallet/history/");
      setTxns(r.data.transactions ?? []);
    } catch {}
  }, []);

  const loadAll = useCallback(async () => {
    try {
      const [w,,k] = await Promise.all([api.get("/wallet/"), api.get("/wallet/history/"), api.get("/wallet/kyc/status/")]);
      setWallet(w.data);
      setKyc(k.data);
      await loadTxns();
    } finally { setLoading(false); }
  }, [loadTxns]);

  useEffect(() => { loadAll(); }, [loadAll]);

  const handleBvn = async () => {
    if (bvn.length!==11) { show("BVN must be 11 digits",false); return; }
    setBvnLoading(true);
    try { await api.post("/wallet/kyc/validate/",{bvn}); show("KYC verified! Wallet operations unlocked."); setBvn(""); loadAll(); }
    catch(e:unknown) { show((e as {response?:{data?:{error?:{message?:string}}}})?.response?.data?.error?.message??"Failed",false); }
    finally { setBvnLoading(false); }
  };

  const handleFund = async () => {
    if (Number(fundAmt)<100) { show("Minimum ₦100",false); return; }
    setFundLoading(true);
    try {
      const r = await api.post("/payments/fund/initialize/",{amount:fundAmt});
      setCheckoutUrl(r.data.checkout_url); setFundRef(r.data.reference);
      show("Initialized. Opening Paystack…");
      window.open(r.data.checkout_url,"_blank");
    } catch(e:unknown) { show((e as {response?:{data?:{error?:{message?:string}}}})?.response?.data?.error?.message??"Failed",false); }
    finally { setFundLoading(false); }
  };

  const handleVerify = async () => {
    if (!fundRef) return;
    setFundLoading(true);
    try {
      const r = await api.get(`/payments/callback?reference=${fundRef}`);
      if (r.data.success) { show("Wallet funded"); setCheckoutUrl(null); setFundRef(null); setFundAmt(""); loadAll(); }
    } catch { show("Not confirmed yet",false); }
    finally { setFundLoading(false); }
  };

  const handleTransfer = async () => {
    if (!tAcct||!tAmt||!tPin) { show("Fill all fields",false); return; }
    setTLoading(true);
    try {
      await api.post("/wallet/transfer/",{recipient_account_no:tAcct,amount:tAmt,pin:tPin,description:tDesc});
      show("Transfer successful"); setTAcct(""); setTAmt(""); setTPin(""); setTDesc(""); loadAll();
    } catch(e:unknown) { show((e as {response?:{data?:{error?:{message?:string}}}})?.response?.data?.error?.message??"Failed",false); }
    finally { setTLoading(false); }
  };

  const kycDone = kyc?.verifications?.bvn_validated;
  const isCredit = (t:string) => ["FUND","TRANSFER_IN","LOAN_CREDIT"].includes(t);

  const Input = ({placeholder,value,onChange,type="text"}:{placeholder:string;value:string;onChange:(v:string)=>void;type?:string}) => (
    <input type={type} className="fw-input" placeholder={placeholder} value={value} onChange={e=>onChange(e.target.value)}/>
  );

  if (loading) return (
    <div style={{padding:"34px 22px",maxWidth:1140,margin:"0 auto"}}>
      <div style={{height:200,borderRadius:20,background:"rgba(255,255,255,0.04)",marginBottom:20,animation:"pulse 2s infinite"}}/>
      <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(310px,1fr))",gap:20}}>
        {[...Array(3)].map((_,i)=><div key={i} style={{height:220,borderRadius:20,background:"rgba(255,255,255,0.04)"}}/>)}
      </div>
    </div>
  );

  return (
    <div style={{maxWidth:1140,margin:"0 auto",padding:"34px 22px 80px"}}>
      <div className="dash-grid">

        {/* ── Wallet card ── */}
        <div className="card wallet-card reveal">
          <div className="card-shine" aria-hidden="true"/>
          <div className="wallet-top">
            <div className="chip" aria-hidden="true"/>
            <span className={`pill ${kycDone?"pill-ok":"pill-warn"}`}>
              {kycDone ? "● KYC verified" : "● KYC pending"}
            </span>
          </div>
          <span className="wallet-label">Available balance</span>
          <div className="balance">{wallet ? formatNaira(wallet.balance) : "₦0.00"}</div>
          <div className="wallet-meta">
            <div><span className="muted">Account No</span><strong>{wallet?.account_no ?? "—"}</strong></div>
            <div><span className="muted">Daily debit limit</span><strong>{wallet ? formatNaira(wallet.debit_limit) : "—"}</strong></div>
            <div><span className="muted">Daily credit limit</span><strong>{wallet ? formatNaira(wallet.credit_limit) : "—"}</strong></div>
          </div>
          <div className="wallet-brand">VelaWallet</div>
        </div>

        {/* ── KYC card ── */}
        {!kycDone && (
          <div className="card glass reveal reveal-2">
            <h3><span className="ico">🪪</span> Complete KYC</h3>
            <p className="muted" style={{marginBottom:16}}>Verify your BVN to unlock funding, transfers and withdrawals.</p>
            <div className="fw-form">
              <label className="fw-label">BVN
                <Input placeholder="Enter your 11-digit BVN" value={bvn} onChange={setBvn}/>
              </label>
              <button className="btn btn-primary btn-glow" onClick={handleBvn} disabled={bvnLoading||bvn.length!==11}>
                {bvnLoading?"Verifying…":"Verify KYC"}
              </button>
            </div>
          </div>
        )}

        {/* ── Fund card ── */}
        <div className="card glass reveal reveal-2">
          <h3><span className="ico">💰</span> Fund wallet</h3>
          {checkoutUrl ? (
            <div className="fw-form">
              <p className="muted">Complete payment on Paystack then confirm below.</p>
              <button className="btn btn-ghost" onClick={()=>window.open(checkoutUrl,"_blank")}>Open Paystack ↗</button>
              <button className="btn btn-success btn-glow" onClick={handleVerify} disabled={fundLoading}>
                {fundLoading?"Verifying…":"I've Paid — Confirm"}
              </button>
              <button className="btn btn-ghost btn-sm" onClick={()=>{setCheckoutUrl(null);setFundRef(null);}}>Cancel</button>
            </div>
          ) : (
            <div className="fw-form">
              <label className="fw-label">Amount<Input placeholder="5000" value={fundAmt} onChange={setFundAmt} type="number"/></label>
              <label className="fw-label">Description<Input placeholder="Top up" value={fundDesc} onChange={setFundDesc}/></label>
              <button className="btn btn-success btn-glow" onClick={handleFund} disabled={fundLoading}>
                {fundLoading?"Initializing…":"Fund"}
              </button>
            </div>
          )}
        </div>

        {/* ── Transfer card ── */}
        <div className="card glass reveal reveal-3">
          <h3><span className="ico">🔁</span> Transfer</h3>
          <div className="fw-form">
            <label className="fw-label">Recipient account no<Input placeholder="10 digits" value={tAcct} onChange={setTAcct}/></label>
            <label className="fw-label">Amount<Input placeholder="1000" value={tAmt} onChange={setTAmt} type="number"/></label>
            <label className="fw-label">PIN<Input placeholder="••••" value={tPin} onChange={setTPin} type="password"/></label>
            <label className="fw-label">Description<Input placeholder="For lunch" value={tDesc} onChange={setTDesc}/></label>
            <button className="btn btn-primary btn-glow" onClick={handleTransfer} disabled={tLoading}>
              {tLoading?"Sending…":"Send"}
            </button>
          </div>
        </div>

        {/* ── More actions ── */}
        <div className="card glass reveal reveal-3">
          <h3><span className="ico">🧭</span> More</h3>
          <div style={{display:"flex",flexDirection:"column",gap:10,marginTop:8}}>
            {[
              {href:"/dashboard/withdraw",label:"🏦 Withdraw to bank"},
              {href:"/dashboard/loans",label:"💼 Loans"},
              {href:"/dashboard/kyc",label:"🛡️ KYC & Verification"},
              {href:"/dashboard/history",label:"🧾 Full history"},
            ].map(({href,label})=>(
              <a key={href} href={href}
                style={{padding:"12px 16px",borderRadius:12,background:"rgba(255,255,255,0.04)",border:"1px solid rgba(255,255,255,0.09)",color:"#eaf0ff",textDecoration:"none",fontSize:"0.92rem",fontWeight:600,transition:"all 0.18s ease",display:"block"}}
                onMouseOver={e=>{(e.currentTarget as HTMLAnchorElement).style.background="rgba(109,107,255,0.12)";(e.currentTarget as HTMLAnchorElement).style.borderColor="rgba(109,107,255,0.3)";}}
                onMouseOut={e=>{(e.currentTarget as HTMLAnchorElement).style.background="rgba(255,255,255,0.04)";(e.currentTarget as HTMLAnchorElement).style.borderColor="rgba(255,255,255,0.09)";}}>
                {label}
              </a>
            ))}
          </div>
        </div>

        {/* ── Transactions ── */}
        <div className="card glass transactions-card reveal reveal-4">
          <div className="tx-head">
            <h3><span className="ico">🧾</span> Transactions</h3>
            <button className="btn btn-ghost btn-sm" onClick={loadTxns}>⟳ Refresh</button>
          </div>
          <div className="tx-list">
            {txns.length === 0
              ? <p className="muted">No transactions yet.</p>
              : txns.map((t,i) => {
                  const credit = isCredit(t.type);
                  return (
                    <div className="tx-item" key={t.reference} style={{animationDelay:`${i*0.04}s`}}>
                      <div className="tx-left">
                        <span className={`tx-icon ${credit?"credit":"debit"}`}>{ICONS[t.type]||(credit?"⬇️":"⬆️")}</span>
                        <span>
                          <div className="tx-type">{t.type.replace(/_/g," ")}</div>
                          <div className="tx-desc">{t.description||"—"} · {formatDate(t.date)}</div>
                        </span>
                      </div>
                      <span className={`tx-amt ${credit?"credit":"debit"}`}>
                        {credit?"+":"-"}{formatNaira(t.amount)}
                      </span>
                    </div>
                  );
                })
            }
          </div>
        </div>
      </div>

      {/* Toast */}
      {toast && <div className={`fw-toast ${toast.ok?"ok":"err"}`}>{toast.ok?"✅":"⚠️"} {toast.msg}</div>}
    </div>
  );
}






