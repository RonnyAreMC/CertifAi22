import { useEffect, useState, useCallback } from 'react';
import {
  Linking, Pressable, RefreshControl, ScrollView, StyleSheet, Text, View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';

import { api } from '@/api/client';
import {
  brandScale, colors, radius, shadows, spacing, TAB_BAR_HEIGHT,
  themed, typography,
} from '@/theme/tokens';
import { useAuth } from '@/stores/auth';
import { useTheme } from '@/stores/theme';
import {
  Badge, GlassCard, GradientText, Loader, MeetLogo, VBackground,
} from '@/components/ui';

type Stats = {
  certificados: number;
  total_horas: number;
  eventos_inscrito: number;
  eventos_asistido: number;
};
type Sesion = {
  id: number;
  titulo_display: string;
  fecha: string;
  hora_inicio: string;
  hora_fin: string;
  es_virtual: boolean;
  enlace_virtual?: string;
  lugar?: string;
};
type Certificado = {
  id: number;
  curso: string;
  fecha_curso: string | null;
  horas: number;
  download_url: string;
};
type DashboardData = {
  stats: Stats;
  proximos: Sesion[];
  recomendados: Sesion[];
  certificados_recientes?: Certificado[];
};

export default function DashboardScreen() {
  const participante = useAuth((s) => s.participante);
  const [data, setData]       = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const theme = useTheme();
  const t = themed(theme);

  const load = useCallback(async () => {
    try {
      const res = await api.get<DashboardData>('/api/v1/public/account/dashboard/');
      setData(res);
    } catch {
      // silencio
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <SafeAreaView style={[styles.safe, { backgroundColor: t.bg }]}>
        <View style={styles.loading}><Loader size={88} label="Cargando tu cuenta…" /></View>
      </SafeAreaView>
    );
  }

  const today = new Date();
  const greeting = getGreeting(today);
  const dateBlock = formatDateBlock(today);
  const nextEvent = data?.proximos?.[0];

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: t.bg }]}>
      <VBackground intensity={theme === 'dark' ? 0.7 : 0.4} />
      <ScrollView
        contentContainerStyle={styles.scroll}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => { setRefreshing(true); load(); }}
            tintColor={colors.brand}
          />
        }
      >
        {/* ═══ HERO SALUDO (saludo a la izquierda + fecha block a la derecha) ═══ */}
        <View style={styles.hero}>
          <View style={styles.heroRow}>
            <View style={{ flex: 1 }}>
              <View style={styles.eyebrow}>
                <Ionicons name={greeting.icon} size={11} color={colors.brand} />
                <Text style={styles.eyebrowText}>{greeting.label.toUpperCase()}</Text>
              </View>
              <View style={styles.heroTitleWrap}>
                <GradientText style={styles.heroTitle}>
                  {`${(participante?.nombres || '—').split(' ')[0]}.`}
                </GradientText>
              </View>
            </View>

            {/* Fecha block (estilo iPhone calendar widget) */}
            <View style={[
              styles.dateBlock,
              {
                backgroundColor: theme === 'dark' ? 'rgba(245,136,48,0.10)' : '#FFFFFF',
                borderColor: theme === 'dark' ? 'rgba(245,136,48,0.30)' : 'rgba(245,136,48,0.40)',
              },
              shadows.sm,
            ]}>
              <Text style={[styles.dateWeekday, { color: colors.brand }]}>{dateBlock.weekday}</Text>
              <Text style={[styles.dateDay, { color: t.text }]}>{dateBlock.day}</Text>
              <Text style={[styles.dateMonth, { color: t.textMuted }]}>{dateBlock.month}</Text>
            </View>
          </View>

          <Text style={[styles.heroSub, { color: t.textMuted }]}>
            {data?.proximos.length
              ? `Tienes ${data.proximos.length} evento${data.proximos.length === 1 ? '' : 's'} próximo${data.proximos.length === 1 ? '' : 's'}.`
              : 'Hoy es un buen día para descubrir un evento nuevo.'}
          </Text>

          {/* Quick action chips */}
          <View style={styles.chipRow}>
            <QuickChip
              icon="qr-code"
              label="Escanear QR"
              onPress={() => router.push('/scanner')}
            />
            <QuickChip
              icon="compass"
              label="Explorar eventos"
              onPress={() => router.push('/(tabs)/events')}
              variant="primary"
            />
          </View>
        </View>

        {/* ═══ STATS ═══ */}
        <View style={styles.statsGrid}>
          <StatTile
            icon="ribbon"
            value={data?.stats.certificados ?? 0}
            label="Certificados"
            gradient={[brandScale[500], brandScale[700]] as [string, string]}
          />
          <StatTile
            icon="time"
            value={data?.stats.total_horas ?? 0}
            suffix="h"
            label="Estudiadas"
            gradient={['#A855F7', '#7C3AED'] as [string, string]}
          />
          <StatTile
            icon="checkmark-circle"
            value={data?.stats.eventos_asistido ?? 0}
            label="Asistidos"
            gradient={['#10B981', '#059669'] as [string, string]}
          />
          <StatTile
            icon="bookmark"
            value={data?.stats.eventos_inscrito ?? 0}
            label="Inscritos"
            gradient={['#3B82F6', '#2563EB'] as [string, string]}
          />
        </View>

        {/* ═══ PRÓXIMO EVENTO destacado con countdown ═══ */}
        {nextEvent ? (
          <View style={styles.section}>
            <NextEventCard evento={nextEvent} />
          </View>
        ) : null}

        {/* ═══ Próximos eventos (resto) ═══ */}
        {(data?.proximos.length ?? 0) > 1 ? (
          <Section title="MIS PRÓXIMOS EVENTOS" actionLabel="Ver todos" onAction={() => router.push('/(tabs)/events')}>
            {data!.proximos.slice(1).map((s) => <SesionRow key={s.id} sesion={s} />)}
          </Section>
        ) : null}

        {/* ═══ Recomendados ═══ */}
        {(data?.recomendados.length ?? 0) > 0 ? (
          <Section title="PARA TI · DISPONIBLES" actionLabel="Ver más" onAction={() => router.push('/(tabs)/events')}>
            {data!.recomendados.slice(0, 3).map((s) => <SesionRow key={s.id} sesion={s} />)}
          </Section>
        ) : null}

        {/* ═══ Certificados recientes ═══ */}
        {(data?.certificados_recientes?.length ?? 0) > 0 ? (
          <Section title="ÚLTIMOS CERTIFICADOS" actionLabel="Ver todos" onAction={() => router.push('/(tabs)/certificates')}>
            {data!.certificados_recientes!.slice(0, 3).map((c) => <CertRow key={c.id} cert={c} />)}
          </Section>
        ) : null}
      </ScrollView>

      {/* FAB → escanear QR (acceso rápido siempre visible) */}
      <Pressable
        onPress={() => router.push('/scanner')}
        style={({ pressed }) => [
          styles.fab,
          { bottom: TAB_BAR_HEIGHT + spacing.sm },
          pressed && { transform: [{ scale: 0.94 }], opacity: 0.92 },
        ]}
      >
        <Ionicons name="qr-code" size={22} color="#FFFFFF" />
      </Pressable>
    </SafeAreaView>
  );
}

