/**
 * Card con variantes y press-lift animado (equivalente al `hoverable` web).
 *
 * Variantes:
 *   - default:  card oscura con borde sutil + sombra ios
 *   - elevated: sombra más fuerte
 *   - glass:    fondo translúcido con blur ligero
 *   - brand:    borde y glow naranja (uso destacado)
 */
import { useRef } from 'react';
import {
  Animated, Pressable, StyleSheet, View, type ViewProps, type ViewStyle,
} from 'react-native';

import { colors, radius, shadows, spacing } from '@/theme/tokens';

type Variant = 'default' | 'elevated' | 'glass' | 'brand';

type Props = ViewProps & {
  variant?: Variant;
  /** Si onPress está definido, el card se vuelve presionable y se eleva al press. */
  onPress?: () => void;
  pressable?: boolean;
  padded?: boolean;
};

const variantStyles: Record<Variant, ViewStyle> = {
  default: {
    backgroundColor: colors.cardDark,
    borderColor: colors.borderDark,
    borderWidth: 1,
    ...shadows.sm,
  },
  elevated: {
    backgroundColor: colors.cardDark,
    borderColor: colors.borderDark,
    borderWidth: 1,
    ...shadows.md,
  },
  glass: {
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderColor: 'rgba(255,255,255,0.10)',
    borderWidth: 1,
    ...shadows.sm,
  },
  brand: {
    backgroundColor: colors.cardDark,
    borderColor: colors.brand,
    borderWidth: 1,
    ...shadows.brand,
  },
};

export function Card({
  variant = 'default', onPress, pressable, padded = true, style, children, ...rest
}: Props) {
  const lift = useRef(new Animated.Value(0)).current;

  if (!onPress && !pressable) {
    return (
      <View
        style={[styles.base, variantStyles[variant], padded && styles.padded, style]}
        {...rest}
      >
        {children}
      </View>
    );
  }

  function onPressIn() {
    Animated.spring(lift, { toValue: 1, useNativeDriver: true, speed: 30, bounciness: 0 }).start();
  }
  function onPressOut() {
    Animated.spring(lift, { toValue: 0, useNativeDriver: true, speed: 18, bounciness: 4 }).start();
  }

  const transform = {
    transform: [
      { translateY: lift.interpolate({ inputRange: [0, 1], outputRange: [0, -3] }) },
      { scale:      lift.interpolate({ inputRange: [0, 1], outputRange: [1, 1.01] }) },
    ],
  };

  return (
    <Pressable onPress={onPress} onPressIn={onPressIn} onPressOut={onPressOut}>
      <Animated.View
        style={[styles.base, variantStyles[variant], padded && styles.padded, transform, style]}
      >
        {children}
      </Animated.View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base:   { borderRadius: radius.lg },
  padded: { padding: spacing.base },
});
