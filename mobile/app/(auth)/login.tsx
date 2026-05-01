import { useState } from 'react';
import {
  KeyboardAvoidingView, Platform, Pressable, ScrollView,
  StyleSheet, Text, TextInput, View,
} from 'react-native';
import { Link, router } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';

import { colors, radius, spacing, themed, typography } from '@/theme/tokens';
import { useAuth } from '@/stores/auth';
import { useTheme } from '@/stores/theme';
import {
  BrandLogo, Button, GradientText, ShowcaseCarousel, VBackground,
} from '@/components/ui';

export default function LoginScreen() {
  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const login   = useAuth((s) => s.login);
  const loading = useAuth((s) => s.loading);
  const error   = useAuth((s) => s.error);
  const theme = useTheme();
  const t = themed(theme);

  async function handleSubmit() {
    try { await login(email.trim(), password); } catch {}
  }

  const inputBg = theme === 'dark' ? 'rgba(255,255,255,0.06)' : 'rgba(15,23,42,0.04)';
  const inputBorder = theme === 'dark' ? 'rgba(255,255,255,0.10)' : 'rgba(15,23,42,0.10)';

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: t.bg }]} edges={['top']}>
      <VBackground intensity={theme === 'dark' ? 0.7 : 0.85} />

      {/* Top bar — back + brand */}
      <View style={styles.topBar}>
        <Pressable
          onPress={() => router.canGoBack() ? router.back() : router.replace('/(auth)/landing')}
          style={({ pressed }) => [styles.back, pressed && { opacity: 0.6 }]}
          hitSlop={12}
        >
          <Ionicons name="chevron-back" size={26} color={colors.brand} style={{ marginLeft: -4 }} />
          <Text style={styles.backText}>Atrás</Text>
        </Pressable>
        <BrandLogo size={22} />
      </View>

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}
        style={{ flex: 1 }}
      >
        <ScrollView
          contentContainerStyle={styles.scroll}
          keyboardShouldPersistTaps="handled"
          keyboardDismissMode="on-drag"
          showsVerticalScrollIndicator={false}
        >
          {/* Showcase carousel — mirror del web auth-shell */}
          <ShowcaseCarousel height={260} />

          {/* Hero */}
          <View style={styles.heroBlock}>
            <GradientText style={styles.title}>Bienvenido</GradientText>
            <Text style={[styles.subtitle, { color: t.textMuted }]}>
              Inicia sesión para acceder a tus certificados y eventos.
            </Text>
          </View>

          {error ? (
            <View style={styles.errorBox}>
              <Ionicons name="alert-circle" size={16} color="#FCA5A5" />
              <Text style={styles.errorText}>{error}</Text>
            </View>
          ) : null}

          {/* Form */}
          <View style={styles.field}>
            <Text style={[styles.label, { color: t.textMuted }]}>Correo electrónico</Text>
            <View style={[styles.inputWrap, { backgroundColor: inputBg, borderColor: inputBorder }]}>
              <Ionicons name="mail-outline" size={18} color={t.textMuted} style={styles.inputIcon} />
              <TextInput
                value={email}
                onChangeText={setEmail}
                placeholder="tu@correo.com"
                placeholderTextColor={t.textMuted}
                autoCapitalize="none"
                autoCorrect={false}
                autoComplete="email"
                textContentType="emailAddress"
                keyboardType="email-address"
                returnKeyType="next"
                style={[styles.input, { color: t.text }]}
              />
            </View>
          </View>

          <View style={styles.field}>
            <Text style={[styles.label, { color: t.textMuted }]}>Contraseña</Text>
            <View style={[styles.inputWrap, { backgroundColor: inputBg, borderColor: inputBorder }]}>
              <Ionicons name="lock-closed-outline" size={18} color={t.textMuted} style={styles.inputIcon} />
              <TextInput
                value={password}
                onChangeText={setPassword}
                placeholder="••••••"
                placeholderTextColor={t.textMuted}
                secureTextEntry={!showPassword}
                autoCapitalize="none"
                autoCorrect={false}
                autoComplete="password"
                textContentType="password"
                returnKeyType="done"
                onSubmitEditing={handleSubmit}
                style={[styles.input, { color: t.text }]}
              />
              <Pressable
                onPress={() => setShowPassword((p) => !p)}
                style={styles.eyeBtn}
                hitSlop={10}
              >
                <Ionicons
                  name={showPassword ? 'eye-off-outline' : 'eye-outline'}
                  size={20}
                  color={t.textMuted}
                />
              </Pressable>
            </View>
          </View>

          <Button
            onPress={handleSubmit}
            loading={loading}
            disabled={!email || !password}
            tone="brand"
            variant="filled"
            size="lg"
            fullWidth
            style={{ marginTop: spacing.sm }}
          >
            {loading ? 'Entrando…' : 'Entrar'}
          </Button>

          <View style={styles.bottomRow}>
            <Text style={[styles.bottomMuted, { color: t.textMuted }]}>¿No tienes cuenta? </Text>
            <Link href="/(auth)/register" style={[styles.bottomLink, { color: colors.brand }]}>
              Regístrate
            </Link>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe:   { flex: 1 },
  scroll: {
    paddingHorizontal: spacing.xl,
    paddingTop: spacing.sm,
    paddingBottom: spacing.huge,
    flexGrow: 1,
  },

  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.xl,
    paddingTop: spacing.sm,
    paddingBottom: spacing.sm,
  },
  back: { flexDirection: 'row', alignItems: 'center' },
  backText: { color: colors.brand, fontSize: typography.base, fontWeight: typography.medium },

  heroBlock: { marginBottom: spacing.lg, marginTop: spacing.sm },
  title:    { fontSize: typography.xxl, fontWeight: typography.black, marginBottom: spacing.xs },
  subtitle: { fontSize: typography.sm },

  errorBox: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    backgroundColor: 'rgba(220,38,38,0.18)',
    borderColor: 'rgba(220,38,38,0.5)', borderWidth: 1,
    padding: spacing.md, borderRadius: radius.md, marginBottom: spacing.base,
  },
  errorText: { color: '#FCA5A5', fontSize: typography.sm, fontWeight: typography.medium, flex: 1 },

  field: { marginBottom: spacing.base },
  label: {
    fontSize: typography.xs, fontWeight: typography.bold,
    marginBottom: spacing.xs, textTransform: 'uppercase', letterSpacing: 1,
  },
  inputWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderRadius: radius.md,
    paddingLeft: spacing.md,
  },
  inputIcon: { marginRight: spacing.sm },
  input: {
    flex: 1,
    paddingVertical: spacing.base,
    paddingRight: spacing.base,
    fontSize: typography.base,
  },
  eyeBtn: { padding: spacing.md },

  bottomRow:    { flexDirection: 'row', justifyContent: 'center', marginTop: spacing.xl },
  bottomMuted:  { fontSize: typography.sm },
  bottomLink:   { fontSize: typography.sm, fontWeight: typography.bold },
});
