/**
 * BettoLogo — avatar del agente IA "Betto" usando la imagen oficial
 * `tiger_chase_loader.png` (la mascota del producto, igual que el web).
 */
import { Image, View, type ViewStyle } from 'react-native';

type Props = {
  size?: number;
  style?: ViewStyle;
};

export function BettoLogo({ size = 40, style }: Props) {
  return (
    <View
      style={[
        {
          width: size,
          height: size,
          alignItems: 'center',
          justifyContent: 'center',
        },
        style,
      ]}
    >
      <Image
        source={require('../../assets/tiger_chase_loader.png')}
        style={{ width: size, height: size }}
        resizeMode="contain"
      />
    </View>
  );
}
