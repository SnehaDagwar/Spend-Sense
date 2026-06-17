import { create } from "zustand";
import { authService } from "../services/auth.service";
import { loadTokens, clearTokens, getRefreshToken } from "../services/apiClient";
import type { UserType, UserSettings } from "@spend-sense/shared";

interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: {
    id: string;
    email: string;
    displayName: string;
    userType: UserType;
    onboardingCompleted: boolean;
  } | null;
  
  initializeAuth: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName: string, userType: UserType) => Promise<void>;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: false,
  isLoading: true,
  user: null,

  initializeAuth: async () => {
    set({ isLoading: true });
    try {
      await loadTokens();
      const user = await authService.getMe();
      set({ user, isAuthenticated: true });
    } catch (e) {
      await clearTokens();
      set({ user: null, isAuthenticated: false });
    } finally {
      set({ isLoading: false });
    }
  },

  login: async (email, password) => {
    set({ isLoading: true });
    try {
      const response = await authService.login(email, password);
      set({
        isAuthenticated: true,
        user: response.user,
        isLoading: false
      });
    } catch (e) {
      set({ isLoading: false });
      throw e;
    }
  },

  register: async (email, password, displayName, userType) => {
    set({ isLoading: true });
    try {
      const response = await authService.register(email, password, displayName, userType);
      set({
        isAuthenticated: true,
        user: response.user,
        isLoading: false
      });
    } catch (e) {
      set({ isLoading: false });
      throw e;
    }
  },

  logout: async () => {
    set({ isLoading: true });
    const token = getRefreshToken();
    try {
      if (token) {
        await authService.logout(token);
      } else {
        await clearTokens();
      }
    } catch (e) {
      console.warn("Logout request failed", e);
    } finally {
      set({
        isAuthenticated: false,
        user: null,
        isLoading: false
      });
    }
  }
}));
