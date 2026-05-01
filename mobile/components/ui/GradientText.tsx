/**
 * Texto con gradiente que se mueve, equivalente a `text-gradient-animated`
 * del design system web (tareas/eneritzdev). El gradiente recorre el texto
 * en bucle infinito usando MaskedView + LinearGradient + Reanimated.
 */
import { useEffect } from 'react';
import { Text, type TextStyle, type StyleProp, View } from 'react-native';
import MaskedView from '@react-native-masked-view/masked-view';
import { LinearGradient } from 'expo-linear-gradient';
import Animated, {
  Easing, useAnimatedStyle, useSharedValue, withRepeat, withTiming,
} from 'react-native-reanimated';

import { colors } from '@/theme/tokens';

type Props = {
  children: string;
  style?: StyleProp<TextStyle>;
  /** Colores del gradiente (mín. 2). Por defecto naranja UNEMI ↔ tono claro. */
  gradient?: readonly string[];
  /** Duración del ciclo en ms. */
  duration?: number;
};

export function GradientText({
  children,
  style,
  gradient = colors.gradientTitle,
  duration = 4500,
}: Props) {
  const x = useSharedValue(0);

  useEffect(() => {
    x.value = withRepeat(
      withTiming(1, { duration, easing: Easing.linear }),
      -1,
      false,
    );
  }, [duration]);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: -x.value * 100 }],
  }));

  return (
    <MaskedView
      style={{ flexDirection: 'row' }}
      maskElement={
        <View style={{ backgroundColor: 'transparent' }}>
          <Text style={[style, { color: 'black' }]}>{children}</Text>
        </View>
      }
    >
      <Animated.View style={[{ width: '300%' }, animatedStyle]}>
        <LinearGradient
          colors={gradient as unknown as [string, string, ...string[]]}
          start={{ x: 0, y: 0.5 }}
          end={{ x: 1, y: 0.5 }}
        >
          <Text style={[style, { opacity: 0 }]}>{children}</Text>
        </LinearGradient>
      </Animated.View>
    </MaskedView>
  );
}
