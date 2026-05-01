/**
 * Design Tokens — paleta UNEMI con escalas completas (50–900).
 * Inspirado en patrones de design systems institucionales: cada hue tiene
 * su propio ramp (`brandScale[500]`, etc.) para usar tonos exactos en
 * filled / outline / soft / ghost. Los aliases simples (`colors.brand`)
 * mantienen compatibilidad con código existente.
 */

// ── Escalas (50 = más claro, 900 = más oscuro) ───────────────────
export const brandScale = {
  50:  '#FFF4EC',
  100: '#FFE0CC',
  200: '#FFC299',
  300: '#FFA366',
  400: '#FF8838',
  500: '#F58830',  // ← brand UNEMI (default)
  600: '#D97520',
  700: '#B25E15',
  800: '#8A480F',
  900: '#5C2F0A',
} as const;

export const navyScale = {
  50:  '#E7E9F2',
  100: '#C2C7DD',
  200: '#8E96B8',
  300: '#5C6695',
  400: '#2E3970',
  500: '#162054',  // ← accent UNEMI (default)
  600: '#101945',
  700: '#0C1335',
  800: '#080D26',
  900: '#040716',
} as const;

export const neutralScale = {
  50:  '#F8FAFC',
  100: '#F1F5F9',
  200: '#E2E8F0',
  300: '#CBD5E1',
  400: '#94A3B8',
  500: '#64748B',
  600: '#475569',
  700: '#334155',
  800: '#1E293B',
  900: '#0F172A',
} as const;

export const successScale = {
  50:  '#ECFDF5',
  100: '#D1FAE5',
  500: '#10B981',
  600: '#059669',
  700: '#047857',
} as const;

export const dangerScale = {
  50:  '#FEF2F2',
  100: '#FEE2E2',
  500: '#EF4444',
  600: '#DC2626',
  700: '#B91C1C',
} as const;

export const warningScale = {
  50:  '#FFFBEB',
  100: '#FEF3C7',
  500: '#F59E0B',
  600: '#D97706',
} as const;

export const infoScale = {
  50:  '#EFF6FF',
  100: '#DBEAFE',
  500: '#3B82F6',
  600: '#2563EB',
} as const;

// ── Colors: aliases simples (string) + ramps ─────────────────────
export const colors = {
  // Aliases semánticos planos — string, compat con código existente
  brand:     brandScale[500],
  brandDark: brandScale[600],
  accent:    navyScale[500],
  success:   successScale[500],
  danger:    dangerScale[500],
  warning:   warningScale[500],
  info:      infoScale[500],

  // Acceso directo a las escalas
  brandScale,
  navyScale,
  neutralScale,
  successScale,
  dangerScale,
  warningScale,
  infoScale,

  // Superficies
  bgDark:    '#0A1535',
  bgLight:   '#F8FAFC',
  cardDark:  '#152448',
  cardLight: '#FFFFFF',

  // Texto
  textDark:       '#E2E8F0',
  textLight:      '#0F172A',
  textMutedDark:  '#94A3B8',
  textMutedLight: '#64748B',

  // Utilidades
  white: '#FFFFFF',
  black: '#000000',
  border:     'rgba(15, 23, 42, 0.08)',
  borderDark: 'rgba(255, 255, 255, 0.08)',

  // Gradientes animados (usados por GradientText)
  gradientTitle:  ['#F58830', '#FFB36B', '#F58830'] as const,
  gradientAurora: ['rgba(245,136,48,0.22)', 'rgba(22,32,84,0.18)', 'rgba(245,136,48,0.18)'] as const,
} as const;

// ── Espaciado, radios, tipografía, sombras ───────────────────────
export const spacing = {
  xs: 4, sm: 8, md: 12, base: 16, lg: 20, xl: 24, xxl: 32, huge: 48,
} as const;

export const radius = {
  sm: 8, md: 12, lg: 16, xl: 20, xxl: 28, full: 999,
} as const;

/** Espacio que ocupa el tab bar flotante (alto + bottom inset + gap),
 *  para que las screens lo agreguen como `paddingBottom`. */
