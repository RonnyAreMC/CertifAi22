import { useEffect } from 'react';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { useAuth } from '@/stores/auth';
import { useTheme, useThemeStore } from '@/stores/theme';
import { ToastProvider } from '@/components/ui';

export default function RootLayout() {
  const refresh = useAuth((s) => s.refresh);
  const hydrate = useThemeStore((s) => s.hydrate);
  const theme = useTheme();

  useEffect(() => {
    refresh();
    hydrate();
  }, []);

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <ToastProvider>
          <StatusBar style={theme === 'dark' ? 'light' : 'dark'} />
          <Stack screenOptions={{ headerShown: false }}>
            <Stack.Screen name="index" />
            <Stack.Screen name="(auth)" />
            <Stack.Screen name="(tabs)" />
            <Stack.Screen
              name="event/[id]"
              options={{ animation: 'slide_from_right', presentation: 'card' }}
            />
            <Stack.Screen
              name="scanner"
              options={{ animation: 'slide_from_bottom', presentation: 'modal' }}
            />
          </Stack>
        </ToastProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}
