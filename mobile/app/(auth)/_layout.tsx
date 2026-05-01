import { Redirect, Stack } from 'expo-router';

import { useAuth } from '@/stores/auth';

export default function AuthLayout() {
  const participante = useAuth((s) => s.participante);

  // Si ya hay sesión, salir del grupo auth.
  if (participante) return <Redirect href="/(tabs)" />;

  return <Stack screenOptions={{ headerShown: false }} />;
}
