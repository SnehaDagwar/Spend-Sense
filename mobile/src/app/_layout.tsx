import { useEffect } from 'react';
import { ActivityIndicator, View } from 'react-native';
import { Stack, useRouter, useSegments } from 'expo-router';
import { useAuthStore } from '../store/useAuthStore';
import { subscribeToSessionExpired } from '../services/apiClient';

export default function RootLayout() {
  const { isAuthenticated, isLoading, initializeAuth, logout } = useAuthStore();
  const segments = useSegments();
  const router = useRouter();

  // Initialize Auth status on app launch
  useEffect(() => {
    initializeAuth();
  }, []);

  // Listen to HTTP 401 Session Expired events
  useEffect(() => {
    const unsubscribe = subscribeToSessionExpired(() => {
      logout();
      router.replace('/login');
    });
    return () => unsubscribe();
  }, [logout, router]);

  // Navigate according to auth state changes
  useEffect(() => {
    if (isLoading) return;

    const inAuthGroup = segments[0] === '(auth)';

    if (!isAuthenticated) {
      // Redirect to login if not authenticated and not in auth screens
      if (!inAuthGroup) {
        router.replace('/login');
      }
    } else if (isAuthenticated) {
      // Redirect to home dashboard if authenticated but on auth screens
      if (inAuthGroup || segments.length === 0 || segments[0] === 'index' || segments[0] === '') {
        router.replace('/(tabs)');
      }
    }
  }, [isAuthenticated, segments, isLoading]);

  if (isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#0f172a' }}>
        <ActivityIndicator size="large" color="#6366f1" />
      </View>
    );
  }

  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="(auth)" options={{ headerShown: false }} />
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
    </Stack>
  );
}
