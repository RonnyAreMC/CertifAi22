import { useEffect, useState, useCallback } from 'react';
import {
  FlatList, Pressable, RefreshControl,
  StyleSheet, Text, View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { api } from '@/api/client';
import {
  colors, metaIconColors, radius, spacing, TAB_BAR_HEIGHT, themed, typography,
} from '@/theme/tokens';
import { useTheme } from '@/stores/theme';
import {
  Badge, GlassCard, Loader, ScreenHeader, stripHtml, VBackground,
} from '@/components/ui';

type Status = 'asisti' | 'inscrito' | 'no_asisti' | 'disponible';
type Evento = {
  id: number;
  titulo: string;
  titulo_display: string;
  descripcion: string;
  fecha: string;
  dia_semana: string;
  hora_inicio: string;
  hora_fin: string;
  modalidad: string;
  es_virtual: boolean;
  lugar: string;
  enlace_virtual: string;
  banner_url: string | null;
  activa: boolean;
  status: Status;
};
type EventosResponse = {
  tab: 'mios' | 'disponibles';
  count_mios: number;
  count_disponibles: number;
  results: Evento[];
};

const STATUS_TONE: Record<Status, 'success' | 'brand' | 'danger' | 'info'> = {
  asisti: 'success', inscrito: 'brand', no_asisti: 'danger', disponible: 'info',
};
const STATUS_LABEL: Record<Status, string> = {
  asisti: 'Asistí', inscrito: 'Inscrito', no_asisti: 'No asistí', disponible: 'Disponible',
};

export default function EventosScreen() {
  const [tab, setTab] = useState<'mios' | 'disponibles'>('mios');
  const [data, setData] = useState<EventosResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const theme = useTheme();
  const t = themed(theme);

  const load = useCallback(async () => {
    try {
      const res = await api.get<EventosResponse>(
        `/api/v1/public/account/events/?tab=${tab}`
      );
      setData(res);
    } catch {
      // silencio
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [tab]);

  useEffect(() => { setLoading(true); load(); }, [load]);

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: t.bg }]}>
      <VBackground intensity={theme === 'dark' ? 0.55 : 0.3} variant="mixed" />
      <ScreenHeader
        eyebrow="EVENTOS"
        title={tab === 'mios' ? 'Mis eventos' : 'Disponibles'}
        gradientTitle
      />

      <View style={styles.tabs}>
        <TabBtn
          label={`Mis eventos${data ? ` (${data.count_mios})` : ''}`}
          active={tab === 'mios'}
          onPress={() => setTab('mios')}
          theme={theme}
        />
        <TabBtn
          label={`Disponibles${data ? ` (${data.count_disponibles})` : ''}`}
          active={tab === 'disponibles'}
          onPress={() => setTab('disponibles')}
          theme={theme}
        />
      </View>

      {loading ? (
        <View style={styles.loading}><Loader size={88} /></View>
      ) : (
        <FlatList
          contentContainerStyle={{ padding: spacing.base, gap: spacing.sm, paddingBottom: TAB_BAR_HEIGHT + spacing.lg }}
          data={data?.results ?? []}
          keyExtractor={(e) => String(e.id)}
          renderItem={({ item }) => <EventoCard evento={item} />}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => { setRefreshing(true); load(); }}
              tintColor={colors.brand}
            />
          }
          ListEmptyComponent={
            <View style={styles.empty}>
              <Text style={[styles.emptyText, { color: t.textMuted }]}>
                {tab === 'mios'
                  ? 'Aún no estás inscrito en ningún evento.'
                  : 'No hay eventos disponibles por ahora.'}
              </Text>
            </View>
          }
        />
      )}
    </SafeAreaView>
  );
}

function TabBtn({
  label, active, onPress, theme,
}: { label: string; active: boolean; onPress: () => void; theme: 'light' | 'dark' }) {
  const t = themed(theme);
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.tabBtn,
        {
          backgroundColor: theme === 'dark' ? 'rgba(255,255,255,0.06)' : 'rgba(15,23,42,0.04)',
          borderColor: t.border,
        },
        active && { backgroundColor: colors.brand, borderColor: colors.brand },
        pressed && { opacity: 0.85 },
      ]}
    >
      <Text style={[
        styles.tabBtnText,
        { color: t.textMuted },
        active && { color: '#FFFFFF', fontWeight: typography.black },
      ]}>
        {label}
      </Text>
    </Pressable>
  );
}

