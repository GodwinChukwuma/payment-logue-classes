"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Wallet, ArrowDownLeft, ArrowUpRight, ArrowLeftRight,
  CreditCard, ShieldCheck, History, LogOut,
  LayoutDashboard, Menu, X, User, ChevronRight,
} from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";

const nav = [
  { href: "/dashboard",          label: "Home",              icon: LayoutDashboard },
  { href: "/dashboard/fund",     label: "Fund Wallet",       icon: ArrowDownLeft },
  { href: "/dashboard/withdraw", label: "Withdraw",          icon: ArrowUpRight },
  { href: "/dashboard/transfer", label: "Transfer",          icon: ArrowLeftRight },
  { href: "/dashboard/loans",    label: "Loans",             icon: CreditCard },
  { href: "/dashboard/history",  label: "History",           icon: History },
  { href: "/dashboard/kyc",      label: "KYC & Verify",      icon: ShieldCheck },
];

function NavContent({ onClose }: { onClose?: () => void }) {
  const pathname = usePathname();
  const router = useRouter();
  const { email, logout } = useAuthStore();
  const firstName = email?.split("@")[0] ?? "User";

  const handleLogout = () => {
    logout();
    toast.success("Logged out");
    router.push("/login");
  };

  return (
    <div className="flex flex-col h-full" style={{ background: "linear-gradient(160deg,#4361EE 0%,#3451C7 100%)" }}>
      {/* Brand */}
      <div className="flex items-center justify-between px-5 pt-6 pb-4">
        <div className="flex items-center gap-2.5">
          <div className="h-9 w-9 rounded-xl bg-white/20 flex items-center justify-center">
            <Wallet className="h-5 w-5 text-white" />
          </div>
          <span className="text-white font-bold text-lg">VelaWallet</span>
        </div>
        {onClose && (
          <button onClick={onClose} className="text-white/60 hover:text-white p-1 rounded-lg hover:bg-white/10 transition-colors">
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      {/* User card */}
      <div className="mx-3 mb-4 p-3.5 rounded-2xl bg-white/10 flex items-center gap-3">
        <div className="h-10 w-10 rounded-full bg-white/20 flex items-center justify-center flex-shrink-0">
          <User className="h-6 w-6 text-white" />
        </div>
        <div className="min-w-0">
          <p className="text-white font-semibold text-sm capitalize truncate">{firstName}</p>
          <p className="text-white/50 text-xs truncate">{email}</p>
        </div>
      </div>

      <Separator className="bg-white/10 mx-3" />

      {/* Nav */}
      <nav className="flex-1 px-3 py-3 space-y-0.5 overflow-y-auto">
        {nav.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              onClick={onClose}
              className={cn(
                "flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all group",
                active
                  ? "bg-white text-primary shadow-sm"
                  : "text-white/75 hover:bg-white/12 hover:text-white"
              )}
            >
              <Icon className={cn("h-[18px] w-[18px] flex-shrink-0", active ? "text-primary" : "text-white/75 group-hover:text-white")} />
              <span className="flex-1">{label}</span>
              {active && <ChevronRight className="h-3.5 w-3.5 text-primary/60" />}
            </Link>
          );
        })}
      </nav>

      <Separator className="bg-white/10 mx-3" />

      {/* Logout */}
      <div className="px-3 py-4">
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium text-white/70 hover:bg-red-500/20 hover:text-red-200 w-full transition-all"
        >
          <LogOut className="h-[18px] w-[18px]" />
          Sign out
        </button>
      </div>
    </div>
  );
}

export function Sidebar() {
  const [open, setOpen] = useState(false);

  return (
    <>
      {/* ── Mobile top bar ───────────────────────────── */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-40 bg-white border-b border-border flex items-center justify-between px-4 h-14 shadow-sm">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-lg bg-primary flex items-center justify-center">
            <Wallet className="h-4 w-4 text-white" />
          </div>
          <span className="font-bold text-foreground">VelaWallet</span>
        </div>
        <Button variant="ghost" size="icon" onClick={() => setOpen(true)} className="rounded-xl">
          <Menu className="h-5 w-5" />
        </Button>
      </div>

      {/* ── Mobile drawer overlay ─────────────────────── */}
      {open && (
        <>
          {/* Backdrop */}
          <div
            className="lg:hidden fixed inset-0 z-50 bg-black/50 backdrop-blur-sm"
            onClick={() => setOpen(false)}
          />
          {/* Drawer */}
          <div className="lg:hidden fixed top-0 left-0 bottom-0 z-50 w-72 shadow-2xl">
            <NavContent onClose={() => setOpen(false)} />
          </div>
        </>
      )}

      {/* ── Desktop sidebar ───────────────────────────── */}
      <aside className="hidden lg:flex flex-col w-64 flex-shrink-0 h-screen sticky top-0">
        <NavContent />
      </aside>
    </>
  );
}
