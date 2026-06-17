import axios from "axios";
import { getAccessToken, getRefreshToken, setTokens, removeTokens } from "./auth";

// Use relative URL to leverage Next.js proxy (no CORS issues)
const API_BASE_URL = "/api";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Shared refresh promise to deduplicate concurrent refresh attempts
let refreshPromise: Promise<string> | null = null;

function getRefreshedToken(): Promise<string> | null {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return null;

  if (!refreshPromise) {
    refreshPromise = axios
      .post(`${API_BASE_URL}/auth/refresh`, null, {
        headers: { Authorization: `Bearer ${refreshToken}` },
      })
      .then((res) => {
        const newAccessToken: string = res.data.access_token;
        const newRefreshToken: string = res.data.refresh_token || refreshToken;
        setTokens(newAccessToken, newRefreshToken);
        return newAccessToken;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }

  return refreshPromise;
}

// Attach access token to requests
api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const tokenPromise = getRefreshedToken();
      if (tokenPromise) {
        try {
          const newToken = await tokenPromise;
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return api(originalRequest);
        } catch {
          removeTokens();
          if (typeof window !== "undefined") {
            window.location.href = "/login";
          }
        }
      } else {
        removeTokens();
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
      }
    }

    return Promise.reject(error);
  }
);

export default api;