function EventoCard({ evento }: { evento: Evento }) {
  const t = themed(useTheme());

  function openDetail() {
    router.push({ pathname: '/event/[id]', params: { id: String(evento.id) } });
  }

  return (
    <GlassCard onPress={openDetail} style={styles.card}>
      <View style={styles.cardTopRow}>
        <Badge
          tone={evento.es_virtual ? 'info' : 'brand'}
          variant="solid"
          size="sm"
          iconLeft={
            <Ionicons
              name={evento.es_virtual ? 'videocam' : 'business'}
              size={11}
              color="#FFFFFF"
            />
          }
        >
          {evento.es_virtual ? 'Virtual' : 'Presencial'}
        </Badge>
        <Badge tone={STATUS_TONE[evento.status]} variant="soft" size="sm" dot>
          {STATUS_LABEL[evento.status]}
        </Badge>
      </View>

      <Text style={[styles.cardTitle, { color: t.text }]} numberOfLines={2}>
        {evento.titulo_display}
      </Text>

      <View style={styles.metaRow}>
        <View style={styles.metaItem}>
          <View style={[styles.metaIcon, { backgroundColor: hexAlpha(metaIconColors.date, 0.14) }]}>
            <Ionicons name="calendar" size={12} color={metaIconColors.date} />
          </View>
          <Text style={[styles.metaText, { color: t.textMuted }]}>{evento.fecha}</Text>
        </View>
        <View style={styles.metaItem}>
          <View style={[styles.metaIcon, { backgroundColor: hexAlpha(metaIconColors.time, 0.14) }]}>
            <Ionicons name="time" size={12} color={metaIconColors.time} />
          </View>
          <Text style={[styles.metaText, { color: t.textMuted }]}>
            {evento.hora_inicio.slice(0, 5)}–{evento.hora_fin.slice(0, 5)}
          </Text>
        </View>
      </View>

      {evento.lugar ? (
        <View style={styles.metaItem}>
          <View style={[styles.metaIcon, { backgroundColor: hexAlpha(metaIconColors.location, 0.14) }]}>
            <Ionicons name="location" size={12} color={metaIconColors.location} />
          </View>
          <Text style={[styles.metaText, { color: t.textMuted }]} numberOfLines={1}>{evento.lugar}</Text>
        </View>
      ) : null}

      {evento.descripcion ? (
        <Text style={[styles.descripcion, { color: t.textMuted }]} numberOfLines={2}>
          {stripHtml(evento.descripcion)}
        </Text>
      ) : null}

      <View style={styles.cardFooter}>
        <Text style={[styles.cardCta, { color: colors.brand }]}>Ver detalles</Text>
        <Ionicons name="chevron-forward" size={16} color={colors.brand} />
      </View>
    </GlassCard>
  );
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

  tabs: {
    flexDirection: 'row', gap: spacing.sm,
    paddingHorizontal: spacing.base, marginBottom: spacing.sm,
  },
  tabBtn: {
    flex: 1,
    borderWidth: 1,
    borderRadius: radius.md,
    paddingVertical: spacing.sm, alignItems: 'center',
  },
  tabBtnText: {
    fontSize: typography.sm, fontWeight: typography.bold,
  },

  loading: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  empty:   { alignItems: 'center', padding: spacing.huge },
  emptyText: { fontSize: typography.sm, textAlign: 'center' },

  card: { gap: spacing.xs },
  cardTopRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  cardTitle:  { fontSize: typography.base, fontWeight: typography.black, marginTop: spacing.xs },
  metaRow:    { flexDirection: 'row', gap: spacing.md, marginTop: spacing.xs, flexWrap: 'wrap' },
  metaItem:   { flexDirection: 'row', alignItems: 'center', gap: 6 },
  metaIcon:   {
    width: 22, height: 22, borderRadius: 6,
    alignItems: 'center', justifyContent: 'center',
  },
  metaText:   { fontSize: typography.sm },
  descripcion:{ fontSize: typography.sm, marginTop: spacing.xs, opacity: 0.8 },
  cardFooter: {
    flexDirection: 'row', alignItems: 'center', gap: 4,
    marginTop: spacing.sm,
  },
  cardCta: {
    fontSize: typography.xs,
    fontWeight: typography.black,
    letterSpacing: 0.6,
    textTransform: 'uppercase',
  },
});
