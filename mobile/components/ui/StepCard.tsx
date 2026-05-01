/**
 * StepCard — paso numerado con título + descripción (+ icono opcional).
 * El badge usa LinearGradient diagonal para un acabado más rico
 * (en vez de un color plano). Soporta tonos: brand · navy · info · success ·
 * violet · warning.
 *
 *   <StepCard number={1} title="Asiste al evento" text="..." />
 *   <StepCard number={2} color="navy" title="..." icon="ribbon" />
 */
import { StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';

import {
  brandScale, navyScale, radius, shadows, spacing, themed, typography,
} from '@/theme/tokens';
import { useTheme } from '@/stores/theme';

type Color = 'brand' | 'navy' | 'info' | 'success' | 'violet' | 'warning';

const GRADIENTS: Record<Color, [string, string]> = {
  brand:   [brandScale[400], brandScale[700]],
  navy:    [navyScale[500],  navyScale[800]],
  info:    ['#3B82F6',       '#1D4ED8'],
  success: ['#10B981',       '#047857'],
  violet:  ['#A855F7',       '#7C3AED'],
  warning: ['#F59E0B',       '#B45309'],
};

type Props = {
  number?: number | string;
  icon?: React.ComponentProps<typeof Ionicons>['name'];
  title: string;
  text?: string;
  color?: Color;
};

export function StepCard({ number, icon, title, text, color = 'brand' }: Props) {
  const t = themed(useTheme());
  const gradient = GRADIENTS[color];

  return (
    <View style={[
      styles.wrap,
      { backgroundColor: t.cardSoft, borderColor: t.border },
      shadows.sm,
    ]}>
      <LinearGradient
        colors={gradient}
        start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
        style={styles.badge}
      >
        {icon ? (
          <Ionicons name={icon} size={20} color="#FFFFFF" />
        ) : (
          <Text style={styles.badgeText}>{number ?? '·'}</Text>
        )}
      </LinearGradient>
      <View style={styles.body}>
        <Text style={[styles.title, { color: t.text }]}>{title}</Text>
        {text ? (
          <Text style={[styles.text, { color: t.textMuted }]}>{text}</Text>
        ) : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    flexDirection: 'row',
    gap: spacing.base,
    padding: spacing.base,
    borderRadius: radius.lg,
    borderWidth: 1,
  },
  badge: {
    width: 44, height: 44,
    borderRadius: radius.md,
    alignItems: 'center', justifyContent: 'center',
    flexShrink: 0,
    ...shadows.sm,
  },
  badgeText: {
    color: '#FFFFFF',
    fontWeight: typography.black,
    fontSize: typography.md,
  },
  body: { flex: 1 },
  title: {
    fontWeight: typography.bold,
    fontSize: typography.base,
    marginBottom: 2,
  },
  text: {
    fontSize: typography.sm,
    lineHeight: typography.sm * 1.45,
  },
});
