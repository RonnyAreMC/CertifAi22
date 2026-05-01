/**
 * VBackground — aurora pastel suave, mirror del `.aurora-bg` web.
 *
 * Técnica: círculos sólidos (View con borderRadius:full) + BlurView muy
 * fuerte por encima. El BlurView difumina el borde duro del círculo en
 * un halo radial smooth — equivalente a `filter: blur(40px)` del web,
 * pero sin necesitar svg ni assets.
 */
import { useEffect } from 'react';
import { Dimensions, Platform, StyleSheet, View } from 'react-native';
import { BlurView } from 'expo-blur';
import Animated, {
  Easing, useAnimatedStyle, useSharedValue, withRepeat, withTiming,
} from 'react-native-reanimated';

import { useTheme } from '@/stores/theme';

type Props = {
  intensity?: number;
  variant?: 'brand' | 'navy' | 'mixed';  // legacy, ignorado
};

// Paleta institucional: azul navy + cyan claro + naranja muy suave.
// Cero rosado ni violeta — eso mezclado con dark navy daba verdoso.
const PALETTE_LIGHT = {
  cyan: 'rgba(186, 230, 253, 0.95)',  // sky-200 (celeste claro)
  navy: 'rgba(165, 180, 252, 0.65)',  // indigo-300 — solo en light, suave
  warm: 'rgba(254, 215, 170, 0.70)',  // orange-200 (un toque cálido del brand)
};
// Dark mode: VBackground retorna null. Solo el bg navy sólido (look "perfil").

const { width: SW, height: SH } = Dimensions.get('window');
const BLOB = Math.max(SW, SH) * 0.85;

export function VBackground({ intensity = 0.7 }: Props) {
  const theme = useTheme();
  const palette = PALETTE_LIGHT;     // dark mode retorna null (ver abajo)

  const t1 = useSharedValue(0);
  const t2 = useSharedValue(0);
  const t3 = useSharedValue(0);

  useEffect(() => {
    t1.value = withRepeat(withTiming(1, { duration: 16000, easing: Easing.inOut(Easing.ease) }), -1, true);
    t2.value = withRepeat(withTiming(1, { duration: 22000, easing: Easing.inOut(Easing.ease) }), -1, true);
    t3.value = withRepeat(withTiming(1, { duration: 26000, easing: Easing.inOut(Easing.ease) }), -1, true);
  }, []);

  const blob1 = useAnimatedStyle(() => ({
    transform: [
      { translateX: -SW * 0.10 + t1.value * SW * 0.30 },
      { translateY: -SH * 0.05 + t1.value * SH * 0.18 },
      { scale: 1 + t1.value * 0.18 },
    ],
    opacity: intensity,
  }));

  const blob2 = useAnimatedStyle(() => ({
    transform: [
      { translateX: SW * 0.08 - t2.value * SW * 0.22 },
      { translateY: SH * 0.10 - t2.value * SH * 0.18 },
      { scale: 1.10 - t2.value * 0.18 },
    ],
    opacity: intensity * 0.9,
  }));

  const blob3 = useAnimatedStyle(() => ({
    transform: [
      { translateX: t3.value * SW * 0.18 - SW * 0.05 },
      { translateY: t3.value * SH * 0.16 - SH * 0.05 },
      { scale: 0.95 + t3.value * 0.20 },
    ],
    opacity: intensity * 0.7,
  }));

  // En dark mode: solo navy sólido, sin blobs (look limpio tipo "perfil")
  if (theme === 'dark') return null;

  const blurTint =
    Platform.OS === 'ios' ? 'systemMaterialLight' : 'light';

  return (
    <View pointerEvents="none" style={StyleSheet.absoluteFill}>
      {/* Capa de blobs sólidos circulares */}
      <Animated.View
        style={[
          styles.blob,
          { top: -BLOB * 0.45, left: -BLOB * 0.35, backgroundColor: palette.cyan },
          blob1,
        ]}
      />
      <Animated.View
        style={[
          styles.blob,
          { bottom: -BLOB * 0.45, right: -BLOB * 0.35, backgroundColor: palette.navy },
          blob2,
        ]}
      />
      <Animated.View
        style={[
          styles.blob,
          {
            top: -BLOB * 0.30,
            left: SW * 0.20 - BLOB * 0.5,
            backgroundColor: palette.warm,
          },
          blob3,
        ]}
      />

      {/* BlurView muy fuerte = `filter: blur(40px)` del CSS */}
      <BlurView
        intensity={Platform.OS === 'ios' ? 90 : 100}
        tint={blurTint as any}
        style={StyleSheet.absoluteFill}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  blob: {
    position: 'absolute',
    width: BLOB,
    height: BLOB,
    borderRadius: BLOB / 2,
  },
});
