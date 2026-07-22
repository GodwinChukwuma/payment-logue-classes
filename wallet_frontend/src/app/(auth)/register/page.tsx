// "use client";
// import { useState } from "react";
// import { useRouter } from "next/navigation";
// import { useForm } from "react-hook-form";
// import { zodResolver } from "@hookform/resolvers/zod";
// import { z } from "zod";
// import { toast } from "sonner";
// import { Loader2 } from "lucide-react";
// import Link from "next/link";
// import Image from "next/image";
// import { Button } from "@/components/ui/button";
// import { Input } from "@/components/ui/input";
// import { Label } from "@/components/ui/label";
// import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
// import api from "@/lib/api";
// import { getErrorMessage } from "@/lib/utils";

// const schema = z.object({
//   full_name: z.string().min(2, "Full name required"),
//   email: z.string().email("Enter a valid email"),
//   password: z.string().min(8, "At least 8 characters"),
//   bvn: z.string().length(11, "BVN must be 11 digits"),
//   pin: z.string().min(4).max(6, "PIN must be 4–6 digits"),
// });
// type FormData = z.infer<typeof schema>;

// const fields = [
//   { id: "full_name", label: "Full Name", type: "text", placeholder: "Godwin Chukwudi" },
//   { id: "email", label: "Email", type: "email", placeholder: "you@example.com" },
//   { id: "password", label: "Password", type: "password", placeholder: "Min 8 characters" },
//   { id: "bvn", label: "BVN", type: "text", placeholder: "11-digit BVN" },
//   { id: "pin", label: "Transaction PIN", type: "password", placeholder: "4–6 digit PIN" },
// ];

// export default function RegisterPage() {
//   const router = useRouter();
//   const [loading, setLoading] = useState(false);
//   const [devToken, setDevToken] = useState<string | null>(null);

//   const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
//     resolver: zodResolver(schema),
//   });

//   const onSubmit = async (data: FormData) => {
//     setLoading(true);
//     try {
//       const res = await api.post("/auth/register/", data);
//       setDevToken(res.data.dev_otp ?? res.data.dev_email_verification_token);
//       toast.success("Account created!");
//       setTimeout(() => router.push("/login"), 4000);
//     } catch (err) {
//       toast.error(getErrorMessage(err));
//     } finally {
//       setLoading(false);
//     }
//   };

//   return (
//     <div className="min-h-screen flex">
//       {/* Left panel */}
//       <div className="hidden lg:flex flex-1 relative overflow-hidden items-center justify-center"
//         style={{ background: "linear-gradient(135deg, #0d0221 0%, #1a0533 40%, #0d1b5e 100%)" }}>
//         <div className="absolute inset-0 opacity-20"
//           style={{ backgroundImage: "linear-gradient(rgba(130,80,255,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(130,80,255,0.3) 1px, transparent 1px)", backgroundSize: "60px 60px" }} />
//         <div className="relative z-10 text-center px-12">
//           <Image src="/illustrations/transfer-banner.png" alt="Transfer" width={480} height={280}
//             className="mx-auto mb-8 rounded-2xl" />
//           <h2 className="text-3xl font-bold text-white mb-2">Start Your Journey</h2>
//           <p className="text-purple-200/70">Tier 1 gets you started. Verify to unlock more.</p>
//           <div className="mt-6 grid grid-cols-3 gap-3 text-center">
//             {[
//               { tier: "Tier 1", desc: "₦50k limit", sub: "Register" },
//               { tier: "Tier 2", desc: "₦500k limit", sub: "Email + Phone" },
//               { tier: "Tier 3", desc: "₦10M limit", sub: "BVN + Face ID" },
//             ].map((t) => (
//               <div key={t.tier} className="bg-white/10 rounded-xl p-3">
//                 <p className="text-white font-bold text-sm">{t.tier}</p>
//                 <p className="text-purple-200 text-xs mt-0.5">{t.desc}</p>
//                 <p className="text-purple-300/60 text-xs">{t.sub}</p>
//               </div>
//             ))}
//           </div>
//         </div>
//       </div>

//       {/* Right panel */}
//       <div className="flex-1 flex items-center justify-center p-6 bg-background overflow-y-auto">
//         <div className="w-full max-w-sm py-6">
//           {devToken && (
//             <div className="mb-4 p-4 bg-amber-50 border border-amber-200 rounded-2xl">
//               <p className="text-xs font-semibold text-amber-700 uppercase tracking-wide">Dev — Email OTP</p>
//               <p className="text-3xl font-bold text-amber-900 tracking-[0.3em] mt-1">{devToken}</p>
//               <p className="text-xs text-amber-600 mt-1">Redirecting in 4s…</p>
//             </div>
//           )}

//           <Card className="border-border shadow-xl">
//             <CardHeader className="pb-4">
//               <CardTitle className="text-2xl">Create account</CardTitle>
//               <CardDescription>Start with Tier 1 and unlock more features as you verify</CardDescription>
//             </CardHeader>
//             <CardContent>
//               <form onSubmit={handleSubmit(onSubmit)} className="space-y-3.5">
//                 {fields.map(({ id, label, type, placeholder }) => (
//                   <div key={id} className="space-y-1.5">
//                     <Label htmlFor={id}>{label}</Label>
//                     <Input id={id} type={type} placeholder={placeholder}
//                       className="h-10 rounded-xl" {...register(id as keyof FormData)} />
//                     {errors[id as keyof FormData] && (
//                       <p className="text-xs text-destructive">{errors[id as keyof FormData]?.message}</p>
//                     )}
//                   </div>
//                 ))}
//                 <Button type="submit" className="w-full h-11 rounded-xl font-semibold mt-1" disabled={loading}>
//                   {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
//                   Create account
//                 </Button>
//               </form>
//               <p className="text-center text-sm text-muted-foreground mt-5">
//                 Already have an account?{" "}
//                 <Link href="/login" className="text-primary font-semibold hover:underline">Sign in</Link>
//               </p>
//             </CardContent>
//           </Card>
//         </div>
//       </div>
//     </div>
//   );
// }

"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

// Register is now handled as a tab on the login page
export default function RegisterPage() {
  const router = useRouter();
  useEffect(() => { router.replace("/login?tab=register"); }, [router]);
  return null;
}