export const TAB_BAR_HEIGHT = 68 + 32 + 20;

/** Paleta de colores para iconos de meta (calendar/time/location/etc),
 *  para que todas las pantallas usen el mismo lenguaje visual. */
export const metaIconColors = {
  date:     '#F58830',  // brand orange — fechas
  time:     '#A855F7',  // violeta — tiempo / horas
  location: '#EF4444',  // rojo — ubicaciones físicas
  virtual:  '#3B82F6',  // azul — modalidad virtual
  hours:    '#10B981',  // verde — duración / horas certificadas
  people:   '#A855F7',  // violeta — capacidad / cupos
  program:  '#F59E0B',  // ámbar — programa / lote
  cert:     '#06B6D4',  // cyan — certificado
} as const;

export const typography = {
  xs: 11, sm: 13, base: 15, md: 17, lg: 20, xl: 24, xxl: 30, huge: 38,

  regular:  '400' as const,
  medium:   '500' as const,
  semibold: '600' as const,
  bold:     '700' as const,
  black:    '900' as const,

  sans: 'System',
  mono: 'Courier',
};

export const shadows = {
  sm: {
    shadowColor:   '#0F172A',
    shadowOffset:  { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius:  6,
    elevation:     2,
  },
  md: {
    shadowColor:   '#0F172A',
    shadowOffset:  { width: 0, height: 4 },
    shadowOpacity: 0.12,
    shadowRadius:  12,
    elevation:     4,
  },
  lg: {
    shadowColor:   '#0F172A',
    shadowOffset:  { width: 0, height: 8 },
    shadowOpacity: 0.18,
    shadowRadius:  24,
    elevation:     8,
  },
  brand: {
    shadowColor:   '#F58830',
    shadowOffset:  { width: 0, height: 6 },
    shadowOpacity: 0.45,
    shadowRadius:  14,
    elevation:     6,
  },
};

export type ThemeMode = 'light' | 'dark';

/**
 * Resuelve un set de colores semánticos según el tema activo. Usar en
 * componentes via `useThemeColors()` o pasando `mode` directo.
 */
export function themed(mode: ThemeMode) {
  const isDark = mode === 'dark';
  return {
    bg:        isDark ? colors.bgDark    : colors.bgLight,
    card:      isDark ? colors.cardDark  : '#FFFFFF',
    // En light: blanco sólido (mejor contraste sobre el bg #F8FAFC del aurora pastel)
    cardSoft:  isDark ? '#1A2A52'        : '#FFFFFF',
    surface:   isDark ? '#0E1A3D'        : '#F8FAFC',
    text:      isDark ? colors.textDark  : colors.textLight,
    textMuted: isDark ? colors.textMutedDark : colors.textMutedLight,
    // Bordes más visibles en light mode para que las tarjetas se separen del bg
    border:    isDark ? colors.borderDark : 'rgba(15, 23, 42, 0.10)',
    brand:     colors.brand,
    accent:    colors.accent,

    // Sombras neumorfistas (dark = highlight es light alpha; shadow es black alpha)
    neuLight:  isDark ? 'rgba(255,255,255,0.04)' : '#FFFFFF',
    neuDark:   isDark ? 'rgba(0,0,0,0.55)'       : 'rgba(15,23,42,0.10)',
  };
}

/**
 * Sombras neumorfistas (outset = botón "elevado", inset = "presionado").
 * Para inset usá `borderColor` simulando la luz que entra al hueco.
 */
export const neuShadow = {
  outsetSoft: (mode: ThemeMode) => {
    const c = themed(mode);
    return {
      shadowColor:   c.neuDark,
      shadowOffset:  { width: 4, height: 6 },
      shadowOpacity: 1,
      shadowRadius:  10,
      elevation:     3,
    };
  },
  outsetStrong: (mode: ThemeMode) => {
    const c = themed(mode);
    return {
      shadowColor:   c.neuDark,
      shadowOffset:  { width: 6, height: 10 },
      shadowOpacity: 1,
      shadowRadius:  18,
      elevation:     6,
    };
  },
};
