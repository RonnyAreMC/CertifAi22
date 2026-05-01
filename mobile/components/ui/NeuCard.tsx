/**
 * NeuCard — superficie con sombras neumorfistas (luz arriba-izq, sombra abajo-der)
 * + opcional press-inset que invierte las sombras al tocar.
 *
 *   <NeuCard>...</NeuCard>
 *   <NeuCard onPress={...}>tocable, se hunde</NeuCard>
 *   <NeuCard variant="raised">elevación más fuerte</NeuCard>
 */
import { useRef } from 'react';
import {
  Animated, Pressable, StyleSheet, View,
  type ViewProps, type ViewStyle,
} from 'react-native';

import { neuShadow, radius, spacing, themed } from '@/theme/tokens';
import { useTheme } from '@/stores/theme';

type Variant = 'flat' | 'raised';

type Props = ViewProps & {
  onPress?: () => void;
  variant?: Variant;
  padded?: boolean;
};

export function NeuCard({
  onPress, variant = 'flat', padded = true,
  style, children, ...rest
}: Props) {
  const theme = useTheme();
  const t = themed(theme);
  const press = useRef(new Animated.Value(0)).current;

  const base: ViewStyle = {
    backgroundColor: t.cardSoft,
    borderRadius: radius.lg,
    padding: padded ? spacing.base : 0,
    borderColor: t.border,
    borderWidth: 1,
    ...(variant === 'raised'
      ? neuShadow.outsetStrong(theme)
      : neuShadow.outsetSoft(theme)),
  };

  // En dark mode también pintamos un highlight superior con un overlay
  // sutil para reforzar la sensación de relieve.
  const highlight: ViewStyle = theme === 'dark' ? {
    borderTopColor: 'rgba(255,255,255,0.06)',
    borderLeftColor: 'rgba(255,255,255,0.04)',
  } : {
    borderTopColor: '#FFFFFF',
    borderLeftColor: '#FFFFFF',
  };

  if (!onPress) {
    return (
      <View style={[base, highlight, style]} {...rest}>
        {children}
      </View>
    );
  }

  function pressIn() {
    Animated.spring(press, { toValue: 1, useNativeDriver: true, speed: 40, bounciness: 0 }).start();
  }
  function pressOut() {
    Animated.spring(press, { toValue: 0, useNativeDriver: true, speed: 18, bounciness: 4 }).start();
  }

  const transform = {
    transform: [
      { scale: press.interpolate({ inputRange: [0, 1], outputRange: [1, 0.985] }) },
    ],
    opacity: press.interpolate({ inputRange: [0, 1], outputRange: [1, 0.92] }),
  };

  return (
    <Pressable onPress={onPress} onPressIn={pressIn} onPressOut={pressOut}>
      <Animated.View style={[base, highlight, transform, style]}>
        {children}
      </Animated.View>
    </Pressable>
  );
}

export const neuStyles = StyleSheet.create({});
