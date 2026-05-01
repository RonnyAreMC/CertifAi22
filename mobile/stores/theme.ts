/**
 * Theme store — light / dark / system. Persiste la preferencia en SecureStore.
 *
 *   const mode  = useThemeStore(s => s.mode);          // 'light' | 'dark' | 'system'
 *   const theme = useTheme();                          // 'light' | 'dark' (efectivo)
 *   const set   = useThemeStore(s => s.setMode);
 */
import { useEffect, useState } from 'react';
import { Appearance } from 'react-native';
import * as SecureStore from 'expo-secure-store';
import { create } from 'zustand';

type Mode = 'light' | 'dark' | 'system';
const KEY = 'certifai.theme';

type ThemeState = {
  mode: Mode;
  setMode: (m: Mode) => Promise<void>;
  hydrate: () => Promise<void>;
};

export const useThemeStore = create<ThemeState>((set) => ({
  mode: 'dark',
  setMode: async (m) => {
    set({ mode: m });
    await SecureStore.setItemAsync(KEY, m);
  },
  hydrate: async () => {
    const v = await SecureStore.getItemAsync(KEY);
    if (v === 'light' || v === 'dark' || v === 'system') set({ mode: v });
  },
}));

/** Devuelve el theme efectivo (resuelve `system` con Appearance). */
export function useTheme(): 'light' | 'dark' {
  const mode = useThemeStore((s) => s.mode);
  const [sys, setSys] = useState<'light' | 'dark'>(
    Appearance.getColorScheme() === 'light' ? 'light' : 'dark'
  );
  useEffect(() => {
    const sub = Appearance.addChangeListener(({ colorScheme }) => {
      setSys(colorScheme === 'light' ? 'light' : 'dark');
    });
    return () => sub.remove();
  }, []);
  return mode === 'system' ? sys : mode;
}
