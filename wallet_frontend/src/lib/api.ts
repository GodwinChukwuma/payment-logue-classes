import axios from "axios";

const api = axios.create({
    baseURL: "http://localhost:8000/api",
    headers: {
        "Content-Type": "application/json",
    },
});

// Attach access token to every request
api.interceptors.request.use((config) => {
    // ensure headers object exists
    config.headers = config.headers || {};

    // normalize URL to always include a trailing slash (preserve querystring)
    if (config.url) {
        const [path, query] = String(config.url).split("?");
        if (!path.endsWith("/")) {
            config.url = path + "/" + (query ? "?" + query : "");
        }
    } else if (config.baseURL && typeof config.baseURL === "string") {
        // if only baseURL is provided, ensure it ends with a slash so relative urls concatenate correctly
        if (!config.baseURL.endsWith("/")) config.baseURL = config.baseURL + "/";
    }

    const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
    if (token) config.headers.Authorization = `Bearer ${token}`;

    // Debug: log the final request method and URL as axios will send it
    try {
        const method = (config.method || "get").toString().toUpperCase();
        const base = config.baseURL || "";
        const url = config.url || "";
        // eslint-disable-next-line no-console
        console.debug(`[api] ${method} ${base}${url}`);
    } catch (e) {
        // ignore logging errors
    }

    return config;
});

// Auto refresh on 401
api.interceptors.response.use(
    (res) => res,
    async (err) => {
        const original = err.config;

        if (err.response?.status === 401 && !original._retry) {
            original._retry = true;

            const refresh = localStorage.getItem("refresh_token");

            if (refresh) {
                try {
                    const { data } = await axios.post("/api/auth/token/refresh/", {
                        refresh,
                    });
                    localStorage.setItem("access_token", data.access);
                    original.headers.Authorization = `Bearer ${data.access}`;
                    return api(original);
                } catch {
                    localStorage.clear();
                    window.location.href = "/login";
                }
            }
        }

        return Promise.reject(err);
    }
);

export default api;

