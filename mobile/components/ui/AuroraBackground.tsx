/**
 * Fondo "aurora": dos gradientes radiales/diagonales suaves que flotan
 * lentamente. Equivalente al `aurora-bg` del design system web.
 *
 * Uso:
 *   <View style={{ flex: 1 }}>
 *     <AuroraBackground />
 *     <YourContent />   // queda encima por z-order
 *   </View>
 */
import { useEffect } from 'react';
import { StyleSheet, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Animated, {
  Easing, useAnimatedStyle, useSharedValue, withRepeat, withTiming,
} from 'react-native-reanimated';

import { colors } from '@/theme/tokens';

export function AuroraBackground({
  intensity = 0.7,
}: { intensity?: number }) {
  const t = useSharedValue(0);

  useEffect(() => {
    t.value = withRepeat(
      withTiming(1, { duration: 12000, easing: Easing.inOut(Easing.ease) }),
      -1,
      true,
    );
  }, []);

  const blob1Style = useAnimatedStyle(() => ({
    transform: [
      { translateX: -50 + t.value * 80 },
      { translateY: -30 + t.value * 60 },
      { scale: 1 + t.value * 0.15 },
    ],
    opacity: 0.55 * intensity,
  }));

  const blob2Style = useAnimatedStyle(() => ({
    transform: [
      { translateX: 40 - t.value * 80 },
      { translateY: 60 - t.value * 50 },
      { scale: 1.2 - t.value * 0.15 },
    ],
    opacity: 0.45 * intensity,
  }));

  return (
    <View pointerEvents="none" style={StyleSheet.absoluteFill}>
      <Animated.View style={[styles.blob, styles.blob1, blob1Style]}>
        <LinearGradient
          colors={[colors.brand, 'transparent']}
          start={{ x: 0.2, y: 0.2 }}
          end={{ x: 1, y: 1 }}
          style={styles.gradient}
        />
      </Animated.View>

      <Animated.View style={[styles.blob, styles.blob2, blob2Style]}>
        <LinearGradient
          colors={[colors.accent, 'transparent']}
          start={{ x: 0.8, y: 0.2 }}
          end={{ x: 0, y: 1 }}
          style={styles.gradient}
        />
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  blob: {
    position: 'absolute',
    width: 360,
    height: 360,
    borderRadius: 180,
  },
  blob1: { top: -80, left: -80 },
  blob2: { top: 120, right: -100 },
  gradient: { flex: 1, borderRadius: 180 },
});
