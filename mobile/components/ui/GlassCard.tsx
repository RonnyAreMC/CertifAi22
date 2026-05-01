/**
 * GlassCard — neumorfismo mirror del `.nm-card` del web (auth_shell.html).
 *
 * Estilo web replicado:
 *   background: rgba(255,255,255,0.85)
 *   border:     1px solid rgba(255,255,255,0.85)
 *   border-radius: 24px
 *   box-shadow:
 *     inset 0 1px 0 rgba(255,255,255,0.95)         (highlight superior)
 *     inset 0 -1px 0 rgba(15,23,42,0.04)            (sombra inset inferior)
 *     0 24px 60px -16px rgba(15,23,42,0.18)         (sombra outset suave)
 *
 * En RN no existe `inset shadow`, pero usamos:
 *   - Outer wrapper con shadow (sin overflow:hidden — no recorte iOS)
 *   - Inner con borderRadius + border
 *   - 2 Views absolutas como "highlight" arriba + "shadow inset" abajo (1px alto)
 *   - En iOS sumamos BlurView real para el saturate(180%) feel
 */
import { useRef } from 'react';
import {
  Animated, Platform, Pressable, StyleSheet, View,
  type ViewProps, type ViewStyle,
} from 'react-native';
import { BlurView } from 'expo-blur';

import { spacing } from '@/theme/tokens';
import { useTheme } from '@/stores/theme';

type Props = ViewProps & {
  onPress?: () => void;
  padded?: boolean;
  intensity?: number;
};

const NM_RADIUS = 18;   // ligeramente menos que 24 del web (en mobile 24 es muy grande)

export function GlassCard({
  onPress, padded = true, intensity, style, children, ...rest
}: Props) {
  const theme = useTheme();
  const press = useRef(new Animated.Value(0)).current;
  const isDark = theme === 'dark';

  // En iOS el BlurView ya provee cuerpo → bg muy translúcido.
  // En Android no hay blur real → bg sólido translúcido (mirror del web .nm-card).
  const isAndroid = Platform.OS === 'android';
  const bg = isDark
    ? (isAndroid ? 'rgba(22,32,84,0.78)' : 'rgba(22,32,84,0.20)')
    : (isAndroid ? 'rgba(255,255,255,0.85)' : 'rgba(255,255,255,0.20)');

  const borderColor = isDark
    ? 'rgba(255,255,255,0.12)'
    : 'rgba(255,255,255,0.85)';

  // inset 0 1px 0 white95 → fina línea blanca arriba
  const insetTop = isDark ? 'rgba(255,255,255,0.10)' : 'rgba(255,255,255,0.95)';
  // inset 0 -1px 0 dark4 → fina línea oscura abajo (sombra inset)
  const insetBottom = isDark ? 'rgba(0,0,0,0.30)' : 'rgba(15,23,42,0.04)';

  // 0 24px 60px -16px rgba(15,23,42,0.18) → sombra grande suave
  const outerStyle: ViewStyle = {
    borderRadius: NM_RADIUS,
    backgroundColor: 'transparent',
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: isDark ? 0.45 : 0.10,
    shadowRadius: 24,
    elevation: 8,
    alignSelf: 'stretch',
  };

  const innerStyle: ViewStyle = {
    borderRadius: NM_RADIUS,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor,
    backgroundColor: bg,
    alignSelf: 'stretch',                              // ← clave: hereda el ancho del outer
    width: '100%',
  };

  const innerPad = padded ? { padding: spacing.base } : null;

  function pressIn() {
    if (!onPress) return;
    Animated.spring(press, { toValue: 1, useNativeDriver: true, speed: 40, bounciness: 0 }).start();
  }
  function pressOut() {
    if (!onPress) return;
    Animated.spring(press, { toValue: 0, useNativeDriver: true, speed: 18, bounciness: 4 }).start();
  }

  const transform = {
    opacity: press.interpolate({ inputRange: [0, 1], outputRange: [1, 0.85] }),
  };

  const card = (
    <Animated.View style={[outerStyle, transform, style]} {...(onPress ? {} : rest)}>
      <View style={innerStyle}>
        {/* Solo iOS: BlurView fuerte (chromeMaterial = estilo Control Center) */}
        {Platform.OS === 'ios' ? (
          <BlurView
            intensity={intensity ?? 100}
            tint={isDark ? 'systemChromeMaterialDark' : 'systemChromeMaterialLight'}
            style={StyleSheet.absoluteFill}
          />
        ) : null}

        {/* inset 0 1px 0 — highlight blanco arriba (1px) */}
        <View style={[styles.insetTop, { backgroundColor: insetTop }]} pointerEvents="none" />
        {/* inset 0 -1px 0 — sombra inset abajo (1px) */}
        <View style={[styles.insetBottom, { backgroundColor: insetBottom }]} pointerEvents="none" />

        {/* Contenido */}
        <View style={innerPad}>{children}</View>
      </View>
    </Animated.View>
  );

  if (!onPress) return card;
  return (
    <Pressable
      onPress={onPress}
      onPressIn={pressIn}
      onPressOut={pressOut}
      style={{ alignSelf: 'stretch' }}
    >
      {card}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  insetTop:    { position: 'absolute', top: 0, left: 0, right: 0, height: 1 },
  insetBottom: { position: 'absolute', bottom: 0, left: 0, right: 0, height: 1 },
});