// ── Subcomponentes ──────────────────────────────────────────────

function QuickChip({
  icon, label, onPress, variant = 'soft',
}: {
  icon: React.ComponentProps<typeof Ionicons>['name'];
  label: string;
  onPress: () => void;
  variant?: 'soft' | 'primary';
}) {
  const t = themed(useTheme());
  if (variant === 'primary') {
    return (
      <Pressable
        onPress={onPress}
        style={({ pressed }) => [
          styles.chip,
          styles.chipPrimary,
          pressed && { opacity: 0.85, transform: [{ scale: 0.98 }] },
        ]}
      >
        <Ionicons name={icon} size={14} color="#FFFFFF" />
        <Text style={styles.chipPrimaryText}>{label}</Text>
      </Pressable>
    );
  }
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.chip,
        { backgroundColor: t.cardSoft, borderColor: t.border },
        pressed && { opacity: 0.85, transform: [{ scale: 0.98 }] },
      ]}
    >
      <Ionicons name={icon} size={14} color={colors.brand} />
      <Text style={[styles.chipText, { color: t.text }]}>{label}</Text>
    </Pressable>
  );
}

function StatTile({
  icon, value, suffix, label, gradient,
}: {
  icon: React.ComponentProps<typeof Ionicons>['name'];
  value: string | number;
  suffix?: string;
  label: string;
  gradient: [string, string];
}) {
  const t = themed(useTheme());
  return (
    <View style={[
      styles.stat,
      { backgroundColor: t.cardSoft, borderColor: t.border },
      shadows.sm,
    ]}>
      <LinearGradient
        colors={gradient}
        start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
        style={styles.statIcon}
      >
        <Ionicons name={icon} size={16} color="#FFFFFF" />
      </LinearGradient>
      <View style={{ flex: 1 }}>
        <Text style={[styles.statValue, { color: t.text }]}>
          {value}
          {suffix ? <Text style={[styles.statSuffix, { color: t.textMuted }]}>{suffix}</Text> : null}
        </Text>
        <Text style={[styles.statLabel, { color: t.textMuted }]}>{label}</Text>
      </View>
    </View>
  );
}

