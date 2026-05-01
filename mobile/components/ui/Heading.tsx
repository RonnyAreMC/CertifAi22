/**
 * Heading semántico con variantes display/title/heading y niveles 1–4.
 * Equivalente al `<Heading>` del design system web (tareas/eneritzdev).
 */
import { Text, type StyleProp, type TextStyle } from 'react-native';

import { colors, typography } from '@/theme/tokens';

type Variant = 'display' | 'title' | 'heading';
type Level = 1 | 2 | 3 | 4;

type Props = {
  level?: Level;
  variant?: Variant;
  style?: StyleProp<TextStyle>;
  numberOfLines?: number;
  children: React.ReactNode;
};

const SIZES: Record<Level, Record<Variant, number>> = {
  1: { display: typography.huge,  title: typography.xxl, heading: typography.xl },
  2: { display: typography.xxl,   title: typography.xl,  heading: typography.lg },
  3: { display: typography.xl,    title: typography.lg,  heading: typography.md },
  4: { display: typography.lg,    title: typography.md,  heading: typography.base },
};

const SPACING: Record<Level, number> = { 1: -1.0, 2: -0.6, 3: -0.3, 4: -0.2 };

export function Heading({
  level = 1, variant = 'display', style, numberOfLines, children,
}: Props) {
  return (
    <Text
      numberOfLines={numberOfLines}
      style={[
        {
          fontSize: SIZES[level][variant],
          fontWeight: typography.black,
          color: colors.white,
          letterSpacing: SPACING[level],
          lineHeight: SIZES[level][variant] * 1.1,
        },
        style,
      ]}
    >
      {children}
    </Text>
  );
}
