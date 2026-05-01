/**
 * Badge — pill compacto para estados (Inscrito, Asistí, Disponible, Lider…).
 *
 *   <Badge tone="brand"   dot>Plan Free</Badge>
 *   <Badge tone="success" iconLeft={<Icon ... />}>Asistido</Badge>
 *   <Badge tone="navy"    variant="solid">Líder</Badge>
 */
import { StyleSheet, Text, View, type ViewStyle, type TextStyle } from 'react-native';

import {
  brandScale, dangerScale, infoScale, navyScale, neutralScale, radius,
  successScale, warningScale,
} from '@/theme/tokens';

export type BadgeTone =
  | 'brand' | 'navy' | 'success' | 'danger' | 'warning' | 'info' | 'neutral';
export type BadgeVariant = 'soft' | 'solid' | 'outline';
export type BadgeSize = 'sm' | 'md';

type Scale = Record<number, string>;
const SCALES: Record<BadgeTone, Scale> = {
  brand: brandScale, navy: navyScale, success: successScale,
  danger: dangerScale, warning: warningScale, info: infoScale, neutral: neutralScale,
};

const SIZE = {
  sm: { paddingV: 2, paddingH: 8,  font: 10, gap: 4, dot: 6,  icon: 11 },
  md: { paddingV: 4, paddingH: 10, font: 12, gap: 6, dot: 7,  icon: 13 },
} as const;

type Props = {
  children: React.ReactNode;
  tone?: BadgeTone;
  variant?: BadgeVariant;
  size?: BadgeSize;
  dot?: boolean;
  iconLeft?: React.ReactNode;
  style?: ViewStyle;
};

export function Badge({
  children, tone = 'brand', variant = 'soft', size = 'sm',
  dot = false, iconLeft, style,
}: Props) {
  const ramp = SCALES[tone];
  const base = ramp[500];
  const soft = ramp[100] ?? ramp[200] ?? base;
  const onSolid = '#FFFFFF';
  const onSoft = ramp[700] ?? ramp[600] ?? base;

  const s = SIZE[size];

  const containerStyle: ViewStyle = {
    paddingVertical: s.paddingV,
    paddingHorizontal: s.paddingH,
    borderRadius: radius.full,
    flexDirection: 'row',
    alignItems: 'center',
    gap: s.gap,
    alignSelf: 'flex-start',
    backgroundColor: variant === 'solid' ? base : variant === 'soft' ? soft : 'transparent',
    borderColor: variant === 'outline' ? base : 'transparent',
    borderWidth: variant === 'outline' ? 1 : 0,
  };
  const fg = variant === 'solid' ? onSolid : variant === 'soft' ? onSoft : base;

  const textStyle: TextStyle = {
    color: fg,
    fontSize: s.font,
    fontWeight: '700',
    letterSpacing: 0.4,
    textTransform: 'uppercase',
  };

  return (
    <View style={[containerStyle, style]}>
      {dot ? <View style={[styles.dot, { backgroundColor: fg, width: s.dot, height: s.dot }]} /> : null}
      {iconLeft ? <View style={{ width: s.icon, height: s.icon, alignItems: 'center', justifyContent: 'center' }}>{iconLeft}</View> : null}
      <Text style={textStyle}>{children}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  dot: { borderRadius: radius.full },
});