function NextEventCard({ evento }: { evento: Sesion }) {
  const theme = useTheme();
  const t = themed(theme);
  const targetDate = new Date(`${evento.fecha}T${evento.hora_inicio}`);
  const [remaining, setRemaining] = useState(() => calcRemaining(targetDate));

  useEffect(() => {
    const timer = setInterval(() => setRemaining(calcRemaining(targetDate)), 1000);
    return () => clearInterval(timer);
  }, [evento.fecha, evento.hora_inicio]);

  return (
    <GlassCard onPress={() => router.push({ pathname: '/event/[id]', params: { id: String(evento.id) } })}>
      <View style={styles.nextHead}>
        <Badge tone="brand" variant="soft" size="sm" iconLeft={<Ionicons name="flash" size={11} color={colors.brand} />}>
          PRÓXIMO EVENTO
        </Badge>
        <Badge
          tone={evento.es_virtual ? 'info' : 'brand'}
          variant="solid"
          size="sm"
          iconLeft={
            <Ionicons name={evento.es_virtual ? 'videocam' : 'business'} size={11} color="#FFFFFF" />
          }
        >
          {evento.es_virtual ? 'Virtual' : 'Presencial'}
        </Badge>
      </View>

      <Text style={[styles.nextTitle, { color: t.text }]} numberOfLines={2}>
        {evento.titulo_display}
      </Text>

      <View style={styles.nextMeta}>
        <View style={styles.nextMetaItem}>
          <Ionicons name="calendar" size={13} color={colors.brand} />
          <Text style={[styles.nextMetaText, { color: t.textMuted }]}>
            {formatDate(evento.fecha)}
          </Text>
        </View>
        <View style={styles.nextMetaItem}>
          <Ionicons name="time" size={13} color={colors.brand} />
          <Text style={[styles.nextMetaText, { color: t.textMuted }]}>
            {evento.hora_inicio.slice(0, 5)}
          </Text>
        </View>
      </View>

      {/* Countdown */}
      <View style={styles.countdownGrid}>
        <CountCell value={remaining.d} label="Días" />
        <CountCell value={remaining.h} label="Horas" />
        <CountCell value={remaining.m} label="Min" />
        <CountCell value={remaining.s} label="Seg" />
      </View>

      {/* Botón Meet — sin caja propia, solo contenido dentro del GlassCard */}
      {evento.es_virtual && evento.enlace_virtual ? (
        <Pressable
          onPress={(e: any) => {
            e?.stopPropagation?.();
            Linking.openURL(evento.enlace_virtual!);
          }}
          style={({ pressed }) => [
            styles.meetBtn,
            pressed && { opacity: 0.7 },
          ]}
        >
          <MeetLogo size={32} />
          <View style={{ flex: 1 }}>
            <Text style={[styles.meetText, { color: t.text }]}>Entrar a Google Meet</Text>
            <Text style={[styles.meetSub, { color: t.textMuted }]}>Reunión virtual</Text>
          </View>
          <View style={styles.meetGo}>
            <Ionicons name="arrow-forward" size={16} color="#FFFFFF" />
          </View>
        </Pressable>
      ) : null}
    </GlassCard>
  );
}

