"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Wallet, ArrowDownLeft, ArrowUpRight, ArrowLeftRight,
  CreditCard, ShieldCheck, History, LogOut,
  LayoutDashboard, Menu, X, User, HelpCircle,
} from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/auth";
import { toast } from "sonner";

const nav = [
  { href: "/dashboard", label: "Home", icon: LayoutDashboard },
  { href: "/dashboard/fund", label: "Fund Wallet", icon: ArrowDownLeft },
  { href: "/dashboard/withdraw", label: "Withdraw", icon: ArrowUpRight },
  { href: "/dashboard/transfer", label: "Transfer", icon: ArrowLeftRight },
  { href: "/dashboard/loans", label: "Loans", icon: CreditCard },
  { href: "/dashboard/history", label: "History", icon: History },
  { href: "/dashboard/kyc", label: "KYC & Verification", icon: ShieldCheck },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { email, logout } = useAuthStore();
  const [open, setOpen] = useState(false);

  const handleLogout = () => {
    logout();
    toast.success("Logged out");
    router.push("/login");
  };

  const firstName = email?.split("@")[0] ?? "User";

  const SidebarContent = () => (
    <div className="sidebar-gradient h-full flex flex-col text-white">
      {/* Profile section — matches the blue profile panel in reference */}
      <div className="px-6 pt-8 pb-6 border-b border-white/10">
        <div className="flex items-center gap-4">
          <div className="h-14 w-14 rounded-full bg-white/20 flex items-center justify-center">
            <User className="h-8 w-8 text-white" />
          </div>
          <div>
            <p className="font-bold text-lg capitalize">{firstName}</p>
            <p className="text-white/60 text-xs truncate max-w-[160px]">{email}</p>
          </div>
        </div>
      </div>

      {/* Nav links */}
      <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
        {nav.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            onClick={() => setOpen(false)}
            className={cn(
              "flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all",
              pathname === href
                ? "bg-white text-primary shadow-md"
                : "text-white/80 hover:bg-white/10"
            )}
          >
            <Icon className={cn("h-5 w-5 flex-shrink-0",
              pathname === href ? "text-primary" : "text-white/80"
            )} />
            {label}
          </Link>
        ))}
      </nav>

      {/* Bottom section */}
      <div className="px-4 pb-6 space-y-1 border-t border-white/10 pt-4">
        <button className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm text-white/70 hover:bg-white/10 w-full transition-all">
          <HelpCircle className="h-5 w-5" />
          Help & Support
        </button>
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm text-white/70 hover:bg-red-500/20 hover:text-red-200 w-full transition-all"
        >
          <LogOut className="h-5 w-5" />
          Log out
        </button>
      </div>
    </div>
  );

  return (
    <>
      {/* Mobile top bar */}
      <div className="lg:hidden flex items-center justify-between px-4 py-3 bg-white border-b border-border sticky top-0 z-40 card-shadow">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-xl bg-primary flex items-center justify-center">
            <Wallet className="h-5 w-5 text-white" />
          </div>
          <span className="font-bold text-foreground">VelaWallet</span>
        </div>
        <button
          onClick={() => setOpen(!open)}
          className="p-2 rounded-xl hover:bg-muted transition-colors"
        >
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile drawer */}
      {open && (
        <div
          className="lg:hidden fixed inset-0 z-50 bg-black/50"
          onClick={() => setOpen(false)}
        >
          <div
            className="w-72 h-full"
            onClick={(e) => e.stopPropagation()}
          >
            <SidebarContent />
          </div>
        </div>
      )}

      {/* Desktop sidebar */}
      <aside className="hidden lg:flex flex-col w-64 h-screen sticky top-0 flex-shrink-0">
        <SidebarContent />
      </aside>
    </>
  );
}
