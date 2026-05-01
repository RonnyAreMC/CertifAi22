/**
 * ShowcaseCarousel — feature carousel del login, mirror del `showcase-stage`
 * del web (`_auth_shell.html`). 4 slides con la mascota tiger_chase, tag
 * pill, headline y subtítulo. Auto-rotate + dots.
 */
import { useEffect, useRef, useState } from 'react';
import {
  Animated, Dimensions, Image, Pressable, StyleSheet, Text, View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { colors, radius, spacing, themed, typography } from '@/theme/tokens';
import { useTheme } from '@/stores/theme';

type Slide = {
  tag: string;
  icon: React.ComponentProps<typeof Ionicons>['name'];
  headline: string;
  sub: string;
};

const SLIDES: Slide[] = [
  {
    tag:      'UNEMI · CertifAI',
    icon:     'school',
    headline: 'Tu plataforma de\ncertificación académica.',
    sub:      'Centralizá tus eventos, certificados y aprendizajes. La IA te ayuda a aprovechar cada reunión.',
  },
  {
    tag:      'Tus diplomas',
    icon:     'ribbon',
    headline: 'Cada certificado, en un solo lugar.',
    sub:      'Descargalo en PDF o compartí un enlace público que cualquiera puede verificar al instante.',
  },
  {
    tag:      'Inteligencia artificial',
    icon:     'sparkles',
    headline: 'Resúmenes y cuestionarios automáticos.',
    sub:      'La IA prepara los puntos clave de cada reunión y un cuestionario para repasar lo aprendido.',
  },
  {
    tag:      'Eventos para ti',
    icon:     'compass',
    headline: 'Eventos pensados a tu medida.',
    sub:      'Recomendaciones según tu historial. Te inscribes con un clic.',
  },
];

const { width: SW } = Dimensions.get('window');

export function ShowcaseCarousel({ height = 280 }: { height?: number }) {
  const [index, setIndex] = useState(0);
  const t = themed(useTheme());
  const fade = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    const timer = setInterval(() => {
      Animated.sequence([
        Animated.timing(fade, { toValue: 0, duration: 280, useNativeDriver: true }),
        Animated.timing(fade, { toValue: 1, duration: 320, useNativeDriver: true }),
      ]).start();
      // El cambio de índice ocurre justo al final del fade-out
      setTimeout(() => setIndex((i) => (i + 1) % SLIDES.length), 280);
    }, 5000);
    return () => clearInterval(timer);
  }, []);

  const slide = SLIDES[index];

  return (
    <View style={[styles.wrap, { height }]}>
      <Animated.View style={[styles.slide, { opacity: fade }]}>
        {/* Mascota */}
        <View style={styles.mascotWrap}>
          <Image
            source={require('../../assets/tiger_chase_loader.png')}
            style={styles.mascot}
            resizeMode="contain"
          />
        </View>

        {/* Tag */}
        <View style={[styles.tag, { borderColor: t.border, backgroundColor: 'rgba(245,136,48,0.10)' }]}>
          <Ionicons name={slide.icon} size={11} color={colors.brand} />
          <Text style={styles.tagText}>{slide.tag}</Text>
        </View>

        {/* Headline */}
        <Text style={[styles.headline, { color: t.text }]} numberOfLines={2}>
          {slide.headline}
        </Text>

        {/* Sub */}
        <Text style={[styles.sub, { color: t.textMuted }]} numberOfLines={2}>
          {slide.sub}
        </Text>
      </Animated.View>

      {/* Dots */}
      <View style={styles.dots}>
        {SLIDES.map((_, i) => (
          <Pressable
            key={i}
            onPress={() => {
              Animated.sequence([
                Animated.timing(fade, { toValue: 0, duration: 200, useNativeDriver: true }),
                Animated.timing(fade, { toValue: 1, duration: 220, useNativeDriver: true }),
              ]).start();
              setTimeout(() => setIndex(i), 200);
            }}
            hitSlop={6}
          >
            <View style={[
              styles.dot,
              i === index ? { width: 22, backgroundColor: colors.brand } : { backgroundColor: t.border },
            ]} />
          </Pressable>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    width: '100%',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: spacing.lg,
  },
  slide: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    width: '100%',
  },
  mascotWrap: { marginBottom: spacing.sm },
  mascot: { width: 100, height: 100 },

  tag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: spacing.md,
    paddingVertical: 5,
    borderRadius: radius.full,
    borderWidth: 1,
  },
  tagText: {
    color: colors.brand,
    fontSize: typography.xs,
    fontWeight: typography.black,
    letterSpacing: 1.2,
    textTransform: 'uppercase',
  },

  headline: {
    fontSize: typography.lg,
    fontWeight: typography.black,
    letterSpacing: -0.4,
    textAlign: 'center',
    marginTop: spacing.sm,
    lineHeight: typography.lg * 1.25,
    paddingHorizontal: spacing.md,
  },
  sub: {
    fontSize: typography.sm,
    textAlign: 'center',
    marginTop: spacing.xs,
    lineHeight: typography.sm * 1.45,
    paddingHorizontal: spacing.md,
  },

  dots: {
    flexDirection: 'row',
    gap: 6,
    marginTop: spacing.base,
  },
  dot: { width: 8, height: 8, borderRadius: radius.full },
});