function CountCell({ value, label }: { value: number; label: string }) {
  const t = themed(useTheme());
  return (
    <View style={[styles.cdCell, { backgroundColor: 'rgba(245,136,48,0.08)', borderColor: 'rgba(245,136,48,0.20)' }]}>
      <Text style={[styles.cdNum, { color: colors.brand }]}>
        {String(Math.max(0, value)).padStart(2, '0')}
      </Text>
      <Text style={[styles.cdLbl, { color: t.textMuted }]}>{label}</Text>
    </View>
  );
}

function Section({
  title, children, actionLabel, onAction,
}: {
  title: string;
  children: React.ReactNode;
  actionLabel?: string;
  onAction?: () => void;
}) {
  const t = themed(useTheme());
  return (
    <View style={styles.section}>
      <View style={styles.sectionHead}>
        <Text style={[styles.sectionTitle, { color: t.textMuted }]}>{title}</Text>
        {actionLabel && onAction ? (
          <Pressable onPress={onAction} hitSlop={6}>
            <Text style={styles.sectionAction}>{actionLabel} →</Text>
          </Pressable>
        ) : null}
      </View>
      <View style={{ gap: spacing.sm }}>{children}</View>
    </View>
  );
}

function SesionRow({ sesion }: { sesion: Sesion }) {
  const t = themed(useTheme());
  return (
    <GlassCard onPress={() => router.push({ pathname: '/event/[id]', params: { id: String(sesion.id) } })}>
      <View style={styles.rowTop}>
        <Badge
          tone={sesion.es_virtual ? 'info' : 'brand'}
          variant="solid"
          size="sm"
          iconLeft={<Ionicons name={sesion.es_virtual ? 'videocam' : 'business'} size={11} color="#FFFFFF" />}
        >
          {sesion.es_virtual ? 'Virtual' : 'Presencial'}
        </Badge>
      </View>
      <Text style={[styles.rowTitle, { color: t.text }]} numberOfLines={2}>
        {sesion.titulo_display}
      </Text>
      <View style={styles.rowMeta}>
        <Ionicons name="calendar-outline" size={13} color={t.textMuted} />
        <Text style={[styles.rowMetaText, { color: t.textMuted }]}>
          {formatDate(sesion.fecha)} · {sesion.hora_inicio.slice(0, 5)}
        </Text>
      </View>
    </GlassCard>
  );
}

function CertRow({ cert }: { cert: Certificado }) {
  const t = themed(useTheme());
  return (
    <GlassCard
      onPress={() => Linking.openURL(`${api.baseUrl}${cert.download_url}`)}
      style={styles.certRow}
    >
      <View style={styles.certIcon}>
        <Ionicons name="ribbon" size={20} color="#FFFFFF" />
      </View>
      <View style={{ flex: 1 }}>
        <Text style={[styles.certTitle, { color: t.text }]} numberOfLines={2}>{cert.curso}</Text>
        <Text style={[styles.certMeta, { color: t.textMuted }]}>
          {cert.fecha_curso ?? '—'} · {cert.horas}h
        </Text>
      </View>
      <Ionicons name="download-outline" size={20} color={colors.brand} />
    </GlassCard>
  );
}

// ── Helpers ─────────────────────────────────────────────────────
function calcRemaining(target: Date) {
  const ms = target.getTime() - Date.now();
  if (ms <= 0) return { d: 0, h: 0, m: 0, s: 0, expired: true };
  const s = Math.floor(ms / 1000);
  return {
    d: Math.floor(s / 86400),
    h: Math.floor((s % 86400) / 3600),
    m: Math.floor((s % 3600) / 60),
    s: s % 60,
    expired: false,
  };
}

