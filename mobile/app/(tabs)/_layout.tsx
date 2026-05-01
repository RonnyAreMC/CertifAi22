import { Redirect, Tabs } from 'expo-router';
import { Platform, StyleSheet, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { BlurView } from 'expo-blur';

import { colors, radius, shadows, spacing, themed } from '@/theme/tokens';
import { useAuth } from '@/stores/auth';
import { useTheme } from '@/stores/theme';

type IoniconName = React.ComponentProps<typeof Ionicons>['name'];

const TAB_ICONS: Record<string, { active: IoniconName; inactive: IoniconName }> = {
  index:        { active: 'home',                  inactive: 'home-outline' },
  events:       { active: 'calendar',              inactive: 'calendar-outline' },
  attendance:   { active: 'checkmark-done-circle', inactive: 'checkmark-done-circle-outline' },
  certificates: { active: 'ribbon',                inactive: 'ribbon-outline' },
  profile:      { active: 'person-circle',         inactive: 'person-circle-outline' },
};

function Icon({ name, focused, theme }: {
  name: keyof typeof TAB_ICONS; focused: boolean; theme: 'light' | 'dark';
}) {
  const t = themed(theme);
  const glyph = focused ? TAB_ICONS[name].active : TAB_ICONS[name].inactive;
  return (
    <View style={[styles.iconWrap, focused && styles.iconWrapActive]}>
      <Ionicons
        name={glyph}
        size={focused ? 24 : 26}                                      // más grandes (era 20/22)
        color={focused ? '#FFFFFF' : t.textMuted}
      />
    </View>
  );
}

export default function TabsLayout() {
  const participante = useAuth((s) => s.participante);
  const ready = useAuth((s) => s.ready);
  const theme = useTheme();

  if (ready && !participante) return <Redirect href="/(auth)/login" />;

  // Liquid glass: blur fuerte en iOS (chromeMaterial es el más "vidrio" — Control Center).
  // En Android usamos overlay sólido translúcido (Android no blurea de verdad).
  const isDark = theme === 'dark';
  const blurTint =
    Platform.OS === 'ios'
      ? (isDark ? 'systemChromeMaterialDark' : 'systemChromeMaterialLight')
      : 'default';

  // En iOS bajamos overlay para que el blur fuerte se vea mejor.
  // En Android lo subimos para dar cuerpo (no hay blur que lo refuerce).
  const overlay = isDark
    ? Platform.OS === 'ios' ? 'rgba(22,32,84,0.20)' : 'rgba(22,32,84,0.78)'
    : Platform.OS === 'ios' ? 'rgba(255,255,255,0.20)' : 'rgba(255,255,255,0.85)';

  const borderColor = isDark
    ? 'rgba(255,255,255,0.12)'
    : 'rgba(255,255,255,0.85)';

  const insetTop = isDark ? 'rgba(255,255,255,0.10)' : 'rgba(255,255,255,0.95)';
  const insetBottom = isDark ? 'rgba(0,0,0,0.30)' : 'rgba(15,23,42,0.04)';

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarShowLabel: false,
        tabBarStyle: [styles.bar, styles.barShadow],
        tabBarItemStyle: styles.item,
        tabBarBackground: () => (
          <View style={[styles.barBgWrap, { borderColor, backgroundColor: overlay }]}>
            {Platform.OS === 'ios' ? (
              <BlurView
                intensity={100}                                       // máximo — bien liquid
                tint={blurTint as any}
                style={StyleSheet.absoluteFill}
              />
            ) : null}
            {/* Highlight superior 1px */}
            <View style={[styles.insetTop, { backgroundColor: insetTop }]} pointerEvents="none" />
            {/* Sombra inset inferior 1px */}
            <View style={[styles.insetBottom, { backgroundColor: insetBottom }]} pointerEvents="none" />
          </View>
        ),
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
  bar: {
    position: 'absolute',
    left: spacing.xl,                                                  // más margen lateral
    right: spacing.xl,
    bottom: Platform.OS === 'ios' ? spacing.xxl : spacing.base,
    height: 68,                                                        // un poquito más alto para los iconos grandes
    borderRadius: radius.xxl,
    borderTopWidth: 0,
    backgroundColor: 'transparent',
    paddingHorizontal: spacing.xs,                                     // menos padding interno → más espacio para los items
    paddingTop: 6,
    paddingBottom: 4,
    elevation: 0,
  },
  barBgWrap: {
    position: 'absolute',
    top: 0, left: 0, right: 0, bottom: 0,
    borderRadius: radius.xxl,
    borderWidth: 1,
    overflow: 'hidden',
  },
  insetTop:    { position: 'absolute', top: 0, left: 0, right: 0, height: 1 },
  insetBottom: { position: 'absolute', bottom: 0, left: 0, right: 0, height: 1 },
  barShadow: {
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.12,
    shadowRadius: 24,
    elevation: 8,
  },
  item: {
    height: 56,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconWrap: {
    width: 44,                                                         // era 38
    height: 44,                                                        // era 38
    borderRadius: radius.full,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconWrapActive: {
    backgroundColor: colors.brand,
    width: 46,                                                         // era 40
    height: 46,                                                        // era 40
    ...shadows.brand,
  },
});
