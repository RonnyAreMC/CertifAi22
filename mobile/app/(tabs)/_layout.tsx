import { Redirect, Tabs } from 'expo-router';
import { Platform, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { colors, radius, shadows, spacing, themed, typography } from '@/theme/tokens';
import { useAuth } from '@/stores/auth';
import { useTheme } from '@/stores/theme';

type IoniconName = React.ComponentProps<typeof Ionicons>['name'];

const TAB_ICONS: Record<string, { active: IoniconName; inactive: IoniconName; label: string }> = {
  index:        { active: 'home',                  inactive: 'home-outline',                  label: 'Inicio' },
  events:       { active: 'calendar',              inactive: 'calendar-outline',              label: 'Eventos' },
  attendance:   { active: 'checkmark-done-circle', inactive: 'checkmark-done-circle-outline', label: 'Asistir' },
  certificates: { active: 'ribbon',                inactive: 'ribbon-outline',                label: 'Certs' },
  profile:      { active: 'person-circle',         inactive: 'person-circle-outline',         label: 'Perfil' },
};

function Icon({ name, focused, theme }: {
  name: keyof typeof TAB_ICONS; focused: boolean; theme: 'light' | 'dark';
}) {
  const t = themed(theme);
  const cfg = TAB_ICONS[name];
  const glyph = focused ? cfg.active : cfg.inactive;
  const tint = focused ? colors.brand : t.textMuted;
  return (
    <View style={styles.itemContent}>
      <Ionicons name={glyph} size={22} color={tint} />
      <Text
        style={[
          styles.label,
          { color: tint, fontWeight: focused ? typography.black : typography.bold },
        ]}
        numberOfLines={1}
      >
        {cfg.label}
      </Text>
      {focused ? <View style={[styles.activeDot, { backgroundColor: colors.brand }]} /> : null}
    </View>
  );
}

export default function TabsLayout() {
  const participante = useAuth((s) => s.participante);
  const ready = useAuth((s) => s.ready);
  const theme = useTheme();

  if (ready && !participante) return <Redirect href="/(auth)/login" />;

  const isDark = theme === 'dark';
  // Nav tradicional limpio: una barra blanca/navy con bordes neumórficos
  const barBg = isDark ? '#0F1A4D' : '#FFFFFF';
  const barBorder = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(15,23,42,0.06)';

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarShowLabel: false,
        tabBarStyle: [
          styles.bar,
          styles.barShadow,
          { backgroundColor: barBg, borderColor: barBorder },
        ],
        tabBarItemStyle: styles.item,
      }}
    >
      <Tabs.Screen name="index"        options={{ title: 'Inicio',       tabBarIcon: ({ focused }) => <Icon name="index"        focused={focused} theme={theme} /> }} />
      <Tabs.Screen name="events"       options={{ title: 'Eventos',      tabBarIcon: ({ focused }) => <Icon name="events"       focused={focused} theme={theme} /> }} />
      <Tabs.Screen name="attendance"   options={{ title: 'Asistencias',  tabBarIcon: ({ focused }) => <Icon name="attendance"   focused={focused} theme={theme} /> }} />
      <Tabs.Screen name="certificates" options={{ title: 'Certificados', tabBarIcon: ({ focused }) => <Icon name="certificates" focused={focused} theme={theme} /> }} />
      <Tabs.Screen name="profile"      options={{ title: 'Perfil',       tabBarIcon: ({ focused }) => <Icon name="profile"      focused={focused} theme={theme} /> }} />
    </Tabs>
  );
}

const styles = StyleSheet.create({
  // Nav tradicional: barra horizontal con bordes redondeados arriba
  bar: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    height: Platform.OS === 'ios' ? 84 : 64,
    paddingTop: 8,
    paddingBottom: Platform.OS === 'ios' ? 24 : 8,
    paddingHorizontal: spacing.sm,
    borderTopWidth: 1,
    borderTopLeftRadius: radius.xxl,
    borderTopRightRadius: radius.xxl,
    elevation: 0,
  },
  barShadow: {
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: -4 },
    shadowOpacity: 0.10,
    shadowRadius: 12,
    elevation: 12,
  },
  item: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  itemContent: {
    alignItems: 'center',
    justifyContent: 'center',
    gap: 2,
    minWidth: 60,
  },
  label: {
    fontSize: typography.xs - 1,
    letterSpacing: 0.4,
    marginTop: 2,
    textAlign: 'center',
  },
  // Indicador (puntito) debajo del label en el tab activo
  activeDot: {
    width: 4, height: 4,
    borderRadius: 2,
    marginTop: 4,
  },
});