function formatDate(iso: string): string {
  try {
    const d = new Date(`${iso}T00:00:00`);
    return d.toLocaleDateString('es-EC', { day: '2-digit', month: 'short' });
  } catch {
    return iso;
  }
}

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

/** Saludo según hora local — buenas días/tardes/noches con icono apropiado. */
function getGreeting(now: Date): {
  label: string;
  icon: 'sunny' | 'partly-sunny' | 'moon';
} {
  const h = now.getHours();
  if (h >= 5 && h < 12)  return { label: 'Buenos días',   icon: 'sunny' };
  if (h >= 12 && h < 19) return { label: 'Buenas tardes', icon: 'partly-sunny' };
  return { label: 'Buenas noches', icon: 'moon' };
}

/** "Jueves, 30 de abril" → { weekday: 'JUE', day: '30', month: 'ABR' } */
function formatDateBlock(d: Date): { weekday: string; day: string; month: string } {
  const days   = ['DOM', 'LUN', 'MAR', 'MIÉ', 'JUE', 'VIE', 'SÁB'];
  const months = ['ENE','FEB','MAR','ABR','MAY','JUN','JUL','AGO','SEP','OCT','NOV','DIC'];
  return {
    weekday: days[d.getDay()],
    day: String(d.getDate()).padStart(2, '0'),
    month: months[d.getMonth()],
  };
}

