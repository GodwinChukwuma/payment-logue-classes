"use client";
import { useRouter } from "next/navigation";
import { ArrowLeft, Home } from "lucide-react";
import { Button } from "@/components/ui/button";

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  showHome?: boolean;
}

export function PageHeader({ title, subtitle, showHome = true }: PageHeaderProps) {
  const router = useRouter();

  return (
    <div className="flex items-start gap-3 mb-5">
      {showHome && (
        <Button
          variant="outline"
          size="icon"
          onClick={() => router.push("/dashboard")}
          className="rounded-xl flex-shrink-0 mt-0.5 border-border hover:bg-primary hover:text-white hover:border-primary transition-all"
          title="Back to Home"
        >
          <Home className="h-4 w-4" />
        </Button>
      )}
      <div>
        <h1 className="text-xl font-bold text-foreground">{title}</h1>
        {subtitle && <p className="text-sm text-muted-foreground mt-0.5">{subtitle}</p>}
      </div>
    </div>
  );
}

export function BackButton({ label = "Back" }: { label?: string }) {
  const router = useRouter();
  return (
    <button
      onClick={() => router.back()}
      className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-primary transition-colors mb-4"
    >
      <ArrowLeft className="h-4 w-4" />
      {label}
    </button>
  );
}


