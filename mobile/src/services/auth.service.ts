import { apiClient, setTokens, clearTokens } from './apiClient';
import type { UserType } from '@spend-sense/shared';

export interface LoginResponse {
  accessToken: string;
  refreshToken: string;
  user: {
    id: string;
    email: string;
    displayName: string;
    userType: UserType;
    onboardingCompleted: boolean;
  };
}

export const authService = {
  async login(email: string, password: string): Promise<LoginResponse> {
    const data = await apiClient.post("/auth/login", { email, password });
    await setTokens(data.accessToken, data.refreshToken);
    return data;
  },

  async register(email: string, password: string, displayName: string, userType: UserType): Promise<LoginResponse> {
    const data = await apiClient.post("/auth/register", {
      email,
      password,
      displayName,
      userType,
    });
    await setTokens(data.accessToken, data.refreshToken);
    return data;
  },

  async logout(refreshToken: string): Promise<void> {
    try {
      await apiClient.post("/auth/logout", { refreshToken });
    } catch (e) {
      console.warn("Logout request to server failed", e);
    } finally {
      await clearTokens();
    }
  },

  async getMe(): Promise<any> {
    return apiClient.get("/auth/me");
  }
};
