import { useEffect, useState, useCallback } from 'react';
import {
  FlatList, RefreshControl, StyleSheet, Text, View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { api } from '@/api/client';
import {
  colors, metaIconColors, radius, shadows, spacing, TAB_BAR_HEIGHT, themed, typography,
} from '@/theme/tokens';
import { useTheme } from '@/stores/theme';
import {
  Badge, GlassCard, Loader, ScreenHeader, VBackground,
} from '@/components/ui';

type Asistencia = {
  id: number;
  sesion_id: number;
  titulo: string;
  fecha: string;
  dia_semana: string;
  hora_inicio: string;
  hora_fin: string;
  es_virtual: boolean;
  modalidad: string;
  lugar: string;
  lote_nombre: string | null;
  fecha_registro: string;
  tiene_certificado: boolean;
  certificado_hash: string | null;
};

type AsistenciasResponse = {
  count: number;
  results: Asistencia[];
};

export default function AsistenciasScreen() {
  const [data, setData] = useState<AsistenciasResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const theme = useTheme();
  const t = themed(theme);

  const load = useCallback(async () => {
    try {
      const res = await api.get<AsistenciasResponse>('/api/v1/public/account/attendances/');
      setData(res);
    } catch {
      // silencio
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: t.bg }]}>
      <VBackground intensity={theme === 'dark' ? 0.5 : 0.3} />
      <ScreenHeader
        eyebrow="MIS ASISTENCIAS"
        title={data ? `${data.count} evento${data.count === 1 ? '' : 's'}` : '—'}
        gradientTitle
      />

      {loading ? (
        <View style={styles.loading}><Loader size={88} /></View>
      ) : (
        <FlatList
          contentContainerStyle={{
            padding: spacing.base,
            gap: spacing.sm,
            paddingBottom: TAB_BAR_HEIGHT + spacing.lg,
          }}
          data={data?.results ?? []}
          keyExtractor={(a) => String(a.id)}
          renderItem={({ item }) => <AsistenciaCard item={item} />}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => { setRefreshing(true); load(); }}
              tintColor={colors.brand}
            />
          }
          ListEmptyComponent={
            <View style={styles.empty}>
              <Ionicons name="checkmark-done-circle-outline" size={48} color={t.textMuted} />
              <Text style={[styles.emptyTitle, { color: t.text }]}>Aún no tienes asistencias</Text>
              <Text style={[styles.emptyText, { color: t.textMuted }]}>
                Inscríbete a un evento y registra tu asistencia escaneando el QR.
              </Text>
            </View>
          }
        />
      )}
    </SafeAreaView>
  );
}

function AsistenciaCard({ item }: { item: Asistencia }) {
  const t = themed(useTheme());
  const fecha = formatDate(item.fecha);

  function open() {
    router.push({ pathname: '/event/[id]', params: { id: String(item.sesion_id) } });
  }

  return (
    <GlassCard onPress={open} style={styles.card}>
      <View style={styles.cardTopRow}>
        <Badge
          tone={item.es_virtual ? 'info' : 'brand'}
          variant="solid"
          size="sm"
          iconLeft={<Ionicons name={item.es_virtual ? 'videocam' : 'business'} size={11} color="#FFFFFF" />}
        >
          {item.es_virtual ? 'Virtual' : 'Presencial'}
        </Badge>
        {item.tiene_certificado ? (
          <Badge
            tone="success" variant="soft" size="sm"
            iconLeft={<Ionicons name="ribbon" size={11} color="#10B981" />}
          >
            Certificado
          </Badge>
        ) : (
          <Badge tone="success" variant="soft" size="sm" dot>Asistido</Badge>
        )}
      </View>

      <Text style={[styles.cardTitle, { color: t.text }]} numberOfLines={2}>
        {item.titulo}
      </Text>

      <View style={styles.metaRow}>
        <View style={styles.metaItem}>
          <View style={[styles.metaIcon, { backgroundColor: hexAlpha(metaIconColors.date, 0.14) }]}>
            <Ionicons name="calendar" size={12} color={metaIconColors.date} />
          </View>
          <Text style={[styles.metaText, { color: t.textMuted }]}>{fecha}</Text>
        </View>
        <View style={styles.metaItem}>
          <View style={[styles.metaIcon, { backgroundColor: hexAlpha(metaIconColors.time, 0.14) }]}>
            <Ionicons name="time" size={12} color={metaIconColors.time} />
          </View>
          <Text style={[styles.metaText, { color: t.textMuted }]}>
            {item.hora_inicio}–{item.hora_fin}
          </Text>
        </View>
      </View>

      {item.lugar ? (
        <View style={styles.metaItem}>
          <View style={[styles.metaIcon, { backgroundColor: hexAlpha(metaIconColors.location, 0.14) }]}>
            <Ionicons name="location" size={12} color={metaIconColors.location} />
          </View>
          <Text style={[styles.metaText, { color: t.textMuted }]} numberOfLines={1}>{item.lugar}</Text>
        </View>
      ) : null}

      {/* Stamp con la hora exacta del registro */}
      <View style={[styles.stamp, { backgroundColor: 'rgba(16,185,129,0.10)', borderColor: 'rgba(16,185,129,0.30)' }]}>
        <Ionicons name="checkmark-circle" size={14} color="#10B981" />
        <Text style={[styles.stampText, { color: '#10B981' }]}>
          Registrado · {item.fecha_registro}
        </Text>
      </View>
    </GlassCard>
  );
}

function formatDate(iso: string): string {
  try {
    const d = new Date(`${iso}T00:00:00`);
    return d.toLocaleDateString('es-EC', { day: '2-digit', month: 'long', year: 'numeric' });
  } catch {
    return iso;
  }
}

/** Mezcla un hex con alpha (#RRGGBB → rgba). */
function hexAlpha(hex: string, alpha: number): string {
  const m = hex.replace('#', '');
  const r = parseInt(m.slice(0, 2), 16);
  const g = parseInt(m.slice(2, 4), 16);
  const b = parseInt(m.slice(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

const styles = StyleSheet.create({
  safe: { flex: 1 },

  loading: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  empty: {
    alignItems: 'center', padding: spacing.huge, gap: spacing.sm,
  },
  emptyTitle: {
    fontSize: typography.lg, fontWeight: typography.black,
    textAlign: 'center', marginTop: spacing.sm,
  },
  emptyText: { fontSize: typography.sm, textAlign: 'center', lineHeight: typography.sm * 1.5 },

  card: { gap: spacing.xs },
  cardTopRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: spacing.sm },
  cardTitle: {
    fontSize: typography.base, fontWeight: typography.black,
    letterSpacing: -0.2, marginTop: spacing.xs,
  },
  metaRow: { flexDirection: 'row', gap: spacing.md, marginTop: spacing.xs, flexWrap: 'wrap' },
  metaItem: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  metaIcon: {
    width: 22, height: 22, borderRadius: 6,
    alignItems: 'center', justifyContent: 'center',
  },
  metaText: { fontSize: typography.sm, fontWeight: typography.medium },

  stamp: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    paddingHorizontal: spacing.md, paddingVertical: spacing.sm - 2,
    borderRadius: radius.md, borderWidth: 1,
    alignSelf: 'flex-start',
    marginTop: spacing.sm,
    ...shadows.sm,
  },
  stampText: {
    fontSize: typography.xs, fontWeight: typography.black,
    letterSpacing: 0.5, textTransform: 'uppercase',
  },
});
