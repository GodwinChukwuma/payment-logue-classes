"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Loader2, Wallet } from "lucide-react";
import Link from "next/link";
import api from "@/lib/api";
import { getErrorMessage } from "@/lib/utils";

const schema = z.object({
  full_name: z.string().min(2, "Full name required"),
  email: z.string().email("Enter a valid email"),
  password: z.string().min(8, "At least 8 characters"),
  bvn: z.string().length(11, "BVN must be 11 digits"),
  pin: z.string().min(4).max(6, "PIN must be 4–6 digits"),
});
type FormData = z.infer<typeof schema>;

const fields = [
  { id: "full_name", label: "Full Name", type: "text", placeholder: "Godwin Chukwudi" },
  { id: "email", label: "Email", type: "email", placeholder: "you@example.com" },
  { id: "password", label: "Password", type: "password", placeholder: "Min 8 characters" },
  { id: "bvn", label: "BVN", type: "text", placeholder: "11-digit BVN" },
  { id: "pin", label: "Transaction PIN", type: "password", placeholder: "4–6 digit PIN" },
];

export default function RegisterPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [devToken, setDevToken] = useState<string | null>(null);

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormData) => {
    setLoading(true);
    try {
      const res = await api.post("/auth/register/", data);
      setDevToken(res.data.dev_otp ?? res.data.dev_email_verification_token);
      toast.success("Account created!");
      setTimeout(() => router.push("/login"), 4000);
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col" style={{background:"linear-gradient(160deg,#4361EE 0%,#3A56D4 40%,#f5f5ff 40%)"}}>
      <div className="flex items-center gap-3 p-6">
        <div className="h-10 w-10 rounded-2xl bg-white/20 flex items-center justify-center">
          <Wallet className="h-6 w-6 text-white" />
        </div>
        <span className="text-xl font-bold text-white">VelaWallet</span>
      </div>

      <div className="flex-1 flex items-start justify-center px-4 pb-8">
        <div className="w-full max-w-sm">
          {devToken && (
            <div className="mb-4 p-4 bg-amber-50 border border-amber-200 rounded-2xl">
              <p className="text-xs font-semibold text-amber-700 uppercase tracking-wide">Dev — Email OTP</p>
              <p className="text-3xl font-bold text-amber-900 tracking-[0.3em] mt-1">{devToken}</p>
              <p className="text-xs text-amber-600 mt-1">Redirecting to login in 4s…</p>
            </div>
          )}

          <div className="bg-white rounded-3xl p-7 card-shadow">
            <h1 className="text-2xl font-bold text-foreground">Create account</h1>
            <p className="text-muted-foreground text-sm mt-1 mb-5">Start with Tier 1. Verify to unlock more.</p>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-3.5">
              {fields.map(({ id, label, type, placeholder }) => (
                <div key={id}>
                  <label className="text-sm font-medium text-foreground block mb-1">{label}</label>
                  <input
                    type={type}
                    placeholder={placeholder}
                    className="w-full h-11 px-4 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                    {...register(id as keyof FormData)}
                  />
                  {errors[id as keyof FormData] && (
                    <p className="text-xs text-destructive mt-0.5">{errors[id as keyof FormData]?.message}</p>
                  )}
                </div>
              ))}

              <button
                type="submit"
                disabled={loading}
                className="w-full h-12 rounded-xl bg-primary text-white font-semibold text-sm flex items-center justify-center gap-2 hover:bg-primary/90 transition-all disabled:opacity-60 mt-1"
              >
                {loading && <Loader2 className="h-4 w-4 animate-spin" />}
                Create account
              </button>
            </form>

            <p className="text-center text-sm text-muted-foreground mt-5">
              Already have an account?{" "}
              <Link href="/login" className="text-primary font-semibold hover:underline">Sign in</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

