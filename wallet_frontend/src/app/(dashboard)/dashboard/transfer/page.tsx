"use client";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { Loader2, CheckCircle2, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { formatNaira } from "@/lib/utils";
import api from "@/lib/api";

const DarkInput = ({ placeholder, type="text", ...props }: React.InputHTMLAttributes<HTMLInputElement>) => (
  <input type={type} placeholder={placeholder}
    className="w-full h-11 px-4 rounded-xl text-white/80 text-sm placeholder-white/20 outline-none transition-all"
    style={{background:"rgba(255,255,255,0.05)",border:"1px solid rgba(255,255,255,0.08)"}}
    onFocus={e=>e.target.style.borderColor="#7c3aed"} onBlur={e=>e.target.style.borderColor="rgba(255,255,255,0.08)"}
    {...props} />
);

export default function TransferPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{amount:string;new_balance:string;recipient_account:string}|null>(null);
  const { register, handleSubmit, reset } = useForm({ defaultValues:{recipient_account_no:"",amount:"",pin:"",description:""} });

  const onSubmit = async (data:Record<string,string>) => {
    setLoading(true);
    try { const r = await api.post("/wallet/transfer/",data); setResult(r.data); toast.success("Transfer successful!"); }
    catch (err:unknown) { toast.error((err as {response?:{data?:{error?:{message?:string}}}})?.response?.data?.error?.message??"Failed"); }
    finally { setLoading(false); }
  };

  return (
    <div className="p-4 lg:p-8 space-y-5 max-w-2xl mx-auto">
      <Link href="/dashboard" className="flex items-center gap-1.5 text-white/40 hover:text-white/70 text-sm transition-colors">
        <ArrowLeft className="h-4 w-4"/> Home
      </Link>

      <div className="rounded-2xl p-6" style={{background:"rgba(255,255,255,0.04)",border:"1px solid rgba(255,255,255,0.08)",backdropFilter:"blur(20px)"}}>
        {result ? (
          <div className="text-center py-6 space-y-4">
            <div className="h-16 w-16 rounded-full flex items-center justify-center mx-auto" style={{background:"rgba(5,150,105,0.15)"}}>
              <CheckCircle2 className="h-8 w-8 text-emerald-400"/>
            </div>
            <div>
              <p className="text-white font-bold text-xl">Transfer Successful!</p>
              <p className="text-white/40 text-sm mt-1">{formatNaira(result.amount)} sent to {result.recipient_account}</p>
              <p className="text-purple-400 text-sm mt-0.5">New balance: {formatNaira(result.new_balance)}</p>
            </div>
            <div className="flex gap-3 justify-center">
              <Link href="/dashboard" className="px-5 py-2.5 rounded-xl text-sm text-white/50" style={{border:"1px solid rgba(255,255,255,0.1)"}}>Home</Link>
              <button onClick={()=>{setResult(null);reset();}} className="px-5 py-2.5 rounded-xl text-sm font-semibold text-white" style={{background:"linear-gradient(90deg,#4361EE,#7c3aed)"}}>New Transfer</button>
            </div>
          </div>
        ) : (
          <>
            <p className="text-white font-bold text-xl mb-1">💸 Transfer</p>
            <p className="text-white/40 text-sm mb-5">Send to another VelaWallet account instantly.</p>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              {[
                {id:"recipient_account_no",label:"Recipient Account No",placeholder:"10-digit wallet number",type:"text"},
                {id:"amount",label:"Amount (₦)",placeholder:"1000",type:"number"},
                {id:"description",label:"Description (optional)",placeholder:"For lunch",type:"text"},
                {id:"pin",label:"Transaction PIN",placeholder:"••••••",type:"password"},
              ].map(({id,label,placeholder,type})=>(
                <div key={id}>
                  <p className="text-white/50 text-xs mb-1.5">{label}</p>
                  <DarkInput type={type} placeholder={placeholder} {...register(id as "recipient_account_no"|"amount"|"description"|"pin",{required:id!=="description"})}/>
                </div>
              ))}
              <button type="submit" disabled={loading}
                className="w-full h-11 rounded-xl text-white font-semibold text-sm flex items-center justify-center gap-2 hover:opacity-90 disabled:opacity-40"
                style={{background:"linear-gradient(90deg,#4361EE,#7c3aed)"}}>
                {loading&&<Loader2 className="h-4 w-4 animate-spin"/>} Send
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}




