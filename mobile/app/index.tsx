import { Redirect } from 'expo-router';

import { useAuth } from '@/stores/auth';
import { Loader } from '@/components/ui';

export default function Index() {
  const participante = useAuth((s) => s.participante);
  const ready = useAuth((s) => s.ready);

  if (!ready) {
    return <Loader fullscreen size={120} />;
  }
  return <Redirect href={participante ? '/(tabs)' : '/(auth)/landing'} />;
}