// ── Estilos ─────────────────────────────────────────────────────
const styles = StyleSheet.create({
  safe:   { flex: 1 },
  scroll: { paddingBottom: TAB_BAR_HEIGHT + spacing.lg },
  loading: { flex: 1, alignItems: 'center', justifyContent: 'center' },

  hero: { paddingHorizontal: spacing.xl, paddingTop: spacing.sm, marginBottom: spacing.lg },
  heroRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: spacing.base,
  },
  eyebrow: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    paddingHorizontal: spacing.md, paddingVertical: 5,
    backgroundColor: 'rgba(245,136,48,0.12)',
    borderColor: 'rgba(245,136,48,0.28)', borderWidth: 1,
    borderRadius: radius.full, alignSelf: 'flex-start',
  },
  eyebrowText: {
    color: colors.brand, fontSize: typography.xs,
    fontWeight: typography.black, letterSpacing: 1,
  },
  heroTitleWrap: { marginTop: spacing.sm },
  heroTitle: {
    fontSize: typography.huge,
    fontWeight: typography.black,
    letterSpacing: -1,
    lineHeight: typography.huge * 1.05,
  },
  heroSub: { fontSize: typography.sm, marginTop: spacing.base, lineHeight: typography.sm * 1.5 },

  // Fecha block widget tipo iPhone Calendar
  dateBlock: {
    minWidth: 64,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.sm,
    borderRadius: radius.lg,
    borderWidth: 1,
    alignItems: 'center', justifyContent: 'center',
  },
  dateWeekday: {
    fontSize: typography.xs - 1,
    fontWeight: typography.black,
    letterSpacing: 1.5,
    textTransform: 'uppercase',
    lineHeight: typography.xs + 2,
  },
  dateDay: {
    fontSize: typography.xxl,
    fontWeight: typography.black,
    letterSpacing: -1,
    lineHeight: typography.xxl,
    marginVertical: 1,
  },
  dateMonth: {
    fontSize: typography.xs - 1,
    fontWeight: typography.bold,
    letterSpacing: 0.6,
    textTransform: 'uppercase',
  },

  chipRow: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.lg, flexWrap: 'wrap' },
  chip: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    paddingHorizontal: spacing.md, paddingVertical: spacing.sm,
    borderRadius: radius.md,
    borderWidth: 1,
  },
  chipText: { fontSize: typography.sm, fontWeight: typography.black },
  chipPrimary: {
    backgroundColor: colors.brand,
    borderColor: colors.brand,
    ...shadows.brand,
  },
  chipPrimaryText: { color: '#FFFFFF', fontSize: typography.sm, fontWeight: typography.black },

  statsGrid: {
    flexDirection: 'row', flexWrap: 'wrap',
    paddingHorizontal: spacing.xl, gap: spacing.sm,
  },
  stat: {
    flexBasis: '48%', flexGrow: 1,
    flexDirection: 'row', alignItems: 'center', gap: spacing.md,
    padding: spacing.base, borderRadius: radius.lg, borderWidth: 1,
  },
  statIcon: {
    width: 36, height: 36, borderRadius: radius.md,
    alignItems: 'center', justifyContent: 'center',
  },
  statValue: {
    fontSize: typography.xl, fontWeight: typography.black,
    letterSpacing: -0.5, lineHeight: typography.xl + 2,
  },
  statSuffix: { fontSize: typography.md, fontWeight: typography.bold },
  statLabel: { fontSize: typography.xs, fontWeight: typography.bold, marginTop: 1 },

  // Próximo evento card
  nextHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  nextTitle: {
    fontSize: typography.lg, fontWeight: typography.black,
    letterSpacing: -0.3, marginTop: spacing.sm,
    lineHeight: typography.lg * 1.2,
  },
  nextMeta: { flexDirection: 'row', gap: spacing.md, marginTop: spacing.xs },
  nextMetaItem: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  nextMetaText: { fontSize: typography.sm, fontWeight: typography.medium },

  countdownGrid: {
    flexDirection: 'row', gap: spacing.xs, marginTop: spacing.base,
  },
  cdCell: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: spacing.sm + 2,
    borderRadius: radius.md,
    borderWidth: 1,
  },
  cdNum: {
    fontSize: typography.xl, fontWeight: typography.black,
    letterSpacing: -0.5, fontVariant: ['tabular-nums'],
  },
  cdLbl: {
    fontSize: typography.xs - 1, fontWeight: typography.bold,
    letterSpacing: 0.5, textTransform: 'uppercase', marginTop: 2,
  },

  meetBtn: {
    flexDirection: 'row', alignItems: 'center',
    gap: spacing.md,
    paddingVertical: spacing.sm,
    marginTop: spacing.base,
    // Sin background, sin border — solo contenido dentro del GlassCard
  },
  meetText: {
    fontSize: typography.base, fontWeight: typography.black,
    letterSpacing: -0.1,
  },
  meetSub: {
    fontSize: typography.xs, fontWeight: typography.medium,
    marginTop: 1,
  },
  meetGo: {
    width: 32, height: 32,
    borderRadius: radius.full,
    backgroundColor: '#00832D',
    alignItems: 'center', justifyContent: 'center',
    ...shadows.sm,
  },

  // Sections
  section: { marginTop: spacing.xl, paddingHorizontal: spacing.xl },
  sectionHead: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    marginBottom: spacing.sm,
  },
  sectionTitle: {
    fontSize: typography.xs, fontWeight: typography.black,
    letterSpacing: 1.5, textTransform: 'uppercase',
  },
  sectionAction: {
    fontSize: typography.xs, fontWeight: typography.black,
    letterSpacing: 0.5, color: colors.brand,
  },

  // Sesion row (lista compacta)
  rowTop: { flexDirection: 'row' },
  rowTitle: {
    fontSize: typography.base, fontWeight: typography.black,
    letterSpacing: -0.2, marginTop: spacing.xs,
  },
  rowMeta: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: spacing.xs },
  rowMetaText: { fontSize: typography.sm, fontWeight: typography.medium },

  // Certificado row
  certRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    minHeight: 96,                                    // todos los cards al mismo porte
  },
  certIcon: {
    width: 40, height: 40, borderRadius: radius.md,
    backgroundColor: colors.brand,
    alignItems: 'center', justifyContent: 'center',
    ...shadows.brand,
  },
  certTitle: { fontSize: typography.base, fontWeight: typography.black },
  certMeta:  { fontSize: typography.sm, fontWeight: typography.medium, marginTop: 2 },

  // FAB
  fab: {
    position: 'absolute',
    right: spacing.lg,
    width: 56, height: 56,
    borderRadius: radius.full,
    backgroundColor: colors.brand,
    alignItems: 'center', justifyContent: 'center',
    ...shadows.brand,
  },
});
