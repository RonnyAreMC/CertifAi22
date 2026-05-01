/**
 * Toast — notificación flotante con icono, animación slide-in/out.
 *
 *   const toast = useToast();
 *   toast.success('Te inscribiste al evento');
 *   toast.error('No pudimos conectarte');
 *   toast.show({ tone: 'brand', title: '¡Listo!', message: '...' });
 *
 * Montar <ToastProvider> una vez en el layout raíz.
 */
import {
  createContext, useCallback, useContext, useEffect, useRef, useState,
} from 'react';
import {
  Animated, Dimensions, StyleSheet, Text, View, type ViewStyle,
} from 'react-native';

import {
  brandScale, dangerScale, infoScale, navyScale, neutralScale, radius,
  shadows, spacing, successScale, typography, warningScale,
} from '@/theme/tokens';

// ── Tipos ────────────────────────────────────────────────────────
type Tone = 'brand' | 'success' | 'danger' | 'warning' | 'info' | 'navy' | 'neutral';

type ToastInput = {
  tone?: Tone;
  title?: string;
  message: string;
  duration?: number;
  icon?: React.ReactNode;
};

type ToastInternal = ToastInput & { id: number };

type ToastApi = {
  show:    (t: ToastInput) => void;
  success: (msg: string, title?: string) => void;
  error:   (msg: string, title?: string) => void;
  info:    (msg: string, title?: string) => void;
  warning: (msg: string, title?: string) => void;
};

const ToastContext = createContext<ToastApi | null>(null);
let nextId = 1;

type Scale = Record<number, string>;
const SCALES: Record<Tone, Scale> = {
  brand: brandScale, navy: navyScale, success: successScale,
  danger: dangerScale, warning: warningScale, info: infoScale, neutral: neutralScale,
};

const ICON_GLYPH: Record<Tone, string> = {
  brand: '✦', success: '✓', danger: '!', warning: '⚠',
  info: 'ℹ', navy: '✦', neutral: '·',
};

// ── Provider ─────────────────────────────────────────────────────
export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<ToastInternal[]>([]);

  const dismiss = useCallback((id: number) => {
    setItems((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const show = useCallback((t: ToastInput) => {
    const id = nextId++;
    setItems((prev) => [...prev, { id, tone: 'brand', duration: 3200, ...t }]);
  }, []);

  const api: ToastApi = {
    show,
    success: (msg, title) => show({ tone: 'success', title, message: msg }),
    error:   (msg, title) => show({ tone: 'danger',  title, message: msg }),
    info:    (msg, title) => show({ tone: 'info',    title, message: msg }),
    warning: (msg, title) => show({ tone: 'warning', title, message: msg }),
  };

  return (
    <ToastContext.Provider value={api}>
      {children}
      <View pointerEvents="box-none" style={styles.host}>
        {items.map((t, idx) => (
          <ToastItem key={t.id} item={t} index={idx} onClose={() => dismiss(t.id)} />
        ))}
      </View>
    </ToastContext.Provider>
  );
}

// ── Item con animación ───────────────────────────────────────────
function ToastItem({
  item, index, onClose,
}: { item: ToastInternal; index: number; onClose: () => void }) {
  const slide = useRef(new Animated.Value(0)).current;
  const tone = item.tone ?? 'brand';
  const ramp = SCALES[tone];

  useEffect(() => {
    Animated.spring(slide, {
      toValue: 1, useNativeDriver: true, speed: 14, bounciness: 6,
    }).start();
    const timer = setTimeout(() => {
      Animated.timing(slide, {
        toValue: 0, duration: 200, useNativeDriver: true,
      }).start(({ finished }) => { if (finished) onClose(); });
    }, item.duration ?? 3200);
    return () => clearTimeout(timer);
  }, []);

  const transform = {
    transform: [
      { translateY: slide.interpolate({ inputRange: [0, 1], outputRange: [-20, 0] }) },
      { scale:      slide.interpolate({ inputRange: [0, 1], outputRange: [0.96, 1] }) },
    ],
    opacity: slide,
  };

  const containerStyle: ViewStyle = {
    backgroundColor: '#1A2A52',                 // dark surface
    borderColor: ramp[500],
    borderLeftWidth: 4,
    borderRadius: radius.lg,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.base,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    width: Dimensions.get('window').width - spacing.xl * 2,
    marginTop: index === 0 ? 0 : spacing.sm,
    ...shadows.lg,
  };

  return (
    <Animated.View style={[containerStyle, transform]}>
      <View style={[styles.iconBox, { backgroundColor: ramp[500] }]}>
        <Text style={styles.iconGlyph}>{ICON_GLYPH[tone]}</Text>
      </View>
      <View style={{ flex: 1 }}>
        {item.title ? <Text style={styles.title}>{item.title}</Text> : null}
        <Text style={[styles.message, !item.title && { fontWeight: typography.semibold }]} numberOfLines={3}>
          {item.message}
        </Text>
      </View>
    </Animated.View>
  );
}

// ── Hook ─────────────────────────────────────────────────────────
export function useToast(): ToastApi {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error('useToast() debe usarse dentro de <ToastProvider>');
  }
  return ctx;
}

// ── Estilos ──────────────────────────────────────────────────────
const styles = StyleSheet.create({
  host: {
    position: 'absolute',
    top: 60,
    left: 0, right: 0,
    alignItems: 'center',
    paddingHorizontal: spacing.xl,
    zIndex: 9999,
  },
  iconBox: {
    width: 30, height: 30, borderRadius: radius.full,
    alignItems: 'center', justifyContent: 'center',
  },
  iconGlyph: { color: '#FFFFFF', fontSize: 16, fontWeight: '900' },
  title:   { color: '#FFFFFF', fontSize: typography.sm,  fontWeight: typography.black, marginBottom: 1 },
  message: { color: neutralScale[300], fontSize: typography.sm, fontWeight: typography.medium },
});
