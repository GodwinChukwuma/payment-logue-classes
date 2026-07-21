import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

export function formatNaira(amount: string | number) {
    const value = Number(amount);
    if (!Number.isFinite(value)) return "₦0.00";

    return new Intl.NumberFormat("en-NG", {
        style: "currency",
        currency: "NGN",
        minimumFractionDigits: 2,
    }).format(value);
}

export function formatDate(dateStr: string) {
    return new Date(dateStr).toLocaleDateString("en-US", {
        day: "numeric",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
    });
}

export function getErrorMessage(err: unknown): string {
    if (axios_is_axios_error(err)) {
        return (
            err.response?.data?.error?.message  ||
            err.response?.data?.detail ||
            "Something went wrong"
        );
    }
    if (err instanceof Error) return err.message;
    return "Something went wrong";
}

function axios_is_axios_error(err: unknown): err is {
    response?: { data?: { error?: { message?: string }; detail?: string } };
} {
    return typeof err === "object" && err !== null && "response" in err;
}

