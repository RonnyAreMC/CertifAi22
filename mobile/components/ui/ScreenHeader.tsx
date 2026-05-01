/**
 * ScreenHeader — header consistente con back button estilo iOS opcional,
 * eyebrow (uppercase), título grande y subtítulo. Soporta título con
 * gradiente animado vía `gradientTitle`. Reactivo al tema.
 */
import { Pressable, StyleSheet, Text, View, type ViewStyle } from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { colors, spacing, themed, typography } from '@/theme/tokens';
import { useTheme } from '@/stores/theme';
import { GradientText } from './GradientText';

type Props = {
  eyebrow?: string;
  title: string;
  subtitle?: string;
  canGoBack?: boolean;
  backLabel?: string;
  gradientTitle?: boolean;
  rightSlot?: React.ReactNode;
  style?: ViewStyle;
};

export function ScreenHeader({
  eyebrow, title, subtitle,
  canGoBack = false, backLabel = 'Atrás',
  gradientTitle = false,
  rightSlot,
  style,
}: Props) {
  const theme = useTheme();
  const t = themed(theme);

  return (
    <View style={[styles.wrap, style]}>
      <View style={styles.topRow}>
        {canGoBack ? (
          <Pressable
            onPress={() => router.back()}
            style={({ pressed }) => [styles.back, pressed && { opacity: 0.6 }]}
            hitSlop={10}
          >
            <Ionicons name="chevron-back" size={26} color={colors.brand} style={{ marginLeft: -4 }} />
            <Text style={[styles.backLabel, { color: colors.brand }]}>{backLabel}</Text>
          </Pressable>
        ) : (
          <View style={{ flex: 1 }} />
        )}
        {rightSlot ? <View style={styles.right}>{rightSlot}</View> : null}
      </View>

      {eyebrow ? <Text style={[styles.eyebrow, { color: colors.brand }]}>{eyebrow}</Text> : null}
      {gradientTitle ? (
        <GradientText style={[styles.title, { color: t.text }]}>{title}</GradientText>
      ) : (
        <Text style={[styles.title, { color: t.text }]}>{title}</Text>
      )}
      {subtitle ? <Text style={[styles.subtitle, { color: t.textMuted }]}>{subtitle}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    paddingHorizontal: spacing.xl,
    paddingTop: spacing.sm,
    paddingBottom: spacing.base,
  },
  topRow: {
    flexDirection: 'row',
    alignItems: 'center',
    minHeight: 32,
    marginBottom: spacing.sm,
  },
  back: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  backLabel: {
    fontSize: typography.base,
    fontWeight: typography.medium,
  },
  right: {
    marginLeft: 'auto',
  },
  eyebrow: {
    fontSize: typography.xs,
    fontWeight: typography.black,
    letterSpacing: 2,
  },
  title: {
    fontSize: typography.xxl,
    fontWeight: typography.black,
    letterSpacing: -0.6,
    lineHeight: typography.xxl * 1.1,
    marginTop: spacing.xs,
  },
  subtitle: {
    fontSize: typography.sm,
    marginTop: spacing.xs,
  },
});
