/**
 * BottomSheet — sheet modal estilo iOS que sube desde abajo, con backdrop
 * tap-to-dismiss y handle visual. Animación spring para que se sienta
 * nativo en iOS y Android.
 *
 *   <BottomSheet visible={open} onClose={() => setOpen(false)} title="Confirmar">
 *     <Text>...</Text>
 *     <View style={{flexDirection:'row',gap:8}}>
 *       <Button variant="ghost" onPress={onClose}>Cancelar</Button>
 *       <Button onPress={onConfirm}>Confirmar</Button>
 *     </View>
 *   </BottomSheet>
 */
import { useEffect, useRef } from 'react';
import {
  Animated, Dimensions, Modal, Pressable, StyleSheet, Text, View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';

import { radius, spacing, themed, typography } from '@/theme/tokens';
import { useTheme } from '@/stores/theme';

type Props = {
  visible: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
};

export function BottomSheet({ visible, onClose, title, children }: Props) {
  const slide = useRef(new Animated.Value(0)).current;
  const insets = useSafeAreaInsets();
  const t = themed(useTheme());

  useEffect(() => {
    Animated.spring(slide, {
      toValue: visible ? 1 : 0,
      useNativeDriver: true,
      speed: 16,
      bounciness: 5,
    }).start();
  }, [visible]);

  const sheetTransform = {
    transform: [
      { translateY: slide.interpolate({ inputRange: [0, 1], outputRange: [Dimensions.get('window').height, 0] }) },
    ],
  };
  const backdropOpacity = { opacity: slide.interpolate({ inputRange: [0, 1], outputRange: [0, 0.5] }) };

  return (
    <Modal
      visible={visible}
      transparent
      animationType="none"
      onRequestClose={onClose}
      statusBarTranslucent
    >
      {/* Backdrop animado */}
      <Animated.View style={[styles.backdrop, backdropOpacity]} pointerEvents={visible ? 'auto' : 'none'}>
        <Pressable style={StyleSheet.absoluteFill} onPress={onClose} />
      </Animated.View>

      {/* Sheet */}
      <View style={styles.sheetWrap} pointerEvents="box-none">
        <Animated.View
          style={[
            styles.sheet,
            { backgroundColor: t.cardSoft, paddingBottom: insets.bottom + spacing.lg, borderColor: t.border },
            sheetTransform,
          ]}
        >
          {/* Handle visual */}
          <View style={styles.handleWrap}>
            <View style={[styles.handle, { backgroundColor: t.textMuted, opacity: 0.4 }]} />
          </View>

          {title ? (
            <View style={styles.titleRow}>
              <Text style={[styles.title, { color: t.text }]}>{title}</Text>
              <Pressable onPress={onClose} hitSlop={10}>
                <Ionicons name="close" size={22} color={t.textMuted} />
              </Pressable>
            </View>
          ) : null}

          <View style={styles.content}>{children}</View>
        </Animated.View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: '#000',
  },
  sheetWrap: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: 'flex-end',
  },
  sheet: {
    borderTopLeftRadius: radius.xxl,
    borderTopRightRadius: radius.xxl,
    paddingHorizontal: spacing.xl,
    paddingTop: spacing.sm,
    borderTopWidth: 1,
    borderLeftWidth: 1,
    borderRightWidth: 1,
  },
  handleWrap: {
    alignItems: 'center',
    paddingVertical: spacing.sm,
  },
  handle: {
    width: 38, height: 5, borderRadius: 3,
  },
  titleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingBottom: spacing.base,
  },
  title: {
    fontSize: typography.lg,
    fontWeight: typography.black,
    letterSpacing: -0.3,
  },
  content: {
    paddingTop: spacing.sm,
  },
});
