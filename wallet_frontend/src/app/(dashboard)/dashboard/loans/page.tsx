"use client";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { Loader2, Plus, X, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { formatNaira, formatDate } from "@/lib/utils";
import api from "@/lib/api";
import type { Loan } from "@/types";

const DarkInput = ({ placeholder, value, onChange, type="text" }: {
  placeholder:string; value?:string; onChange?:(v:string)=>void; type?:string;
}) => (
  <input type={type} placeholder={placeholder} value={value} onChange={e=>onChange?.(e.target.value)}
    className="w-full h-11 px-4 rounded-xl text-white/80 text-sm placeholder-white/20 outline-none transition-all"
    style={{background:"rgba(255,255,255,0.05)",border:"1px solid rgba(255,255,255,0.08)"}}
    onFocus={e=>e.target.style.borderColor="#7c3aed"}
    onBlur={e=>e.target.style.borderColor="rgba(255,255,255,0.08)"} />
);

export default function LoansPage() {
  const [loans, setLoans] = useState<Loan[]>([]);
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState(false);
  const [repaying, setRepaying] = useState<number|null>(null);
  const [showForm, setShowForm] = useState(false);
  const [repayAmounts, setRepayAmounts] = useState<Record<number,string>>({});

  const { register, handleSubmit, reset } = useForm({ defaultValues:{amount_requested:"",duration_months:"",pin:""} });

  const fetchLoans = () => { api.get("/loans/").then(r=>setLoans(r.data.loans??[])).finally(()=>setLoading(false)); };
  useEffect(()=>{ fetchLoans(); },[]);

  const onApply = async (data: Record<string,string>) => {
    setApplying(true);
    try { await api.post("/loans/apply/",data); toast.success("Application submitted!"); setShowForm(false); reset(); fetchLoans(); }
    catch (err: unknown) { toast.error((err as {response?:{data?:{error?:{message?:string}}}})?.response?.data?.error?.message??"Failed"); }
    finally { setApplying(false); }
  };

  const onRepay = async (id:number) => {
    setRepaying(id);
    try {
      const pin = prompt("Transaction PIN:");
      if (!pin) return;
      const amount = repayAmounts[id];
      await api.post(`/loans/${id}/repay/`,{pin,...(amount?{amount}:{})});
      toast.success("Repayment successful!"); fetchLoans();
    } catch (err: unknown) { toast.error((err as {response?:{data?:{error?:{message?:string}}}})?.response?.data?.error?.message??"Failed"); }
    finally { setRepaying(null); }
  };

  const statusColor = (s:string) => s==="ACTIVE"?"#fbbf24":s==="CLOSED"?"#34d399":"#f87171";

  return (
    <div className="p-4 lg:p-8 space-y-5 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <Link href="/dashboard" className="flex items-center gap-1.5 text-white/40 hover:text-white/70 text-sm transition-colors">
          <ArrowLeft className="h-4 w-4"/> Home
        </Link>
        <button onClick={()=>setShowForm(!showForm)}
          className="h-9 px-4 rounded-xl text-white text-sm font-semibold flex items-center gap-2"
          style={{background:"linear-gradient(90deg,#7c3aed,#db2777)"}}>
          <Plus className="h-4 w-4"/> Apply
        </button>
      </div>

      {/* Tier info */}
      <div className="rounded-2xl p-5" style={{background:"rgba(255,255,255,0.04)",border:"1px solid rgba(255,255,255,0.08)"}}>
        <h2 className="text-white font-bold mb-3">💼 Loans</h2>
        <div className="grid grid-cols-3 gap-3">
          {[
            {tier:"Tier 1",amount:"₦2,000",months:"1 month",color:"#fbbf24"},
            {tier:"Tier 2",amount:"₦10,000",months:"3 months",color:"#60a5fa"},
            {tier:"Tier 3",amount:"₦1,000,000",months:"60 months",color:"#a78bfa"},
          ].map(({tier,amount,months,color})=>(
            <div key={tier} className="rounded-xl p-3 text-center" style={{background:"rgba(255,255,255,0.04)"}}>
              <p className="text-xs font-bold" style={{color}}>{tier}</p>
              <p className="text-white font-bold text-sm mt-0.5">{amount}</p>
              <p className="text-white/30 text-xs">{months}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Apply form */}
      {showForm && (
        <div className="rounded-2xl p-5" style={{background:"rgba(255,255,255,0.04)",border:"1px solid rgba(255,255,255,0.08)"}}>
          <div className="flex items-center justify-between mb-4">
            <p className="text-white font-bold">New Application</p>
            <button onClick={()=>setShowForm(false)} className="text-white/30 hover:text-white/60"><X className="h-5 w-5"/></button>
          </div>
          <form onSubmit={handleSubmit(onApply)} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <p className="text-white/50 text-xs mb-1.5">Amount (₦)</p>
                <input type="number" placeholder="e.g. 5000"
                  className="w-full h-11 px-4 rounded-xl text-white/80 text-sm placeholder-white/20 outline-none"
                  style={{background:"rgba(255,255,255,0.05)",border:"1px solid rgba(255,255,255,0.08)"}}
                  {...register("amount_requested",{required:true})}/>
              </div>
              <div>
                <p className="text-white/50 text-xs mb-1.5">Duration (months)</p>
                <input type="number" min="1" placeholder="e.g. 3"
                  className="w-full h-11 px-4 rounded-xl text-white/80 text-sm placeholder-white/20 outline-none"
                  style={{background:"rgba(255,255,255,0.05)",border:"1px solid rgba(255,255,255,0.08)"}}
                  {...register("duration_months",{required:true})}/>
              </div>
            </div>
            <div>
              <p className="text-white/50 text-xs mb-1.5">Transaction PIN</p>
              <input type="password" maxLength={6} placeholder="••••••"
                className="w-full h-11 px-4 rounded-xl text-white/80 text-sm placeholder-white/20 outline-none"
                style={{background:"rgba(255,255,255,0.05)",border:"1px solid rgba(255,255,255,0.08)"}}
                {...register("pin",{required:true})}/>
            </div>
            <div className="flex gap-3">
              <button type="submit" disabled={applying}
                className="flex-1 h-11 rounded-xl text-white font-semibold text-sm flex items-center justify-center gap-2 hover:opacity-90 disabled:opacity-40"
                style={{background:"linear-gradient(90deg,#7c3aed,#db2777)"}}>
                {applying&&<Loader2 className="h-4 w-4 animate-spin"/>} Submit
              </button>
              <button type="button" onClick={()=>setShowForm(false)}
                className="h-11 px-5 rounded-xl text-white/50 text-sm"
                style={{border:"1px solid rgba(255,255,255,0.1)"}}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      {/* Loans list */}
      {loading ? (
        <div className="space-y-3 animate-pulse">
          {[...Array(2)].map((_,i)=><div key={i} className="h-44 rounded-2xl" style={{background:"rgba(255,255,255,0.04)"}}/>)}
        </div>
      ) : loans.length===0 ? (
        <div className="rounded-2xl p-12 text-center" style={{background:"rgba(255,255,255,0.04)",border:"1px solid rgba(255,255,255,0.08)"}}>
          <p className="text-4xl mb-3">💼</p>
          <p className="text-white/60 font-semibold">No loans yet</p>
          <p className="text-white/30 text-sm mt-1">Click Apply above to get started.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {loans.map(loan=>(
            <div key={loan.id} className="rounded-2xl overflow-hidden"
              style={{background:"rgba(255,255,255,0.04)",border:"1px solid rgba(255,255,255,0.08)"}}>
              <div className="flex items-center justify-between px-5 py-4 border-b" style={{borderColor:"rgba(255,255,255,0.06)"}}>
                <div>
                  <p className="text-white font-bold">Loan #{loan.user_loan_number}</p>
                  <p className="text-white/30 text-xs">{formatDate(loan.created_at)}</p>
                </div>
                <span className="text-xs font-semibold px-3 py-1 rounded-full"
                  style={{background:`${statusColor(loan.status)}20`, color:statusColor(loan.status)}}>
                  {loan.status}
                </span>
              </div>
              <div className="grid grid-cols-3 gap-px border-b" style={{borderColor:"rgba(255,255,255,0.06)",background:"rgba(255,255,255,0.04)"}}>
                {[
                  {label:"Approved",value:formatNaira(loan.amount_approved||loan.amount_requested)},
                  {label:"Monthly",value:formatNaira(loan.monthly_instalment)},
                  {label:"Outstanding",value:formatNaira(loan.outstanding_balance)},
                ].map(({label,value})=>(
                  <div key={label} className="px-4 py-3 text-center" style={{background:"rgba(0,0,0,0.1)"}}>
                    <p className="text-white/30 text-xs">{label}</p>
                    <p className="text-white font-bold text-sm mt-0.5">{value}</p>
                  </div>
                ))}
              </div>
              {loan.status==="ACTIVE" && (
                <div className="px-5 py-3 flex gap-2">
                  <input type="number" placeholder="Amount (blank = next instalment)"
                    className="flex-1 h-10 px-3 rounded-xl text-white/70 text-sm placeholder-white/20 outline-none"
                    style={{background:"rgba(255,255,255,0.05)",border:"1px solid rgba(255,255,255,0.08)"}}
                    value={repayAmounts[loan.id]??""} onChange={e=>setRepayAmounts(p=>({...p,[loan.id]:e.target.value}))}/>
                  <button onClick={()=>onRepay(loan.id)} disabled={repaying===loan.id}
                    className="h-10 px-4 rounded-xl text-white text-sm font-semibold flex items-center gap-1.5 hover:opacity-90 disabled:opacity-40"
                    style={{background:"linear-gradient(90deg,#7c3aed,#db2777)"}}>
                    {repaying===loan.id&&<Loader2 className="h-3 w-3 animate-spin"/>} Repay
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







