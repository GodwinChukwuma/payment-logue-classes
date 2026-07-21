import { create } from "zustand";

interface AuthState {
    accessToken: string | null;
    refreshToken: string | null;
    email: string | null;
    isAuthenticated: boolean;
    login: (access: string, refresh: string, email: string) => void;
    logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
    accessToken:
        typeof window !== "undefined" ? localStorage.getItem("access_token") : null,
    refreshToken:
        typeof window !== "undefined" ? localStorage.getItem("refresh_token") : null,
    email:
        typeof window !== "undefined" ? localStorage.getItem("user_email") : null,
    isAuthenticated:
        typeof window !== "undefined" ? !!localStorage.getItem("access_token") : false,
    login: (access, refresh, email) => {
        localStorage.setItem("access_token", access);
        localStorage.setItem("refresh_token", refresh);
        localStorage.setItem("user_email", email);
        set({ accessToken: access, refreshToken: refresh, email: email, isAuthenticated: true });
    },

    logout: () => {
        localStorage.clear();
        set({ accessToken: null, refreshToken: null, email: null, isAuthenticated: false });
    }
}));

