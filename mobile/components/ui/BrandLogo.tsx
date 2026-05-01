/**
 * BrandLogo — el logo "certif·ai" del web replicado en mobile:
 * `certif` en color sólido + `ai` con gradiente naranja → navy.
 *
 * Usa MaskedView + LinearGradient para el efecto de gradient text en la
 * partícula `ai`, igual que `.brand-ai` en `home.html`.
 */
import { Text, View, type TextStyle, type ViewStyle, type StyleProp } from 'react-native';
import MaskedView from '@react-native-masked-view/masked-view';
import { LinearGradient } from 'expo-linear-gradient';

import { colors, themed, typography } from '@/theme/tokens';
import { useTheme } from '@/stores/theme';

type Props = {
  size?: number;
  style?: StyleProp<ViewStyle>;
};

export function BrandLogo({ size = 28, style }: Props) {
  const t = themed(useTheme());
  const baseStyle: TextStyle = {
    fontSize: size,
    fontWeight: typography.black,
    letterSpacing: -size * 0.025,
    lineHeight: size * 1.05,
  };

  return (
    <View style={[{ flexDirection: 'row', alignItems: 'baseline' }, style]}>
      <Text style={[baseStyle, { color: t.text }]}>certif</Text>
      <MaskedView
        style={{ height: size * 1.05 }}
        maskElement={
          <Text style={[baseStyle, { color: 'black' }]}>ai</Text>
        }
      >
        <LinearGradient
          colors={[colors.brand, '#E8721C', colors.accent] as [string, string, string]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={{ flex: 1 }}
        >
          <Text style={[baseStyle, { opacity: 0 }]}>ai</Text>
        </LinearGradient>
      </MaskedView>
    </View>
  );
}
