"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, email, logout } = useAuthStore();
  const router = useRouter();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    if (!isAuthenticated) router.replace("/login");
  }, [isAuthenticated, router]);

  if (!mounted || !isAuthenticated) return null;

  const displayName = email?.split("@")[0]?.replace(/\./g, " ")
    .split(" ").map((w:string) => w.charAt(0).toUpperCase() + w.slice(1)).join(" ") ?? "User";
  const initial = displayName.trim().charAt(0).toUpperCase();

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <div style={{ position:"relative", minHeight:"100vh" }}>
      {/* Aurora */}
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
        <div className="user-badge">
          <span className="avatar">{initial}</span>
          <span style={{fontWeight:600,fontSize:"0.92rem"}}>{displayName}</span>
          <button onClick={handleLogout} className="btn btn-ghost btn-sm">Logout</button>
        </div>
      </header>

      <main style={{position:"relative",zIndex:1}}>
        {children}
      </main>
    </div>
  );
}






