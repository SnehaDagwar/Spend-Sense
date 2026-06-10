const BASE_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000") + "/api/v1";

interface TokenInfo {
  accessToken: string;
  refreshToken: string;
}

export class ApiError extends Error {
  status: number;
  code?: string;
  details?: Array<{ field: string; message: string }>;

  constructor(message: string, status: number, code?: string, details?: any[]) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

// Memory cache for active access token
let _accessToken: string | null = localStorage.getItem("spend_sense_access_token");
let _refreshToken: string | null = localStorage.getItem("spend_sense_refresh_token");

export const getAccessToken = () => _accessToken;
export const getRefreshToken = () => _refreshToken;

export const setTokens = (accessToken: string, refreshToken: string) => {
  _accessToken = accessToken;
  _refreshToken = refreshToken;
  localStorage.setItem("spend_sense_access_token", accessToken);
  localStorage.setItem("spend_sense_refresh_token", refreshToken);
};

export const clearTokens = () => {
  _accessToken = null;
  _refreshToken = null;
  localStorage.removeItem("spend_sense_access_token");
  localStorage.removeItem("spend_sense_refresh_token");
};

// Queue for request retries while token is refreshing
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: any) => void;
  reject: (reason: any) => void;
  request: () => Promise<any>;
}> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(prom.request());
    }
  });
  failedQueue = [];
};

export const apiClient = {
  async request(path: string, options: RequestInit = {}): Promise<any> {
    const url = `${BASE_URL}${path}`;
    const headers = new Headers(options.headers || {});

    // Set JSON content-type if not already specified and not FormData
    if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
      headers.set("Content-Type", "application/json");
    }

    // Set Authorization header if access token exists
    if (_accessToken) {
      headers.set("Authorization", `Bearer ${_accessToken}`);
    }

    const fetchOptions: RequestInit = {
      ...options,
      headers,
    };

    const executeRequest = async () => {
      const response = await fetch(url, fetchOptions);
      
      if (response.status === 204) {
        return null;
      }

      let data: any = null;
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        data = await response.json();
      }

      if (!response.ok) {
        // Handle standardized error structure from FastAPI backend
        const errorMessage = data?.error?.message || data?.detail || `HTTP error ${response.status}`;
        const errorCode = data?.error?.code || "bad_request";
        const errorDetails = data?.error?.details || [];
        
        throw new ApiError(errorMessage, response.status, errorCode, errorDetails);
      }

      return data;
    };

    try {
      return await executeRequest();
    } catch (error: any) {
      // If error is 401, attempt to refresh the token
      if (error instanceof ApiError && error.status === 401 && _refreshToken) {
        // If already refreshing, queue this request
        if (isRefreshing) {
          return new Promise((resolve, reject) => {
            failedQueue.push({
              resolve,
              reject,
              request: () => apiClient.request(path, options), // retry original call
            });
          });
        }

        isRefreshing = true;

        try {
          // Send request to refresh token (bypass client wrapper to avoid loop)
          const refreshResponse = await fetch(`${BASE_URL}/auth/refresh`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ refreshToken: _refreshToken }),
          });

          if (!refreshResponse.ok) {
            // Refresh token failed/expired -> force logout
            clearTokens();
            processQueue(new ApiError("Session expired. Please log in again.", 401), null);
            isRefreshing = false;
            
            // Dispatch custom event to let the app know session expired
            window.dispatchEvent(new Event("auth:session-expired"));
            throw new ApiError("Session expired. Please log in again.", 401);
          }

          const refreshData = await refreshResponse.json();
          setTokens(refreshData.accessToken, refreshData.refreshToken);
          isRefreshing = false;

          // Process the queued requests and retry current request
          processQueue(null, refreshData.accessToken);
          
          // Update headers and retry current request
          headers.set("Authorization", `Bearer ${refreshData.accessToken}`);
          return await fetch(url, { ...options, headers }).then(async (res) => {
            if (res.status === 204) return null;
            const text = await res.text();
            return text ? JSON.parse(text) : null;
          });
        } catch (refreshError) {
          isRefreshing = false;
          clearTokens();
          processQueue(refreshError, null);
          window.dispatchEvent(new Event("auth:session-expired"));
          throw refreshError;
        }
      }

      throw error;
    }
  },

  get(path: string, options: RequestInit = {}): Promise<any> {
    return this.request(path, { ...options, method: "GET" });
  },

  post(path: string, body: any, options: RequestInit = {}): Promise<any> {
    return this.request(path, {
      ...options,
      method: "POST",
      body: body instanceof FormData ? body : JSON.stringify(body),
    });
  },

  put(path: string, body: any, options: RequestInit = {}): Promise<any> {
    return this.request(path, {
      ...options,
      method: "PUT",
      body: body instanceof FormData ? body : JSON.stringify(body),
    });
  },

  patch(path: string, body: any, options: RequestInit = {}): Promise<any> {
    return this.request(path, {
      ...options,
      method: "PATCH",
      body: body instanceof FormData ? body : JSON.stringify(body),
    });
  },

  delete(path: string, options: RequestInit = {}): Promise<any> {
    return this.request(path, { ...options, method: "DELETE" });
  },
};
