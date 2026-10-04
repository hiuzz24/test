import axios from "axios";
import { clearAuthSession } from "@/lib/authSession";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor: attach Bearer token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor: handle 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const isCredentialRequest = ["/auth/login", "/auth/register"].includes(
      error.config?.url?.split("?")[0] ?? ""
    );
    // Invalid credentials belong to the form, not the expired-session flow.
    if (error.response?.status === 401 && !isCredentialRequest) {
      clearAuthSession();
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);
