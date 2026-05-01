/**
 * Button — variantes inspiradas en design systems institucionales.
 *
 *   <Button variant="filled"  tone="brand"   onPress={...}>Entrar</Button>
 *   <Button variant="outline" tone="navy"    iconLeft={<Icon name="..." />}>Ver</Button>
 *   <Button variant="soft"    tone="success">Guardar</Button>
 *   <Button variant="ghost"   tone="danger"  onPress={...}>Cancelar</Button>
 *   <Button variant="link"    tone="brand"   onPress={...}>Recordar</Button>
 *
 * Tonos disponibles: brand · navy · success · danger · warning · info · neutral
 * Tamaños:           sm · md · lg
 */
import { useRef } from 'react';
import {
  ActivityIndicator, Animated, Pressable, StyleSheet, Text,
  View, type ViewStyle, type TextStyle,
} from 'react-native';

import {
  brandScale, dangerScale, infoScale, navyScale, neutralScale, radius,
  shadows, spacing, successScale, typography, warningScale,
} from '@/theme/tokens';
import { useTheme } from '@/stores/theme';

// ── Tipos ────────────────────────────────────────────────────────
export type ButtonVariant = 'filled' | 'outline' | 'soft' | 'ghost' | 'link';
export type ButtonTone =
  | 'brand' | 'navy' | 'success' | 'danger' | 'warning' | 'info' | 'neutral';
export type ButtonSize = 'sm' | 'md' | 'lg';

type Props = {
  children: React.ReactNode;
  onPress?: () => void;
  variant?: ButtonVariant;
  tone?: ButtonTone;
  size?: ButtonSize;
  disabled?: boolean;
  loading?: boolean;
  fullWidth?: boolean;
  iconLeft?: React.ReactNode;
  iconRight?: React.ReactNode;
  style?: ViewStyle;
};

// ── Lookup de escalas por tone ───────────────────────────────────
type Scale = Record<number, string>;
const SCALES: Record<ButtonTone, Scale> = {
  brand:   brandScale,
  navy:    navyScale,
  success: successScale,
  danger:  dangerScale,
  warning: warningScale,
  info:    infoScale,
  neutral: neutralScale,
};

// ── Sizes ────────────────────────────────────────────────────────
const SIZE = {
  sm: { paddingV: spacing.xs + 2, paddingH: spacing.md, font: typography.sm,   icon: 14, gap: 6 },
  md: { paddingV: spacing.sm + 2, paddingH: spacing.base, font: typography.base, icon: 16, gap: 8 },
  lg: { paddingV: spacing.md + 2, paddingH: spacing.lg, font: typography.md,   icon: 18, gap: 10 },
} as const;

// ── Estilos por variant + tone ───────────────────────────────────
function getColors(
  variant: ButtonVariant,
  tone: ButtonTone,
  disabled: boolean,
  theme: 'light' | 'dark',
) {
  const ramp = SCALES[tone];
  const base = ramp[500];
  // Para outline/ghost/link en dark mode con tonos oscuros (navy, neutral)
  // usamos un nivel más claro del ramp para que el texto se lea sobre el bg.
  const isDarkTone = tone === 'navy' || tone === 'neutral';
  const onSurface = theme === 'dark' && isDarkTone
    ? (ramp[200] ?? ramp[300] ?? base)
    : base;

  // Para soft, en dark mode el bg debe ser menos saturado para no
  // chocar con el bg de pantalla.
  const softBg = theme === 'dark'
    ? `${base}26`            // ~15% alpha sobre el color base
    : (ramp[100] ?? ramp[200] ?? base);
  const softText = theme === 'dark'
    ? (ramp[200] ?? ramp[300] ?? base)
    : (ramp[700] ?? ramp[600] ?? base);

  if (disabled) {
    return {
      bg: variant === 'filled' ? neutralScale[200] : 'transparent',
      border: variant === 'outline' ? neutralScale[300] : 'transparent',
      text: neutralScale[400],
    };
  }

  switch (variant) {
    case 'filled':
      return { bg: base, border: 'transparent', text: '#FFFFFF' };
    case 'outline':
      return { bg: 'transparent', border: onSurface, text: onSurface };
    case 'soft':
      return { bg: softBg, border: 'transparent', text: softText };
    case 'ghost':
      return { bg: 'transparent', border: 'transparent', text: onSurface };
    case 'link':
      return { bg: 'transparent', border: 'transparent', text: onSurface };
  }
}

// ── Componente ───────────────────────────────────────────────────
export function Button({
  children, onPress,
  variant = 'filled', tone = 'brand', size = 'md',
  disabled = false, loading = false, fullWidth = false,
  iconLeft, iconRight, style,
}: Props) {
  const press = useRef(new Animated.Value(0)).current;
  const theme = useTheme();
  const isInactive = disabled || loading;
  const c = getColors(variant, tone, isInactive, theme);
  const s = SIZE[size];

  function pressIn() {
    Animated.spring(press, {
      toValue: 1, useNativeDriver: true, speed: 40, bounciness: 0,
    }).start();
  }
  function pressOut() {
    Animated.spring(press, {
      toValue: 0, useNativeDriver: true, speed: 22, bounciness: 4,
    }).start();
  }

  const transform = {
    transform: [
      { scale: press.interpolate({ inputRange: [0, 1], outputRange: [1, 0.97] }) },
    ],
    opacity: press.interpolate({ inputRange: [0, 1], outputRange: [1, 0.85] }),
  };

  const containerStyle: ViewStyle = {
    backgroundColor: c.bg,
    borderColor: c.border,
    borderWidth: variant === 'outline' ? 1.5 : 0,
    borderRadius: variant === 'link' ? 0 : radius.md,
    paddingVertical: variant === 'link' ? 0 : s.paddingV,
    paddingHorizontal: variant === 'link' ? 0 : s.paddingH,
    alignSelf: fullWidth ? 'stretch' : 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: s.gap,
    ...(variant === 'filled' && tone === 'brand' && !isInactive ? shadows.brand : null),
  };

  const textStyle: TextStyle = {
    color: c.text,
    fontSize: s.font,
    fontWeight: typography.bold,
    letterSpacing: 0.2,
    textDecorationLine: variant === 'link' ? 'underline' : 'none',
  };

  return (
    <Pressable
      disabled={isInactive}
      onPress={onPress}
      onPressIn={pressIn}
      onPressOut={pressOut}
      style={({ pressed }) => [
        fullWidth ? { alignSelf: 'stretch' } : { alignSelf: 'flex-start' },
        style,
      ]}
    >
      <Animated.View style={[containerStyle, transform]}>
        {loading ? (
          <ActivityIndicator size="small" color={c.text} />
        ) : iconLeft ? (
          <View style={{ width: s.icon, height: s.icon, alignItems: 'center', justifyContent: 'center' }}>
            {iconLeft}
          </View>
        ) : null}
        <Text style={textStyle}>{children}</Text>
        {!loading && iconRight ? (
          <View style={{ width: s.icon, height: s.icon, alignItems: 'center', justifyContent: 'center' }}>
            {iconRight}
          </View>
        ) : null}
      </Animated.View>
    </Pressable>
  );
}

// ── Estilos auxiliares ───────────────────────────────────────────
// (mantenido exportado para uso interno si se necesita componer)
export const buttonStyles = StyleSheet.create({
  // placeholder — todos los styles van inline para soportar tone dinámico
});
