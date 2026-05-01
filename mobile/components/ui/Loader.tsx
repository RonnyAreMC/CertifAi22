/**
 * Loader oficial de CertifAI — el tigre/zorro que persigue, animado con
 * un float vertical suave para dar vida sin marear. Equivalente al loader
 * que usa la web (`static/tiger_chase_loader.png`).
 *
 *   <Loader />
 *   <Loader size={140} label="Cargando tu cuenta…" />
 *   <Loader fullscreen />   // ocupa toda la pantalla, centrado
 */
import { useEffect, useRef } from 'react';
import { Animated, Easing, Image, StyleSheet, Text, View } from 'react-native';

import { spacing, themed, typography } from '@/theme/tokens';
import { useTheme } from '@/stores/theme';

type Props = {
  size?: number;
  label?: string;
  fullscreen?: boolean;
};

export function Loader({ size = 96, label, fullscreen = false }: Props) {
  const float = useRef(new Animated.Value(0)).current;
  const theme = useTheme();
  const t = themed(theme);

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(float, { toValue: 1, duration: 900, easing: Easing.inOut(Easing.quad), useNativeDriver: true }),
        Animated.timing(float, { toValue: 0, duration: 900, easing: Easing.inOut(Easing.quad), useNativeDriver: true }),
      ]),
    ).start();
  }, []);

  const transform = {
    transform: [
      { translateY: float.interpolate({ inputRange: [0, 1], outputRange: [-3, 4] }) },
      { scale:      float.interpolate({ inputRange: [0, 1], outputRange: [1, 1.04] }) },
    ],
  };

  const content = (
    <View style={styles.wrap}>
      <Animated.Image
        source={require('../../assets/tiger_chase_loader.png')}
        style={[{ width: size, height: size, resizeMode: 'contain' }, transform]}
      />
      {label ? (
        <Text style={[styles.label, { color: t.textMuted }]} numberOfLines={2}>
          {label}
        </Text>
      ) : null}
    </View>
  );

  if (fullscreen) {
    return (
      <View style={[styles.fullscreen, { backgroundColor: t.bg }]}>
        {content}
      </View>
    );
  }
  return content;
}

const styles = StyleSheet.create({
  wrap:       { alignItems: 'center', justifyContent: 'center', gap: spacing.base },
  fullscreen: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  label: {
    fontSize: typography.sm,
    fontWeight: typography.medium,
    textAlign: 'center',
    paddingHorizontal: spacing.lg,
  },
});
